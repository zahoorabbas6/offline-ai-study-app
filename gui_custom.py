"""
CustomTkinter GUI Module for Offline AI Study Engine.
Provides a modern offline interface with saved-data browsing and editing.
"""

import json
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from typing import Optional, Callable

import customtkinter as ctk
from utils import DataManager
from pdf_reader import FileReader, TextInputHandler
from nlp_engine import NLPEngine
from flashcards import FlashcardGenerator, FlashcardDeck
from exam_predictor import ExamPredictor
from quiz_generator import QuizGenerator


ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class StudyAppGUI:
    """Main GUI for the Study Engine."""

    def __init__(self, root: ctk.CTk):
        self.root = root
        self.root.title("Offline AI Study Engine")
        self.root.geometry("1000x760")

        self.data_manager = DataManager()
        self.nlp_engine = NLPEngine()
        self.flashcard_generator = None
        self.exam_predictor = None
        self.current_text = ""
        self.current_deck = None
        self.current_flashcards = []
        self.current_exam_predictions = []
        self.current_quiz_data = None
        self.current_quiz_results = None

        self.create_menu()
        self.create_main_ui()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open PDF", command=self.load_pdf)
        file_menu.add_command(label="Open Text File", command=self.load_text_file)
        file_menu.add_command(label="Enter Text", command=self.enter_text_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="View Saved Data", command=self.view_saved_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Generate Flashcards", command=self.generate_flashcards)
        tools_menu.add_command(label="Predict Exam Questions", command=self.predict_exam_questions)
        tools_menu.add_command(label="Create Quiz", command=self.create_quiz)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_main_ui(self):
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        header = ctk.CTkLabel(main_frame, text="Offline AI Study Engine", font=ctk.CTkFont(size=24, weight="bold"))
        header.pack(pady=(0, 12))

        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure((0, 1), weight=1)

        left_frame = ctk.CTkFrame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        right_frame = ctk.CTkFrame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        left_label = ctk.CTkLabel(left_frame, text="Study Material", font=ctk.CTkFont(size=18, weight="bold"))
        left_label.pack(pady=(8, 8))

        self.text_input = ctk.CTkTextbox(left_frame, width=450, height=380)
        self.text_input.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        left_button_frame = ctk.CTkFrame(left_frame)
        left_button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ctk.CTkButton(left_button_frame, text="Load PDF", command=self.load_pdf).pack(side=tk.LEFT, expand=True, padx=4)
        ctk.CTkButton(left_button_frame, text="Load Text", command=self.load_text_file).pack(side=tk.LEFT, expand=True, padx=4)
        ctk.CTkButton(left_button_frame, text="Clear", command=self._clear_text).pack(side=tk.LEFT, expand=True, padx=4)

        right_label = ctk.CTkLabel(right_frame, text="Tools & Output", font=ctk.CTkFont(size=18, weight="bold"))
        right_label.pack(pady=(8, 8))

        self.output_display = ctk.CTkTextbox(right_frame, width=450, height=320)
        self.output_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        right_button_frame = ctk.CTkFrame(right_frame)
        right_button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ctk.CTkButton(right_button_frame, text="Generate Flashcards", command=self.generate_flashcards).pack(fill=tk.X, pady=4)
        ctk.CTkButton(right_button_frame, text="Predict Exam Questions", command=self.predict_exam_questions).pack(fill=tk.X, pady=4)
        ctk.CTkButton(right_button_frame, text="Create Quiz", command=self.create_quiz).pack(fill=tk.X, pady=4)
        ctk.CTkButton(right_button_frame, text="Text Statistics", command=self.show_text_stats).pack(fill=tk.X, pady=4)
        ctk.CTkButton(right_button_frame, text="Export Flashcards", command=self.export_flashcards).pack(fill=tk.X, pady=4)
        ctk.CTkButton(right_button_frame, text="Export Exam Predictions", command=self.export_exam_predictions).pack(fill=tk.X, pady=4)
        ctk.CTkButton(right_button_frame, text="Export Quiz Results", command=self.export_quiz_results).pack(fill=tk.X, pady=4)
        ctk.CTkButton(right_button_frame, text="View Saved Data", command=self.view_saved_data).pack(fill=tk.X, pady=4)

        self.status_label = ctk.CTkLabel(self.root, text="Ready", anchor="w")
        self.status_label.pack(fill=tk.X, padx=12, pady=(0, 8))

    def _clear_text(self):
        self.text_input.delete("0.0", tk.END)
        self.current_text = ""
        self.status_label.configure(text="Input cleared")

    def load_pdf(self):
        filepath = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")])
        if filepath:
            text = FileReader.read_file(filepath)
            if text:
                self.text_input.delete("0.0", tk.END)
                self.text_input.insert("0.0", text)
                self.current_text = text
                self.status_label.configure(text=f"Loaded: {Path(filepath).name}")
            else:
                messagebox.showerror("Error", "Failed to read PDF")

    def load_text_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt"), ("Markdown files", "*.md"), ("All files", "*.*")])
        if filepath:
            text = FileReader.read_file(filepath)
            if text:
                self.text_input.delete("0.0", tk.END)
                self.text_input.insert("0.0", text)
                self.current_text = text
                self.status_label.configure(text=f"Loaded: {Path(filepath).name}")

    def enter_text_dialog(self):
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Enter Study Material")
        dialog.geometry("640x480")

        label = ctk.CTkLabel(dialog, text="Paste or type your study material:")
        label.pack(padx=12, pady=10)

        text_widget = ctk.CTkTextbox(dialog, width=600, height=320)
        text_widget.pack(fill=tk.BOTH, expand=True, padx=12, pady=6)

        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill=tk.X, padx=12, pady=10)

        def save_text():
            text = text_widget.get("0.0", tk.END)
            is_valid, message = TextInputHandler.validate_input(text)
            if is_valid:
                self.text_input.delete("0.0", tk.END)
                self.text_input.insert("0.0", text)
                self.current_text = TextInputHandler.process_input(text)
                self.status_label.configure(text="Text entered successfully")
                dialog.destroy()
            else:
                messagebox.showwarning("Invalid Input", message)

        ctk.CTkButton(button_frame, text="Save", command=save_text).pack(side=tk.LEFT, padx=8)
        ctk.CTkButton(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=8)

    def generate_flashcards(self):
        text = self.text_input.get("0.0", tk.END).strip()
        if not text:
            messagebox.showwarning("No Input", "Please enter or load study material first")
            return

        if not self.nlp_engine.is_ready():
            messagebox.showerror("NLP Error", "NLP engine not initialized. Check logs.")
            return

        self.status_label.configure(text="Generating flashcards...")
        self.root.update()

        try:
            self.flashcard_generator = FlashcardGenerator(self.nlp_engine)
            cards = self.flashcard_generator.generate_all(text, num_cards=50)
            self.current_deck = FlashcardDeck("Generated Deck")
            self.current_deck.add_cards(cards)
            self.current_flashcards = self.current_deck.to_dict_list()

            output = [f"Generated {len(cards)} Flashcards\n"]
            for i, card in enumerate(cards[:10], 1):
                output.extend([
                    f"{i}. Q: {card.question}",
                    f"   A: {card.answer[:60]}...",
                    f"   Tags: {', '.join(card.tags)}",
                    f"   Difficulty: {card.difficulty.name}\n",
                ])
            output.append(f"... and {len(cards) - 10} more cards")

            self.output_display.delete("0.0", tk.END)
            self.output_display.insert("0.0", "\n".join(output))
            self.status_label.configure(text=f"Successfully generated {len(cards)} flashcards")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate flashcards: {str(e)}")
            self.status_label.configure(text="Error generating flashcards")

    def predict_exam_questions(self):
        text = self.text_input.get("0.0", tk.END).strip()
        if not text:
            messagebox.showwarning("No Input", "Please enter or load study material first")
            return

        if not self.nlp_engine.is_ready():
            messagebox.showerror("NLP Error", "NLP engine not initialized")
            return

        self.status_label.configure(text="Predicting exam questions...")
        self.root.update()

        try:
            self.exam_predictor = ExamPredictor(self.nlp_engine)
            questions = self.exam_predictor.predict_questions(text, num_questions=20)
            self.current_exam_predictions = [q.to_dict() for q in questions]

            output = [f"Predicted {len(questions)} Exam Questions\n"]
            for i, q in enumerate(self.exam_predictor.rank_by_probability()[:10], 1):
                output.extend([
                    f"{i}. [{q.probability.name}] {q.question_type.value}",
                    f"   Q: {q.question}",
                    f"   Topic: {q.topic}\n",
                ])

            output.append(f"... and {len(questions) - 10} more questions")
            self.output_display.delete("0.0", tk.END)
            self.output_display.insert("0.0", "\n".join(output))
            self.status_label.configure(text=f"Successfully predicted {len(questions)} exam questions")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to predict questions: {str(e)}")
            self.status_label.configure(text="Error predicting exam questions")

    def create_quiz(self):
        if not self.current_deck or len(self.current_deck) == 0:
            messagebox.showwarning("No Flashcards", "Please generate flashcards first")
            return

        quiz_window = tk.Toplevel(self.root)
        quiz_window.title("Quiz")
        quiz_window.geometry("700x520")

        quiz_session = QuizGenerator.create_from_flashcards(self.current_deck.cards, quiz_name="Study Quiz", num_questions=10)

        self.current_quiz_data = {
            "quiz_name": quiz_session.quiz_name,
            "questions": [self._serialize_quiz_question(q) for q in quiz_session.questions],
        }
        self.data_manager.save_quiz_structure(self.current_quiz_data, quiz_session.quiz_name.replace(" ", "_"))
        self.status_label.configure(text="Quiz structure saved for review")

        QuizUI(quiz_window, quiz_session, self.data_manager, on_finish=self._quiz_finished)

    def show_text_stats(self):
        text = self.text_input.get("0.0", tk.END).strip()
        if not text:
            messagebox.showwarning("No Input", "Please enter or load study material first")
            return

        from utils import TextAnalyzer

        stats = TextAnalyzer.get_stats(text)
        output = ["TEXT STATISTICS\n"]
        for key, value in stats.items():
            output.append(f"{key.replace('_', ' ').title()}: {value}")

        if self.nlp_engine.is_ready():
            complexity = self.nlp_engine.analyze_text_complexity(text)
            output.append("\nCOMPLEXITY METRICS")
            for key, value in complexity.items():
                output.append(f"{key.replace('_', ' ').title()}: {value:.2f}")

        self.output_display.delete("0.0", tk.END)
        self.output_display.insert("0.0", "\n".join(output))

    def export_flashcards(self):
        if not self.current_deck or len(self.current_deck) == 0:
            messagebox.showwarning("No Flashcards", "Please generate flashcards first")
            return

        filename = self.data_manager.save_flashcards(self.current_deck.to_dict_list(), "exported")
        messagebox.showinfo("Exported", f"Flashcards saved to: {filename}")
        self.status_label.configure(text=f"Exported to {filename}")

    def export_exam_predictions(self):
        if not self.current_exam_predictions:
            messagebox.showwarning("No Prediction", "Please predict exam questions first")
            return

        filename = self.data_manager.save_exam_predictions(self.current_exam_predictions, "predicted_exam")
        messagebox.showinfo("Exported", f"Exam predictions saved to: {filename}")
        self.status_label.configure(text=f"Exported to {filename}")

    def export_quiz_results(self):
        if not self.current_quiz_results:
            messagebox.showwarning("No Quiz Results", "Please complete a quiz first")
            return

        filename = self.data_manager.save_quiz_results(self.current_quiz_results, self.current_quiz_results.get("quiz_name", "quiz"))
        messagebox.showinfo("Exported", f"Quiz results saved to: {filename}")
        self.status_label.configure(text=f"Exported to {filename}")

    def view_saved_data(self):
        SavedDataUI(self.root, self.data_manager)

    def _quiz_finished(self, results: dict):
        self.current_quiz_results = results
        self.data_manager.save_quiz_results(results, results.get("quiz_name", "quiz"))
        self.status_label.configure(text="Quiz completed and results saved")

    def _serialize_quiz_question(self, question):
        if hasattr(question, "question_type"):
            return {
                "question": question.question,
                "type": question.question_type.value,
                "probability": question.probability.name,
                "topic": question.topic,
                "answer": question.answer_key,
                "options": question.options,
            }

        return {
            "question": question.question,
            "answer": question.answer,
            "tags": question.tags,
            "difficulty": question.difficulty.name,
        }

    def show_about(self):
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
    def __init__(self, window: tk.Toplevel, quiz_session, data_manager: DataManager, on_finish: Optional[Callable] = None):
        self.window = window
        self.quiz_session = quiz_session
        self.data_manager = data_manager
        self.on_finish = on_finish

        self.create_ui()

    def create_ui(self):
        progress_frame = ctk.CTkFrame(self.window)
        progress_frame.pack(fill=tk.X, padx=10, pady=5)

        current, total = self.quiz_session.get_progress()
        ctk.CTkLabel(progress_frame, text=f"Question {current}/{total}").pack()

        question_frame = ctk.CTkFrame(self.window)
        question_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        question = self.quiz_session.get_current_question()
        question_text = question.question if hasattr(question, "question") else "No question"

        ctk.CTkLabel(question_frame, text=question_text, wraplength=640, justify=tk.LEFT).pack(pady=10)

        answer_frame = ctk.CTkFrame(self.window)
        answer_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.answer_input = ctk.CTkTextbox(answer_frame, width=660, height=120)
        self.answer_input.pack(fill=tk.BOTH, expand=True)

        button_frame = ctk.CTkFrame(self.window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        ctk.CTkButton(button_frame, text="Submit Answer", command=self.submit_answer).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(button_frame, text="Quit Quiz", command=self.window.destroy).pack(side=tk.LEFT, padx=5)

    def submit_answer(self):
        answer = self.answer_input.get("0.0", tk.END).strip()
        if not answer:
            messagebox.showwarning("No Answer", "Please enter an answer")
            return

        is_correct = self.quiz_session.submit_answer(answer)
        current, total = self.quiz_session.get_progress()

        if current >= total:
            results = self.quiz_session.finish()
            if self.on_finish:
                self.on_finish(results)
            self.show_results(results)
            self.window.destroy()
        else:
            messagebox.showinfo("Answer Submitted", f"{'Correct!' if is_correct else 'Incorrect'}")
            self.window.destroy()

    def show_results(self, results):
        messagebox.showinfo(
            "Quiz Complete",
            f"Score: {results['score_percentage']:.1f}%\n"
            f"Correct: {results['correct']}/{results['total_questions']}",
        )


class SavedDataUI:
    def __init__(self, parent: ctk.CTk, data_manager: DataManager):
        self.parent = parent
        self.data_manager = data_manager
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Saved Data Browser")
        self.window.geometry("820x620")
        self.selected_file = None

        self.create_ui()

    def create_ui(self):
        frame = ctk.CTkFrame(self.window)
        frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        top_frame = ctk.CTkFrame(frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))

        self.file_menu = ctk.CTkOptionMenu(top_frame, values=self.data_manager.list_saved_files("*.json"), command=self._on_file_selected)
        self.file_menu.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        ctk.CTkButton(top_frame, text="Refresh", command=self._refresh_file_list).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(top_frame, text="Save Changes", command=self._save_changes).pack(side=tk.LEFT, padx=5)

        self.editor = ctk.CTkTextbox(frame, width=780, height=520)
        self.editor.pack(fill=tk.BOTH, expand=True)

    def _refresh_file_list(self):
        files = self.data_manager.list_saved_files("*.json")
        self.file_menu.configure(values=files)

    def _on_file_selected(self, filename: str):
        self.selected_file = filename
        data = self.data_manager.load_saved_item(filename)
        if data is None:
            messagebox.showerror("Load Error", "Failed to load saved file.")
            return

        self.editor.delete("0.0", tk.END)
        self.editor.insert("0.0", json.dumps(data, indent=2))

    def _save_changes(self):
        if not self.selected_file:
            messagebox.showwarning("No File", "Please select a saved file first")
            return

        raw_data = self.editor.get("0.0", tk.END).strip()
        try:
            data = json.loads(raw_data)
        except json.JSONDecodeError as exc:
            messagebox.showerror("Invalid JSON", f"Cannot save: {exc}")
            return

        self.data_manager.save_json(self.selected_file, data)
        messagebox.showinfo("Saved", f"Changes saved to {self.selected_file}")


def run_gui():
    root = ctk.CTk()
    app = StudyAppGUI(root)
    root.mainloop()


__all__ = [
    'StudyAppGUI',
    'QuizUI',
    'SavedDataUI',
    'run_gui',
]
