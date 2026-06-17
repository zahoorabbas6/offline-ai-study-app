"""
Main entry point for Offline AI Study Engine.
Provides both CLI and GUI interfaces.
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, List

from utils import Logger, DataManager, TextCleaner
from pdf_reader import FileReader, TextInputHandler
from nlp_engine import NLPEngine
from flashcards import FlashcardGenerator, FlashcardDeck
from exam_predictor import ExamPredictor
from quiz_generator import QuizGenerator, QuizDifficulty, WeaknessAnalyzer


class StudyEngineCore:
    """Core engine orchestrating all study features."""

    def __init__(self):
        """Initialize the core engine."""
        Logger.log("Initializing Offline AI Study Engine...")
        self.data_manager = DataManager()
        self.nlp_engine = NLPEngine()
        self.current_text = ""
        self.current_deck = None

        if not self.nlp_engine.is_ready():
            Logger.log_warning("NLP Engine not fully initialized. Some features may be limited.")

    def load_text(self, source: str) -> bool:
        """
        Load text from file or direct input.
        
        Args:
            source: File path or direct text
            
        Returns:
            True if successful
        """
        source_path = Path(source)

        if source_path.exists():
            # Treat as file
            text = FileReader.read_file(source)
        else:
            # Treat as direct text
            text = TextInputHandler.process_input(source)

        if text:
            self.current_text = text
            Logger.log(f"Loaded {len(text)} characters of text")
            return True

        Logger.log_error("Failed to load text")
        return False

    def generate_flashcards(self, num_cards: int = 50) -> Optional[FlashcardDeck]:
        """
        Generate flashcards from current text.
        
        Args:
            num_cards: Number of cards to generate
            
        Returns:
            FlashcardDeck or None if failed
        """
        if not self.current_text:
            Logger.log_error("No text loaded")
            return None

        if not self.nlp_engine.is_ready():
            Logger.log_error("NLP Engine not ready")
            return None

        Logger.log(f"Generating {num_cards} flashcards...")

        generator = FlashcardGenerator(self.nlp_engine)
        cards = generator.generate_all(self.current_text, num_cards=num_cards)

        self.current_deck = FlashcardDeck("Study Deck")
        self.current_deck.add_cards(cards)

        Logger.log(f"Successfully generated {len(cards)} flashcards")
        return self.current_deck

    def predict_exam_questions(self, num_questions: int = 20) -> Optional[List]:
        """
        Predict likely exam questions.
        
        Args:
            num_questions: Number of questions to predict
            
        Returns:
            List of exam questions or None
        """
        if not self.current_text:
            Logger.log_error("No text loaded")
            return None

        if not self.nlp_engine.is_ready():
            Logger.log_error("NLP Engine not ready")
            return None

        Logger.log(f"Predicting {num_questions} exam questions...")

        predictor = ExamPredictor(self.nlp_engine)
        questions = predictor.predict_questions(self.current_text, num_questions=num_questions)

        Logger.log(f"Generated {len(questions)} predicted exam questions")
        return questions

    def create_quiz(
        self,
        source: str = "flashcards",
        difficulty: QuizDifficulty = QuizDifficulty.INTERMEDIATE,
        num_questions: int = 10,
    ):
        """
        Create a practice quiz.
        
        Args:
            source: "flashcards" or "exam_questions"
            difficulty: Quiz difficulty
            num_questions: Number of questions
            
        Returns:
            QuizSession or None
        """
        if source == "flashcards":
            if not self.current_deck or len(self.current_deck) == 0:
                Logger.log_error("No flashcard deck available")
                return None

            quiz = QuizGenerator.create_difficulty_based(
                self.current_deck.cards,
                difficulty=difficulty,
                num_questions=num_questions,
            )
        elif source == "exam_questions":
            questions = self.predict_exam_questions(num_questions)
            if not questions:
                return None

            quiz = QuizGenerator.create_from_exam_questions(
                questions,
                num_questions=num_questions,
            )
        else:
            Logger.log_error(f"Unknown quiz source: {source}")
            return None

        return quiz

    def export_flashcards(self, filename: Optional[str] = None) -> Optional[str]:
        """
        Export flashcards to JSON.
        
        Args:
            filename: Custom filename (optional)
            
        Returns:
            Saved filename or None
        """
        if not self.current_deck or len(self.current_deck) == 0:
            Logger.log_error("No flashcard deck to export")
            return None

        if not filename:
            filename = self.data_manager.save_flashcards(self.current_deck.to_dict_list(), "export")
        else:
            self.data_manager.save_json(filename, {"cards": self.current_deck.to_dict_list()})

        Logger.log(f"Exported flashcards to {filename}")
        return filename

    def show_statistics(self):
        """Display statistics about current session."""
        if not self.current_text:
            Logger.log("No text loaded")
            return

        from utils import TextAnalyzer

        print("\n" + "=" * 50)
        print("TEXT STATISTICS")
        print("=" * 50)

        stats = TextAnalyzer.get_stats(self.current_text)
        for key, value in stats.items():
            print(f"{key.replace('_', ' ').title()}: {value}")

        if self.nlp_engine.is_ready():
            print("\nCOMPLEXITY METRICS")
            print("-" * 50)
            complexity = self.nlp_engine.analyze_text_complexity(self.current_text)
            for key, value in complexity.items():
                print(f"{key.replace('_', ' ').title()}: {value:.3f}")

        if self.current_deck:
            print("\nFLASHCARD DECK STATISTICS")
            print("-" * 50)
            deck_stats = self.current_deck.get_stats()
            for key, value in deck_stats.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        print(f"{sub_key}: {sub_value}")
                else:
                    print(f"{key}: {value}")

        print("=" * 50 + "\n")


class CLIInterface:
    """Command-line interface for the Study Engine."""

    def __init__(self):
        """Initialize CLI."""
        self.engine = StudyEngineCore()

    def run_interactive(self):
        """Run interactive CLI mode."""
        print("\n" + "=" * 60)
        print("OFFLINE AI STUDY ENGINE - Interactive Mode")
        print("=" * 60 + "\n")

        while True:
            print("Options:")
            print("1. Load PDF/Text file")
            print("2. Enter text directly")
            print("3. Generate flashcards")
            print("4. Predict exam questions")
            print("5. Create quiz")
            print("6. Show statistics")
            print("7. Export flashcards")
            print("8. Exit")
            print()

            choice = input("Select option (1-8): ").strip()

            if choice == "1":
                filepath = input("Enter file path: ").strip()
                if self.engine.load_text(filepath):
                    print("[OK] File loaded successfully")
                else:
                    print("[ERROR] Failed to load file")

            elif choice == "2":
                print("Enter or paste your text (press Ctrl+D or Ctrl+Z on Windows to finish):")
                try:
                    lines = []
                    while True:
                        line = input()
                        lines.append(line)
                except EOFError:
                    pass

                text = "\n".join(lines)
                if self.engine.load_text(text):
                    print("[OK] Text loaded successfully")
                else:
                    print("[ERROR] Invalid text input")

            elif choice == "3":
                num = input("Number of flashcards to generate (default 50): ").strip()
                num = int(num) if num.isdigit() else 50
                deck = self.engine.generate_flashcards(num)
                if deck:
                    self.show_flashcards(deck)

            elif choice == "4":
                num = input("Number of exam questions to predict (default 20): ").strip()
                num = int(num) if num.isdigit() else 20
                questions = self.engine.predict_exam_questions(num)
                if questions:
                    self.show_exam_questions(questions)

            elif choice == "5":
                print("Quiz feature available in GUI mode")

            elif choice == "6":
                self.engine.show_statistics()

            elif choice == "7":
                filename = self.engine.export_flashcards()
                if filename:
                    print(f"[OK] Flashcards exported to {filename}")

            elif choice == "8":
                print("Exiting...")
                break

            else:
                print("Invalid option")

            print()

    @staticmethod
    def show_flashcards(deck: FlashcardDeck):
        """Display flashcards."""
        print("\n" + "=" * 60)
        print(f"Generated {len(deck)} Flashcards")
        print("=" * 60 + "\n")

        for i, card in enumerate(deck.cards[:10], 1):
            print(f"{i}. Q: {card.question}")
            print(f"   A: {card.answer}")
            print(f"   Tags: {', '.join(card.tags)}")
            print(f"   Difficulty: {card.difficulty.name}\n")

        if len(deck) > 10:
            print(f"... and {len(deck) - 10} more flashcards\n")

    @staticmethod
    def show_exam_questions(questions: List):
        """Display exam questions."""
        print("\n" + "=" * 60)
        print(f"Predicted {len(questions)} Exam Questions")
        print("=" * 60 + "\n")

        # Sort by probability
        questions.sort(key=lambda q: q.probability.value, reverse=True)

        for i, q in enumerate(questions[:10], 1):
            print(f"{i}. [{q.probability.name}] {q.question_type.value}")
            print(f"   Q: {q.question}")
            print(f"   Topic: {q.topic}\n")

        if len(questions) > 10:
            print(f"... and {len(questions) - 10} more questions\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Offline AI Study Engine")
    parser.add_argument("--gui", action="store_true", help="Run GUI mode")
    parser.add_argument("--cli", action="store_true", help="Run CLI interactive mode")
    parser.add_argument("--file", type=str, help="Load file at startup")
    parser.add_argument(
        "--flashcards",
        type=int,
        default=50,
        help="Number of flashcards to generate",
    )
    parser.add_argument(
        "--exam",
        type=int,
        default=20,
        help="Number of exam questions to predict",
    )

    args = parser.parse_args()

    # Default to GUI if available, otherwise CLI
    use_gui = args.gui or (not args.cli)

    if use_gui:
        try:
            from gui_pyside import run_gui

            Logger.log("Starting PySide6 GUI mode...")
            run_gui()
        except ImportError:
            Logger.log_warning("PySide6 GUI not available, falling back to customtkinter GUI.")
            try:
                from gui_custom import run_gui

                Logger.log("Starting CustomTkinter GUI mode...")
                run_gui()
            except ImportError:
                Logger.log_error("No GUI available. Falling back to CLI.")
                cli = CLIInterface()
                cli.run_interactive()
    else:
        cli = CLIInterface()
        cli.run_interactive()


if __name__ == "__main__":
    main()
