"""
Request processing service for PDF analysis endpoints
Handles the complete workflow from file validation to response generation
"""

import time
import logging
from fastapi import HTTPException
from app.backend_models.response import PDFAnalysisResponse
from app.services_pdf.pdf_parser import PDFParserService
from app.services_pdf.pdf_analyzer import PDFAnalyzerService

logger = logging.getLogger(__name__)


class PDFRequestService:
    """Service for handling complete PDF analysis requests"""
    
    def __init__(self):
        self.pdf_parser = PDFParserService()
        self.pdf_analyzer = PDFAnalyzerService()
    
    async def process_analyze_request(self, file, include_raw_text: bool = False) -> PDFAnalysisResponse:
        """Process PDF analysis request with AI"""
        request_start = time.time()
        logger.info(f"🚀 Starting analyze-pdf request - File: {file.filename}")
        
        try:
            # Validate and read file
            pdf_content = await self._validate_and_read_file(file)
            
            # Extract text and metadata using PDF parser service
            extracted_text, metadata = self.pdf_parser.extract_text_from_pdf(pdf_content)
            
            if not extracted_text:
                logger.warning("⚠️ No text extracted from PDF")
                return PDFAnalysisResponse(
                    success=False,
                    error="No text could be extracted from the PDF. The file might be image-based or corrupted.",
                    metadata=metadata
                )
            
            # Analyze with OpenAI using PDF analyzer service
            analysis = await self.pdf_analyzer.analyze_with_openai(extracted_text)
            
            total_time = time.time() - request_start
            logger.info(f"🏁 analyze-pdf request completed in {total_time:.2f}s total")
            
            return PDFAnalysisResponse(
                success=True,
                extracted_text=extracted_text if include_raw_text else None,
                analysis=analysis,
                metadata={**metadata, "total_request_time": round(total_time, 2)}
            )
            
        except HTTPException:
            error_time = time.time() - request_start
            logger.error(f"❌ HTTPException in analyze-pdf after {error_time:.2f}s")
            raise
        except Exception as e:
            error_time = time.time() - request_start
            logger.error(f"❌ analyze-pdf failed after {error_time:.2f}s: {str(e)}")
            return PDFAnalysisResponse(
                success=False,
                error=f"Analysis failed: {str(e)}"
            )
    
    async def process_parse_request(self, file, include_raw_text: bool = True) -> PDFAnalysisResponse:
        """Process PDF parsing request without AI"""
        request_start = time.time()
        logger.info(f"📄 Starting parse-pdf request - File: {file.filename}")
        
        try:
            # Validate and read file
            pdf_content = await self._validate_and_read_file(file)
            
            # Extract text and metadata using PDF parser service
            extracted_text, metadata = self.pdf_parser.extract_text_from_pdf(pdf_content)
            
            total_time = time.time() - request_start
            logger.info(f"🏁 parse-pdf request completed in {total_time:.2f}s total")
            
            if not extracted_text:
                logger.warning("⚠️ No text extracted from PDF")
                return PDFAnalysisResponse(
                    success=False,
                    error="No text could be extracted from the PDF. The file might be image-based or corrupted.",
                    metadata={**metadata, "total_request_time": round(total_time, 2)}
                )
            
            # Return extracted text without AI analysis
            return PDFAnalysisResponse(
                success=True,
                extracted_text=extracted_text if include_raw_text else None,
                analysis="Text extraction completed successfully using PyPDF. No AI analysis performed.",
                metadata={**metadata, "total_request_time": round(total_time, 2)}
            )
            
        except HTTPException:
            error_time = time.time() - request_start
            logger.error(f"❌ HTTPException in parse-pdf after {error_time:.2f}s")
            raise
        except Exception as e:
            error_time = time.time() - request_start
            logger.error(f"❌ parse-pdf failed after {error_time:.2f}s: {str(e)}")
            return PDFAnalysisResponse(
                success=False,
                error=f"Text extraction failed: {str(e)}"
            )
    
    async def _validate_and_read_file(self, file):
        """Validate file type and read content"""
        # Validate file type
        validation_start = time.time()
        if not file.filename.lower().endswith('.pdf'):
            logger.error(f"❌ Invalid file type: {file.filename}")
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        validation_time = time.time() - validation_start
        logger.info(f"✅ File validation completed in {validation_time:.2f}s")
        
        # Read and process PDF
        read_start = time.time()
        pdf_content = await file.read()
        read_time = time.time() - read_start
        logger.info(f"📖 File read completed in {read_time:.2f}s - Size: {len(pdf_content)} bytes")
        
        if not pdf_content:
            logger.error("❌ Empty PDF file")
            raise HTTPException(status_code=400, detail="Empty PDF file")
        
        return pdf_content