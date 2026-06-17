"""
GUI Module for Offline AI Study Engine.
Provides a clean Tkinter interface for all features.
"""

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from pathlib import Path
from typing import Optional, Callable
from utils import Logger, DataManager
from pdf_reader import FileReader, TextInputHandler
from nlp_engine import NLPEngine
from flashcards import FlashcardGenerator, FlashcardDeck
from exam_predictor import ExamPredictor
from quiz_generator import QuizGenerator, QuizDifficulty, WeaknessAnalyzer


class StudyAppGUI:
    """Main GUI for the Study Engine."""

    def __init__(self, root: tk.Tk):
        """
        Initialize GUI.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Offline AI Study Engine")
        self.root.geometry("900x700")

        # Initialize components
        self.data_manager = DataManager()
        self.nlp_engine = NLPEngine()
        self.flashcard_generator = None
        self.exam_predictor = None
        self.current_text = ""
        self.current_deck = None

        # Setup theme
        self.root.configure(bg="#f0f0f0")
        self.setup_styles()

        # Create UI
        self.create_menu()
        self.create_main_ui()

    def setup_styles(self):
        """Setup ttk styles."""
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", font=("Arial", 10))
        style.configure("TLabel", font=("Arial", 10), background="#f0f0f0")
        style.configure("Title.TLabel", font=("Arial", 14, "bold"), background="#f0f0f0")

    def create_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open PDF", command=self.load_pdf)
        file_menu.add_command(label="Open Text File", command=self.load_text_file)
        file_menu.add_command(label="Enter Text", command=self.enter_text_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Generate Flashcards", command=self.generate_flashcards)
        tools_menu.add_command(label="Predict Exam Questions", command=self.predict_exam_questions)
        tools_menu.add_command(label="Create Quiz", command=self.create_quiz)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_main_ui(self):
        """Create main UI layout."""
        # Title
        title_label = ttk.Label(
            self.root,
            text="Offline AI Study Engine",
            style="Title.TLabel",
        )
        title_label.pack(pady=10)

        # Main content frame
        content_frame = ttk.Frame(self.root)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Input
        left_frame = ttk.LabelFrame(content_frame, text="Study Material", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.text_input = scrolledtext.ScrolledText(left_frame, height=20, width=40)
        self.text_input.pack(fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(left_frame)
        button_frame.pack(fill=tk.X, pady=5)

        ttk.Button(button_frame, text="Load PDF", command=self.load_pdf).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Load Text", command=self.load_text_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear", command=lambda: self.text_input.delete("1.0", tk.END)).pack(
            side=tk.LEFT, padx=2
        )

        # Right panel - Output/Controls
        right_frame = ttk.LabelFrame(content_frame, text="Tools & Options", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        # Output display
        ttk.Label(right_frame, text="Output:").pack()
        self.output_display = scrolledtext.ScrolledText(right_frame, height=15, width=40)
        self.output_display.pack(fill=tk.BOTH, expand=True, pady=5)

        # Control buttons
        button_frame_right = ttk.Frame(right_frame)
        button_frame_right.pack(fill=tk.X, pady=5)

        ttk.Button(
            button_frame_right,
            text="Generate Flashcards",
            command=self.generate_flashcards,
        ).pack(fill=tk.X, pady=2)

        ttk.Button(
            button_frame_right,
            text="Predict Exam Questions",
            command=self.predict_exam_questions,
        ).pack(fill=tk.X, pady=2)

        ttk.Button(
            button_frame_right,
            text="Create Quiz",
            command=self.create_quiz,
        ).pack(fill=tk.X, pady=2)

        ttk.Button(
            button_frame_right,
            text="Text Statistics",
            command=self.show_text_stats,
        ).pack(fill=tk.X, pady=2)

        ttk.Button(
            button_frame_right,
            text="Export Flashcards",
            command=self.export_flashcards,
        ).pack(fill=tk.X, pady=2)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def load_pdf(self):
        """Load PDF file."""
        filepath = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if filepath:
            text = FileReader.read_file(filepath)
            if text:
                self.text_input.delete("1.0", tk.END)
                self.text_input.insert("1.0", text)
                self.current_text = text
                self.status_var.set(f"Loaded: {Path(filepath).name}")
            else:
                messagebox.showerror("Error", "Failed to read PDF")

    def load_text_file(self):
        """Load text file."""
        filepath = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("Markdown files", "*.md"), ("All files", "*.*")]
        )
        if filepath:
            text = FileReader.read_file(filepath)
            if text:
                self.text_input.delete("1.0", tk.END)
                self.text_input.insert("1.0", text)
                self.current_text = text
                self.status_var.set(f"Loaded: {Path(filepath).name}")

    def enter_text_dialog(self):
        """Show dialog to enter text directly."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Enter Study Material")
        dialog.geometry("600x400")

        label = ttk.Label(dialog, text="Paste or type your study material:")
        label.pack(padx=10, pady=5)

        text_widget = scrolledtext.ScrolledText(dialog, height=20, width=70)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        def save_text():
            text = text_widget.get("1.0", tk.END)
            is_valid, message = TextInputHandler.validate_input(text)
            if is_valid:
                self.text_input.delete("1.0", tk.END)
                self.text_input.insert("1.0", text)
                self.current_text = TextInputHandler.process_input(text)
                self.status_var.set("Text entered successfully")
                dialog.destroy()
            else:
                messagebox.showwarning("Invalid Input", message)

        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(button_frame, text="Save", command=save_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def generate_flashcards(self):
        """Generate flashcards from current text."""
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("No Input", "Please enter or load study material first")
            return

        if not self.nlp_engine.is_ready():
            messagebox.showerror("NLP Error", "NLP engine not initialized. Check logs.")
            return

        self.status_var.set("Generating flashcards...")
        self.root.update()

        try:
            self.flashcard_generator = FlashcardGenerator(self.nlp_engine)
            cards = self.flashcard_generator.generate_all(text, num_cards=50)

            self.current_deck = FlashcardDeck("Generated Deck")
            self.current_deck.add_cards(cards)

            # Display results
            self.output_display.delete("1.0", tk.END)
            output = f"Generated {len(cards)} Flashcards\n\n"

            for i, card in enumerate(cards[:10], 1):
                output += f"{i}. Q: {card.question}\n"
                output += f"   A: {card.answer[:60]}...\n"
                output += f"   Tags: {', '.join(card.tags)}\n"
                output += f"   Difficulty: {card.difficulty.name}\n\n"

            output += f"\n... and {len(cards) - 10} more cards"
            self.output_display.insert("1.0", output)

            self.status_var.set(f"Successfully generated {len(cards)} flashcards")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate flashcards: {str(e)}")
            self.status_var.set("Error generating flashcards")

    def predict_exam_questions(self):
        """Predict likely exam questions."""
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("No Input", "Please enter or load study material first")
            return

        if not self.nlp_engine.is_ready():
            messagebox.showerror("NLP Error", "NLP engine not initialized")
            return

        self.status_var.set("Predicting exam questions...")
        self.root.update()

        try:
            self.exam_predictor = ExamPredictor(self.nlp_engine)
            questions = self.exam_predictor.predict_questions(text, num_questions=20)

            # Display results
            self.output_display.delete("1.0", tk.END)
            output = f"Predicted {len(questions)} Exam Questions\n\n"

            by_probability = self.exam_predictor.rank_by_probability()
            for i, q in enumerate(by_probability[:10], 1):
                output += f"{i}. [{q.probability.name}] {q.question_type.value}\n"
                output += f"   Q: {q.question}\n"
                output += f"   Topic: {q.topic}\n\n"

            output += f"\n... and {len(questions) - 10} more questions"
            self.output_display.insert("1.0", output)

            self.status_var.set(f"Successfully predicted {len(questions)} exam questions")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to predict questions: {str(e)}")

    def create_quiz(self):
        """Create and run a quiz."""
        if not self.current_deck or len(self.current_deck) == 0:
            messagebox.showwarning("No Flashcards", "Please generate flashcards first")
            return

        # Create quiz window
        quiz_window = tk.Toplevel(self.root)
        quiz_window.title("Quiz")
        quiz_window.geometry("700x500")

        # Create quiz session
        quiz_session = QuizGenerator.create_from_flashcards(
            self.current_deck.cards,
            quiz_name="Study Quiz",
            num_questions=10,
        )

        QuizUI(quiz_window, quiz_session, self.data_manager)

    def show_text_stats(self):
        """Show statistics about current text."""
        text = self.text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("No Input", "Please enter or load study material first")
            return

        from utils import TextAnalyzer

        stats = TextAnalyzer.get_stats(text)

        output = "TEXT STATISTICS\n\n"
        for key, value in stats.items():
            output += f"{key.replace('_', ' ').title()}: {value}\n"

        if self.nlp_engine.is_ready():
            complexity = self.nlp_engine.analyze_text_complexity(text)
            output += "\nCOMPLEXITY METRICS\n"
            for key, value in complexity.items():
                output += f"{key.replace('_', ' ').title()}: {value:.2f}\n"

        self.output_display.delete("1.0", tk.END)
        self.output_display.insert("1.0", output)

    def export_flashcards(self):
        """Export flashcards to JSON."""
        if not self.current_deck or len(self.current_deck) == 0:
            messagebox.showwarning("No Flashcards", "Please generate flashcards first")
            return

        filename = self.data_manager.save_flashcards(
            self.current_deck.to_dict_list(),
            "exported",
        )
        messagebox.showinfo("Exported", f"Flashcards saved to: {filename}")
        self.status_var.set(f"Exported to {filename}")

    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            "Offline AI Study Engine\n\n"
            "Convert study materials into:\n"
            "• Flashcards\n"
            "• Predicted Exam Questions\n"
            "• Practice Quizzes\n"
            "• Weakness Analysis\n\n"
            "All processing is done offline on your machine.",
        )


