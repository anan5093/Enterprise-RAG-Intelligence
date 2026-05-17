from pydantic import BaseModel, Field

from app.models.domain import DataSourceType, Principal, RAGAnswer, Role, SensitivityLevel


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    principal: Principal


class QueryRequest(BaseModel):
    query: str = Field(min_length=2, max_length=4000)
    stream: bool = False


class QueryResponse(RAGAnswer):
    pass


class IngestRequest(BaseModel):
    path: str
    source_type: DataSourceType
    department: str
    owner: str
    confidentiality: SensitivityLevel = SensitivityLevel.internal
    allowed_roles: list[Role]
    rbac_tags: list[str] = Field(default_factory=list)


class IngestResponse(BaseModel):
    indexed_chunks: int
    source: str
    lineage_ids: list[str]


class HealthResponse(BaseModel):
    status: str
    service: str

