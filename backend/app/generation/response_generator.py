from app.generation.citation_engine import CitationEngine
from app.generation.confidence_estimator import ConfidenceEstimator
from app.generation.hallucination_guard import HallucinationGuard
from app.generation.prompt_builder import PromptBuilder
from app.models.domain import DocumentChunk, Principal, RAGAnswer, RetrievalTrace

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "for",
    "from",
    "in",
    "of",
    "on",
    "show",
    "the",
    "to",
    "were",
    "with",
}


class ResponseGenerator:
    def __init__(
        self,
        prompt_builder: PromptBuilder | None = None,
        citation_engine: CitationEngine | None = None,
        confidence_estimator: ConfidenceEstimator | None = None,
        guard: HallucinationGuard | None = None,
    ) -> None:
        self.prompt_builder = prompt_builder or PromptBuilder()
        self.citation_engine = citation_engine or CitationEngine()
        self.confidence_estimator = confidence_estimator or ConfidenceEstimator()
        self.guard = guard or HallucinationGuard()

    async def generate(self, query: str, chunks: list[DocumentChunk], principal: Principal, trace: RetrievalTrace) -> RAGAnswer:
        if not chunks:
            return RAGAnswer(
                answer=self.guard.insufficient_message,
                citations=[],
                confidence=0.0,
                trace=trace,
                access_filter_explanation=self._filter_explanation(trace),
            )
        evidence_chunks = self._select_evidence_chunks(query, chunks)
        confidence = self.confidence_estimator.estimate(evidence_chunks, trace, query=query)
        if not evidence_chunks:
            return RAGAnswer(
                answer=self.guard.insufficient_message,
                citations=[],
                confidence=0.0,
                trace=trace,
                access_filter_explanation=self._filter_explanation(trace),
            )
        if self.guard.should_refuse(evidence_chunks, confidence):
            return RAGAnswer(
                answer=self.guard.insufficient_message,
                citations=[],
                confidence=confidence,
                trace=trace,
                access_filter_explanation=self._filter_explanation(trace),
            )
        answer = self._synthesize_answer(query, evidence_chunks)
        return RAGAnswer(
            answer=self.guard.sanitize(answer),
            citations=self.citation_engine.build(evidence_chunks),
            confidence=confidence,
            trace=trace,
            access_filter_explanation=self._filter_explanation(trace),
        )

    def _select_evidence_chunks(self, query: str, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        query_terms = self._query_terms(query)
        wants_alerts = {"alert", "alerts", "security"}.intersection(query_terms)
        wants_incidents = "incident" in query_terms or "incidents" in query_terms

        scored: list[tuple[float, DocumentChunk]] = []
        for rank, chunk in enumerate(chunks):
            fields = self._parse_fields(chunk.text)
            searchable = f"{chunk.metadata.source} {chunk.text}".lower()
            overlap = sum(1 for term in query_terms if term in searchable)
            score = float(overlap) + max(0.0, chunk.score or 0.0)

            if wants_alerts and ("alert_id" in fields or "alert" in chunk.metadata.source.lower()):
                score += 3.0
            if wants_incidents and ("incident_id" in fields or "incident" in chunk.metadata.source.lower()):
                score += 2.0
            if "critical" in query_terms and fields.get("severity", "").lower() == "critical":
                score += 2.0
            if self._is_policy_or_access_metadata(chunk) and not {"policy", "policies", "access", "rbac"}.intersection(query_terms):
                score -= 6.0
            if "payroll" in chunk.metadata.source.lower() and not {"payroll", "salary", "bonus"}.intersection(query_terms):
                score -= 5.0
            if "employee_roles" in chunk.metadata.source.lower() and "role" not in query_terms:
                score -= 3.0

            if score > 0:
                scored.append((score - rank * 0.01, chunk))

        selected = [chunk for _, chunk in sorted(scored, key=lambda item: item[0], reverse=True)[:5]]
        return self._rank_evidence_chunks(query, selected or chunks[:1])

    def _synthesize_answer(self, query: str, chunks: list[DocumentChunk]) -> str:
        rows = [self._parse_fields(chunk.text) for chunk in chunks]
        query_terms = self._query_terms(query)

        alert_summaries = []
        incident_summaries = []
        policy_summaries = []
        general_summaries = []

        for chunk, fields in zip(chunks, rows):
            if "alert_id" in fields:
                alert_summaries.append(self._format_alert(fields))
            elif "incident_id" in fields:
                incident_summaries.append(self._format_incident(fields))
            elif chunk.metadata.source.endswith((".md", ".txt")):
                policy_summary = self._summarize_policy_text(chunk.text)
                if policy_summary:
                    policy_summaries.append(policy_summary)
            elif fields:
                formatted_fields = self._format_fields(fields)
                if formatted_fields:
                    general_summaries.append(formatted_fields)
                else:
                    general_summaries.extend(self._sentences_matching_query(chunk.text, query_terms, limit=1))
            else:
                general_summaries.extend(self._sentences_matching_query(chunk.text, query_terms, limit=1))

        parts: list[str] = []
        if alert_summaries:
            parts.append("Security alerts found: " + " ".join(alert_summaries))
        if incident_summaries:
            parts.append("Related operational incidents: " + " ".join(incident_summaries))
        if policy_summaries:
            parts.append("Relevant policy context: " + " ".join(policy_summaries))
        if not parts and general_summaries:
            parts.append("Relevant authorized findings: " + " ".join(general_summaries[:3]))

        return " ".join(parts).strip() or self.guard.insufficient_message

    def _rank_evidence_chunks(self, query: str, chunks: list[DocumentChunk]) -> list[DocumentChunk]:
        query_terms = self._query_terms(query)

        def rank_key(item: tuple[int, DocumentChunk]) -> tuple[int, int, float, int]:
            original_rank, chunk = item
            fields = self._parse_fields(chunk.text)
            category = self._evidence_category(chunk, fields)
            importance = self._importance_score(fields)
            direct_relevance = self._direct_relevance(query_terms, chunk)
            trust = self._source_trust(chunk)
            semantic = max(0.0, chunk.score or 0.0)
            return (
                category,
                -importance,
                -(direct_relevance * 2.0 + semantic + trust),
                original_rank,
            )

        return [chunk for _, chunk in sorted(enumerate(chunks), key=rank_key)]

    def _query_terms(self, query: str) -> set[str]:
        return {term.strip(".,:;!?()[]{}").lower() for term in query.split() if term.lower() not in STOPWORDS and len(term) > 2}

    def _parse_fields(self, text: str) -> dict[str, str]:
        fields: dict[str, str] = {}
        for line in text.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            normalized_key = key.strip().lower()
            if normalized_key:
                fields[normalized_key] = value.strip()
        return fields

    def _format_alert(self, fields: dict[str, str]) -> str:
        alert_id = fields.get("alert_id", "An alert")
        severity = fields.get("severity")
        system = fields.get("system")
        description = fields.get("description")
        status = fields.get("status")
        details = [alert_id]
        if severity:
            details.append(f"was marked {severity.lower()}")
        if system:
            details.append(f"on {system}")
        if description:
            details.append(f"for {description[0].lower() + description[1:] if description else description}")
        if status:
            details.append(f"with status {status}")
        return self._sentence_from_fragments(details)

    def _format_incident(self, fields: dict[str, str]) -> str:
        incident_id = fields.get("incident_id", "An incident")
        severity = fields.get("severity")
        system = fields.get("system")
        status = fields.get("status")
        details = [incident_id]
        if severity:
            details.append(f"was marked {severity.lower()}")
        if system:
            details.append(f"for {system}")
        if status:
            details.append(f"with status {status}")
        return self._sentence_from_fragments(details)

    def _format_fields(self, fields: dict[str, str]) -> str:
        allowed_keys = ["severity", "system", "description", "status", "event_type", "risk", "finding"]
        fragments = [f"{key.replace('_', ' ')}: {fields[key]}" for key in allowed_keys if key in fields]
        return self._sentence_from_fragments(fragments)

    def _summarize_policy_text(self, text: str) -> str:
        lowered = text.lower()
        requirements = []
        if "security approval" in lowered:
            requirements.append("security approval")
        if "compliance review" in lowered:
            requirements.append("compliance review")
        if "ci/cd validation" in lowered or "cicd validation" in lowered:
            requirements.append("CI/CD validation")

        ack_minutes = self._extract_acknowledgement_minutes(text)
        clauses = []
        if requirements:
            clauses.append(f"production deployments require {self._join_human(requirements)}")
        if ack_minutes:
            clauses.append(f"critical incidents must be acknowledged within {ack_minutes} minutes")

        if clauses:
            return "Operational policy states that " + "; ".join(clauses) + "."

        sentences = self._sentences_matching_query(text, {"policy", "incident", "security", "compliance"}, limit=1)
        return sentences[0] if sentences else ""

    def _extract_acknowledgement_minutes(self, text: str) -> str:
        tokens = text.replace(".", " ").split()
        for index, token in enumerate(tokens):
            if token.isdigit() and any("minute" in nearby.lower() for nearby in tokens[index : index + 3]):
                return token
        return ""

    def _join_human(self, values: list[str]) -> str:
        if len(values) <= 1:
            return "".join(values)
        return ", ".join(values[:-1]) + f", and {values[-1]}"

    def _sentence_from_fragments(self, fragments: list[str]) -> str:
        sentence = " ".join(fragment for fragment in fragments if fragment).strip()
        if not sentence:
            return ""
        return sentence if sentence.endswith(".") else f"{sentence}."

    def _sentences_matching_query(self, text: str, query_terms: set[str], limit: int) -> list[str]:
        normalized = text.replace("#", " ")
        candidates = [part.strip(" -\n\t") for part in normalized.replace("\n", ". ").split(".") if part.strip(" -\n\t")]
        matched = [sentence for sentence in candidates if any(term in sentence.lower() for term in query_terms)]
        return [self._sentence_from_fragments([sentence]) for sentence in matched[:limit]]

    def _is_policy_or_access_metadata(self, chunk: DocumentChunk) -> bool:
        source = chunk.metadata.source.lower()
        text = chunk.text.lower()
        return "access_policies" in source or "allowed_roles" in text or "sensitivity:" in text

    def _evidence_category(self, chunk: DocumentChunk, fields: dict[str, str]) -> int:
        source = chunk.metadata.source.lower()
        if "alert_id" in fields or "alert" in source:
            return 0
        if "incident_id" in fields or "incident" in source:
            return 1
        if source.endswith((".md", ".txt")) or "policy" in source:
            return 2
        return 3

    def _importance_score(self, fields: dict[str, str]) -> int:
        severity = fields.get("severity", "").lower()
        if severity == "critical":
            return 3
        if severity == "high":
            return 2
        if severity == "medium":
            return 1
        return 0

    def _direct_relevance(self, query_terms: set[str], chunk: DocumentChunk) -> float:
        if not query_terms:
            return 0.0
        searchable = f"{chunk.metadata.source} {chunk.text}".lower()
        return sum(1 for term in query_terms if term in searchable) / len(query_terms)

    def _source_trust(self, chunk: DocumentChunk) -> float:
        source = chunk.metadata.source.lower()
        if "security_alert" in source:
            return 0.35
        if "incident" in source:
            return 0.28
        if source.endswith((".md", ".txt")):
            return 0.18
        if source.endswith((".csv", ".json")):
            return 0.12
        return 0.05

    def _filter_explanation(self, trace: RetrievalTrace) -> str:
        denied = len(trace.denied_chunk_ids)
        allowed = len(trace.authorized_chunk_ids)
        return f"Applied source routing and RBAC filters before generation. Authorized chunks: {allowed}; denied chunks excluded: {denied}."
