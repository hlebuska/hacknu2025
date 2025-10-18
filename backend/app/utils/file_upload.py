import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from typing import Optional
import aiofiles

# Configure upload directory
UPLOAD_DIR = Path("uploads/resumes")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

async def save_uploaded_file(file: UploadFile) -> str:
    """
    Save uploaded file and return the file path
    
    Args:
        file: UploadFile object from FastAPI
        
    Returns:
        str: Relative path to saved file
        
    Raises:
        HTTPException: If file validation fails
    """
    # Validate filename exists
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File must have a filename"
        )
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Validate file size
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # Return relative path
    return str(file_path)

async def delete_file(file_path: str) -> bool:
    """
    Delete uploaded file
    
    Args:
        file_path: Path to file to delete
        
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")
        return False

def get_file_url(file_path: Optional[str]) -> Optional[str]:
    """
    Convert file path to accessible URL
    
    Args:
        file_path: Local file path
        
    Returns:
        str: URL to access the file
    """
    if not file_path:
        return None
    
    # In production, this would be a cloud storage URL
    # For now, return relative path
    return f"/files/{Path(file_path).name}"
