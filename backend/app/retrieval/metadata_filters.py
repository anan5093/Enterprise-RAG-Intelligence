from app.models.domain import DataSourceType, DocumentChunk, Principal
from app.security.rbac import RBACFilter


class MetadataFilterBuilder:
    def source_filter(self, sources: list[DataSourceType]) -> str:
        return "source_type in (" + ", ".join(source.value for source in sources) + ")"


class SecureMetadataFilter:
    def __init__(self, rbac_filter: RBACFilter | None = None) -> None:
        self.rbac_filter = rbac_filter or RBACFilter()

    def apply(self, principal: Principal, chunks: list[DocumentChunk]) -> tuple[list[DocumentChunk], list[DocumentChunk], list[str]]:
        return self.rbac_filter.filter_chunks(principal, chunks)

