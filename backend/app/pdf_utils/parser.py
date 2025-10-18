"""
PDF Parser - Clean extraction logic moved from services
"""

import io
import time
import logging
import pypdf

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_content: bytes) -> tuple[str, dict]:
    """Extract text and metadata from PDF using PyPDF"""
    start_time = time.time()
    logger.info(f"📄 Starting PDF text extraction - Size: {len(pdf_content)} bytes")
    
    try:
        # PDF parsing
        pdf_parse_start = time.time()
        pdf_stream = io.BytesIO(pdf_content)
        reader = pypdf.PdfReader(pdf_stream)
        pdf_parse_time = time.time() - pdf_parse_start
        logger.info(f"📖 PDF parsed in {pdf_parse_time:.2f}s - Pages: {len(reader.pages)}")
        
        # Extract text from all pages
        text_extract_start = time.time()
        text = ""
        for page_num, page in enumerate(reader.pages):
            page_start = time.time()
            page_text = page.extract_text()
            page_time = time.time() - page_start
            
            if page_text.strip():
                text += f"Page {page_num + 1}:\n{page_text}\n\n"
                logger.debug(f"📝 Page {page_num + 1} extracted in {page_time:.2f}s - {len(page_text)} chars")
            else:
                logger.warning(f"⚠️ Page {page_num + 1} has no extractable text")
        
        text_extract_time = time.time() - text_extract_start
        logger.info(f"📝 Text extraction completed in {text_extract_time:.2f}s - {len(text)} chars total")
        
        # Get metadata
        metadata_start = time.time()
        metadata = {
            "num_pages": len(reader.pages),
            "size_kb": round(len(pdf_content) / 1024, 2),
            "has_text": bool(text.strip()),
            "extraction_time": round(text_extract_time, 2),
            "parse_time": round(pdf_parse_time, 2)
        }
        
        # Try to get PDF info
        if reader.metadata:
            pdf_info = reader.metadata
            metadata.update({
                "title": pdf_info.get("/Title", "Unknown"),
                "author": pdf_info.get("/Author", "Unknown"),
                "creator": pdf_info.get("/Creator", "Unknown")
            })
        
        metadata_time = time.time() - metadata_start
        total_time = time.time() - start_time
        
        logger.info(f"📊 Metadata extracted in {metadata_time:.2f}s")
        logger.info(f"✅ PDF processing completed in {total_time:.2f}s total")
        
        return text.strip(), metadata
        
    except Exception as e:
        error_time = time.time() - start_time
        logger.error(f"❌ PDF extraction failed after {error_time:.2f}s: {str(e)}")
        return "", {"error": str(e), "failed_after": round(error_time, 2)}