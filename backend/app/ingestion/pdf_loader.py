import logging
from pathlib import Path

from app.ingestion.chunking import Chunker
from app.models.domain import DocumentChunk, DocumentMetadata

logger = logging.getLogger(__name__)


class PDFLoader:
    def __init__(self, chunker: Chunker | None = None) -> None:
        self.chunker = chunker or Chunker()

    async def load(self, path: str, metadata: DocumentMetadata) -> list[DocumentChunk]:
        file_path = Path(path)
        text_by_page: list[tuple[int, str]] = []
        try:
            import fitz  # PyMuPDF

            with fitz.open(file_path) as pdf:
                for page_index, page in enumerate(pdf, start=1):
                    page_text = page.get_text("text")
                    if not page_text.strip():
                        page_text = await self._ocr_fitz_page(page)
                    if page_text.strip():
                        text_by_page.append((page_index, page_text))
        except Exception as exc:  # pragma: no cover - optional dependency fallback
            logger.warning("pymupdf_failed path=%s error=%s", path, exc)
            try:
                import pdfplumber

                with pdfplumber.open(file_path) as pdf:
                    for page_index, page in enumerate(pdf.pages, start=1):
                        text_by_page.append((page_index, page.extract_text() or ""))
            except Exception as pdf_exc:
                logger.error("pdf_parse_failed path=%s error=%s", path, pdf_exc)

        chunks: list[DocumentChunk] = []
        for page, text in text_by_page:
            chunks.extend(self.chunker.chunk_text(text, metadata.model_copy(update={"page": page})))
        return chunks

    async def _ocr_page(self, image) -> str:
        try:
            import pytesseract

            return pytesseract.image_to_string(image)
        except Exception as exc:  # pragma: no cover - optional system dependency
            logger.warning("ocr_failed error=%s", exc)
            return ""

    async def _ocr_fitz_page(self, page) -> str:
        try:
            from PIL import Image

            pixmap = page.get_pixmap(dpi=220)
            image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
            return await self._ocr_page(image)
        except Exception as exc:  # pragma: no cover - optional system dependency
            logger.warning("fitz_ocr_render_failed error=%s", exc)
            return ""
