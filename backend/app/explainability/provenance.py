from app.models.domain import Citation


class ProvenanceRenderer:
    def render(self, citations: list[Citation]) -> list[str]:
        rendered: list[str] = []
        for citation in citations:
            location = citation.source
            if citation.page:
                location += f" page {citation.page}"
            if citation.table:
                location += f" table {citation.table}"
            if citation.row_id:
                location += f" row {citation.row_id}"
            rendered.append(f"{citation.chunk_id}: {location}")
        return rendered

