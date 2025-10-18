"""
PDF parsing service for text extraction and metadata
"""

from app.pdf_utils import extract_text_from_pdf


class PDFParserService:
    """Service for PDF text extraction and metadata parsing"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_content: bytes) -> tuple[str, dict]:
        """Extract text and metadata from PDF using PyPDF"""
        return extract_text_from_pdf(pdf_content)