"""
Utility functions for the Offline AI Study Engine.
Includes text cleaning, data persistence, and helper functions.
"""

import json
import re
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import hashlib
from datetime import datetime


class DataManager:
    """Manages data persistence (JSON/pickle storage)."""

    def __init__(self, data_dir: str = "study_data"):
        """
        Initialize DataManager.
        
        Args:
            data_dir: Directory to store data files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def save_json(self, filename: str, data: Any) -> None:
        """Save data as JSON."""
        filepath = self.data_dir / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_json(self, filename: str) -> Any:
        """Load data from JSON."""
        filepath = self.data_dir / filename
        if not filepath.exists():
            return None
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_flashcards(self, flashcards: List[Dict], session_name: str) -> str:
        """
        Save flashcards with timestamp.
        
        Args:
            flashcards: List of flashcard dictionaries
            session_name: Name of the study session
            
        Returns:
            Filename where cards were saved
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"flashcards_{session_name}_{timestamp}.json"
        self.save_json(filename, {"timestamp": timestamp, "type": "flashcards", "cards": flashcards})
        return filename

    def save_exam_predictions(self, questions: List[Dict], session_name: str) -> str:
        """
        Save predicted exam questions with timestamp.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exam_predictions_{session_name}_{timestamp}.json"
        self.save_json(filename, {"timestamp": timestamp, "type": "exam_predictions", "questions": questions})
        return filename

    def save_quiz_results(self, quiz_data: Dict, session_name: str) -> str:
        """
        Save quiz results with timestamp.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quiz_results_{session_name}_{timestamp}.json"
        record = {"timestamp": timestamp, "type": "quiz_results", **quiz_data}
        self.save_json(filename, record)
        return filename

    def save_quiz_structure(self, quiz_data: Dict, session_name: str) -> str:
        """
        Save quiz structure for review and editing.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quiz_structure_{session_name}_{timestamp}.json"
        record = {"timestamp": timestamp, "type": "quiz_structure", **quiz_data}
        self.save_json(filename, record)
        return filename

    def load_flashcards(self, filename: str) -> Optional[List[Dict]]:
        """Load flashcards from file."""
        data = self.load_json(filename)
        return data.get("cards") if data else None

    def load_saved_item(self, filename: str) -> Any:
        """Load any saved JSON item."""
        return self.load_json(filename)

    def list_saved_files(self, pattern: str = "*") -> List[str]:
        """List all saved files matching pattern."""
        return [f.name for f in self.data_dir.glob(pattern)]


class TextCleaner:
    """Handles text cleaning and preprocessing."""

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        # Normalize quotes
        text = text.replace('“', '"').replace('”', '"').replace("‘", "'").replace("’", "'")
        
        return text.strip()

    @staticmethod
    def extract_sentences(text: str) -> List[str]:
        """
        Split text into sentences (basic approach before NLP).
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Split by common sentence endings
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    @staticmethod
    def extract_paragraphs(text: str) -> List[str]:
        """
        Extract paragraphs from text.
        
        Args:
            text: Raw text
            
        Returns:
            List of paragraphs
        """
        # Split by double newlines or multiple spaces
        paragraphs = re.split(r'\n\n+|\r\n\r\n+', text)
        return [p.strip() for p in paragraphs if p.strip()]


class TextAnalyzer:
    """Analyzes text properties."""

    @staticmethod
    def get_stats(text: str) -> Dict[str, int]:
        """
        Get text statistics.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with stats
        """
        words = text.split()
        sentences = TextCleaner.extract_sentences(text)
        
        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(TextCleaner.extract_paragraphs(text)),
            "avg_words_per_sentence": len(words) // max(len(sentences), 1),
            "unique_words": len(set(words)),
        }

    @staticmethod
    def calculate_text_hash(text: str) -> str:
        """
        Calculate hash of text for deduplication.
        
        Args:
            text: Text to hash
            
        Returns:
            MD5 hash of text
        """
        return hashlib.md5(text.encode()).hexdigest()


class ConceptExtractor:
    """Basic concept extraction (before full NLP processing)."""

    COMMON_QUESTION_WORDS = {'what', 'who', 'when', 'where', 'why', 'how', 'which', 'define', 'explain'}

    @staticmethod
    def extract_definitions(text: str) -> List[Tuple[str, str]]:
        """
        Extract simple definitions (term: definition patterns).
        
        Args:
            text: Text to extract from
            
        Returns:
            List of (term, definition) tuples
        """
        definitions = []
        
        # Pattern: "X is/are/means Y"
        pattern = r'([A-Z][^.!?]*?)\s+(?:is|are|means|refers to)\s+([^.!?]+[.!?])'
        matches = re.finditer(pattern, text, re.MULTILINE)
        
        for match in matches:
            term = match.group(1).strip()
            defn = match.group(2).strip()
            
            # Filter out very long definitions
            if len(term) > 5 and len(defn) < 300:
                definitions.append((term, defn))
        
        return definitions

    @staticmethod
    def extract_keywords(text: str, top_n: int = 10) -> List[str]:
        """
        Extract common keywords (simple frequency-based).
        
        Args:
            text: Text to extract from
            top_n: Number of top keywords to return
            
        Returns:
            List of keywords sorted by frequency
        """
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'do', 'does', 'did', 'will', 'would', 'should', 'could',
            'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
        }
        
        words = re.findall(r'\b\w+\b', text.lower())
        word_freq = {}
        
        for word in words:
            if len(word) > 3 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_n]]


class Logger:
    """Simple logging utility."""

    @staticmethod
    def log(message: str, level: str = "INFO") -> None:
        """
        Print timestamped log message.
        
        Args:
            message: Log message
            level: Log level (INFO, WARNING, ERROR)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    @staticmethod
    def log_error(message: str) -> None:
        """Log error message."""
        Logger.log(message, "ERROR")

    @staticmethod
    def log_warning(message: str) -> None:
        """Log warning message."""
        Logger.log(message, "WARNING")


# Export commonly used classes
__all__ = [
    'DataManager',
    'TextCleaner',
    'TextAnalyzer',
    'ConceptExtractor',
    'Logger',
]
