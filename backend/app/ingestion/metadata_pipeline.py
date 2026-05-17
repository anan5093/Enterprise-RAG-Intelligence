from pathlib import Path

from app.models.api import IngestRequest
from app.models.domain import DocumentMetadata


class MetadataPipeline:
    def build(self, request: IngestRequest) -> DocumentMetadata:
        return DocumentMetadata(
            source=Path(request.path).name,
            source_type=request.source_type,
            department=request.department,
            confidentiality=request.confidentiality,
            owner=request.owner,
            rbac_tags=request.rbac_tags,
            access_level=request.confidentiality,
            allowed_roles=request.allowed_roles,
            sensitivity_level=request.confidentiality,
        )