class QuizUI:
    """Quiz interface."""

    def __init__(self, window: tk.Toplevel, quiz_session, data_manager):
        """
        Initialize quiz UI.
        
        Args:
            window: Tkinter window
            quiz_session: Quiz session object
            data_manager: Data manager
        """
        self.window = window
        self.quiz_session = quiz_session
        self.data_manager = data_manager

        self.create_ui()

    def create_ui(self):
        """Create quiz UI."""
        # Progress
        progress_frame = ttk.Frame(self.window)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)

        current, total = self.quiz_session.get_progress()
        ttk.Label(progress_frame, text=f"Question {current}/{total}").pack()

        # Question display
        question_frame = ttk.LabelFrame(self.window, text="Question", padding=10)
        question_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        question = self.quiz_session.get_current_question()
        if isinstance(question, object) and hasattr(question, "question"):
            question_text = question.question
        else:
            question_text = "No question"

        question_label = ttk.Label(question_frame, text=question_text, wraplength=600, justify=tk.LEFT)
        question_label.pack(pady=10)

        # Answer input
        answer_frame = ttk.LabelFrame(self.window, text="Your Answer", padding=10)
        answer_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.answer_input = scrolledtext.ScrolledText(answer_frame, height=5, width=60)
        self.answer_input.pack(fill=tk.BOTH, expand=True)

        # Buttons
        button_frame = ttk.Frame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(button_frame, text="Submit Answer", command=self.submit_answer).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Quit Quiz", command=self.window.destroy).pack(side=tk.LEFT, padx=5)

    def submit_answer(self):
        """Submit answer."""
        answer = self.answer_input.get("1.0", tk.END).strip()
        if not answer:
            messagebox.showwarning("No Answer", "Please enter an answer")
            return

        is_correct = self.quiz_session.submit_answer(answer)
        current, total = self.quiz_session.get_progress()

        if current >= total:
            results = self.quiz_session.finish()
            self.show_results(results)
            self.window.destroy()
        else:
            messagebox.showinfo(
                "Answer Submitted",
                f"{'Correct!' if is_correct else 'Incorrect'}",
            )
            self.window.destroy()

    def show_results(self, results):
        """Show quiz results."""
        messagebox.showinfo(
            "Quiz Complete",
            f"Score: {results['score_percentage']:.1f}%\n"
            f"Correct: {results['correct']}/{results['total_questions']}",
        )


def run_gui():
    """Run the GUI application."""
    root = tk.Tk()
    app = StudyAppGUI(root)
    root.mainloop()


# Export commonly used functions
__all__ = [
    'StudyAppGUI',
    'QuizUI',
    'run_gui',
]
