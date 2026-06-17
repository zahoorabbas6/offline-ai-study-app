"""
PDF and text file reader module.
Handles extraction of text from PDFs and text files.
"""

import os
from typing import Optional, List
from pathlib import Path
from utils import TextCleaner, Logger

try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False


class FileReader:
    """Reads text from various file formats."""

    SUPPORTED_FORMATS = {'.txt', '.pdf', '.md', '.log'}

    @staticmethod
    def read_file(filepath: str) -> Optional[str]:
        """
        Read text from a file (auto-detects format).
        
        Args:
            filepath: Path to the file
            
        Returns:
            Extracted text or None if failed
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            Logger.log_error(f"File not found: {filepath}")
            return None
        
        file_ext = filepath.suffix.lower()
        
        if file_ext == '.pdf':
            return FileReader.read_pdf(filepath)
        elif file_ext in {'.txt', '.md', '.log'}:
            return FileReader.read_text(filepath)
        else:
            Logger.log_warning(f"Unsupported file format: {file_ext}")
            return None

    @staticmethod
    def read_text(filepath: Path) -> Optional[str]:
        """
        Read text from .txt, .md, or .log files.
        
        Args:
            filepath: Path to the text file
            
        Returns:
            File contents
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            Logger.log(f"Successfully read text file: {filepath.name} ({len(text)} chars)")
            return TextCleaner.clean_text(text)
        except Exception as e:
            Logger.log_error(f"Error reading text file: {e}")
            return None

    @staticmethod
    def read_pdf(filepath: Path) -> Optional[str]:
        """
        Extract text from PDF file.
        
        Args:
            filepath: Path to the PDF file
            
        Returns:
            Extracted text
        """
        if not PDF_SUPPORT:
            Logger.log_error("PyPDF2 not installed. Install with: pip install PyPDF2")
            return None
        
        try:
            text = []
            with open(filepath, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                num_pages = len(pdf_reader.pages)
                
                for page_num in range(num_pages):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text)
            
            combined_text = '\n\n'.join(text)
            Logger.log(f"Successfully extracted from PDF: {filepath.name} "
                      f"({len(pdf_reader.pages)} pages, {len(combined_text)} chars)")
            return TextCleaner.clean_text(combined_text)
        
        except Exception as e:
            Logger.log_error(f"Error reading PDF: {e}")
            return None

    @staticmethod
    def read_directory(dirpath: str, file_types: Optional[List[str]] = None) -> dict:
        """
        Read all files from a directory.
        
        Args:
            dirpath: Path to directory
            file_types: List of file extensions to read (e.g., ['.txt', '.pdf'])
            
        Returns:
            Dictionary with filename -> text mapping
        """
        if file_types is None:
            file_types = ['.txt', '.pdf', '.md']
        
        dirpath = Path(dirpath)
        results = {}
        
        for file_path in dirpath.glob('*'):
            if file_path.suffix.lower() in file_types:
                text = FileReader.read_file(str(file_path))
                if text:
                    results[file_path.name] = text
        
        Logger.log(f"Read {len(results)} files from directory: {dirpath}")
        return results


class TextInputHandler:
    """Handles direct text input."""

    @staticmethod
    def validate_input(text: str, min_length: int = 50) -> tuple[bool, str]:
        """
        Validate text input.
        
        Args:
            text: Input text
            min_length: Minimum acceptable length
            
        Returns:
            (is_valid, message)
        """
        if not text or not text.strip():
            return False, "Text cannot be empty"
        
        if len(text) < min_length:
            return False, f"Text too short (minimum {min_length} characters)"
        
        return True, "Valid input"

    @staticmethod
    def process_input(text: str) -> Optional[str]:
        """
        Process and clean raw text input.
        
        Args:
            text: Raw input text
            
        Returns:
            Cleaned text or None if invalid
        """
        is_valid, message = TextInputHandler.validate_input(text)
        
        if not is_valid:
            Logger.log_warning(f"Invalid input: {message}")
            return None
        
        cleaned = TextCleaner.clean_text(text)
        Logger.log(f"Processed text input ({len(cleaned)} chars)")
        return cleaned


# Export commonly used classes
__all__ = [
    'FileReader',
    'TextInputHandler',
]
