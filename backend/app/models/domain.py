from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Role(str, Enum):
    admin = "Admin"
    hr = "HR"
    finance = "Finance"
    engineering = "Engineering"
    compliance = "Compliance"
    operations = "Operations"
    guest = "Guest"


class SensitivityLevel(str, Enum):
    public = "public"
    internal = "internal"
    confidential = "confidential"
    restricted = "restricted"


class DataSourceType(str, Enum):
    pdf = "pdf"
    docx = "docx"
    sql = "sql"
    csv = "csv"
    json = "json"
    audit = "audit"
    knowledge_base = "knowledge_base"


class Principal(BaseModel):
    user_id: str
    username: str
    roles: list[Role]
    departments: list[str] = Field(default_factory=list)
    clearance: SensitivityLevel = SensitivityLevel.internal


class DocumentMetadata(BaseModel):
    source: str
    source_type: DataSourceType
    department: str
    confidentiality: SensitivityLevel
    owner: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    rbac_tags: list[str] = Field(default_factory=list)
    access_level: SensitivityLevel = SensitivityLevel.internal
    allowed_roles: list[Role] = Field(default_factory=list)
    sensitivity_level: SensitivityLevel = SensitivityLevel.internal
    lineage_id: str = Field(default_factory=lambda: str(uuid4()))
    page: int | None = None
    table: str | None = None
    row_id: str | None = None


class DocumentChunk(BaseModel):
    chunk_id: str = Field(default_factory=lambda: f"chunk_{uuid4().hex}")
    text: str
    metadata: DocumentMetadata
    embedding: list[float] | None = None
    score: float | None = None


class QueryType(str, Enum):
    factual = "factual"
    analytical = "analytical"
    compliance = "compliance"
    operational = "operational"
    audit = "audit"


class RetrievalStrategy(str, Enum):
    semantic = "semantic"
    keyword = "keyword"
    hybrid = "hybrid"
    sql = "sql"


class QueryRoute(BaseModel):
    query_type: QueryType
    sources: list[DataSourceType]
    strategy: RetrievalStrategy
    needs_sql: bool = False
    needs_summarization: bool = False
    confidence: float = 0.5
    rationale: str = "Rule-based route"


class RetrievalTrace(BaseModel):
    query: str
    route: QueryRoute
    candidate_chunk_ids: list[str] = Field(default_factory=list)
    authorized_chunk_ids: list[str] = Field(default_factory=list)
    denied_chunk_ids: list[str] = Field(default_factory=list)
    filters_applied: list[str] = Field(default_factory=list)
    latency_ms: float = 0


class Citation(BaseModel):
    chunk_id: str
    source: str
    page: int | None = None
    table: str | None = None
    row_id: str | None = None
    score: float | None = None


class RAGAnswer(BaseModel):
    answer: str
    citations: list[Citation]
    confidence: float
    trace: RetrievalTrace
    access_filter_explanation: str

