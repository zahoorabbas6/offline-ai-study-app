"""Premium PySide6 GUI for Offline AI Study Engine."""

from pathlib import Path

from PySide6.QtCore import QThread, QSize, Qt, Signal
from PySide6.QtGui import QAction, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from utils import DataManager
from pdf_reader import FileReader
from nlp_engine import NLPEngine
from flashcards import Difficulty, Flashcard, FlashcardDeck, FlashcardGenerator
from exam_predictor import ExamPredictor, ExamProbability, ExamQuestion, QuestionType
from quiz_generator import QuizGenerator, WeaknessAnalyzer
from local_ai import LocalAIManager
from memory_store import StudyMemory


class ChatWorker(QThread):
    """Runs local AI chat without blocking the Qt event loop."""

    response_ready = Signal(str)

    def __init__(self, ai_manager, memory, message: str, current_text: str):
        super().__init__()
        self.ai_manager = ai_manager
        self.memory = memory
        self.message = message
        self.current_text = current_text

    def run(self) -> None:
        try:
            response = self.ai_manager.chat(
                self.message,
                current_text=self.current_text,
                memory_context=self.memory.build_context(self.current_text),
            )
            self.memory.add_chat_turn(self.message, response)
            self.response_ready.emit(response)
        except Exception:
            self.response_ready.emit(
                "Local AI is unavailable right now. The core study tools still work with the offline fallback system."
            )


class PremiumStudyApp(QMainWindow):
    """A polished, offline-first study engine UI built with PySide6."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Offline AI Study Engine - Premium")
        self.resize(1280, 860)

        self.data_manager = DataManager()
        self.memory = StudyMemory()
        self.ai_manager = LocalAIManager()
        self.local_ai_active = self.ai_manager.status.active
        self.nlp_engine = None
        self.current_text = ""
        self.current_deck = None
        self.current_flashcards = []
        self.current_exam_predictions = []
        self.current_quiz = None
        self.last_quiz_results = None
        self.splitter = None
        self.saved_group = None
        self.saved_files_list = None
        self.chat_worker = None

        self._create_actions()
        self._build_ui()
        self._apply_style()
        if self.local_ai_active:
            self._update_status(f"Ready - Local AI enabled: {self.ai_manager.status.model}")
        else:
            self._update_status(f"Ready - fallback mode. {self.ai_manager.status.message}")
        self._refresh_saved_files()

    def _create_actions(self) -> None:
        self.open_pdf_action = QAction("Open PDF...", self)
        self.open_pdf_action.triggered.connect(self.load_pdf)

        self.open_text_action = QAction("Open Text...", self)
        self.open_text_action.triggered.connect(self.load_text_file)

        self.clear_action = QAction("Clear Input", self)
        self.clear_action.triggered.connect(self._clear_text)

        self.generate_flashcards_action = QAction("Generate Flashcards", self)
        self.generate_flashcards_action.triggered.connect(self.generate_flashcards)

        self.predict_exam_questions_action = QAction("Predict Exam Questions", self)
        self.predict_exam_questions_action.triggered.connect(self.predict_exam_questions)

        self.start_quiz_action = QAction("Start Quiz", self)
        self.start_quiz_action.triggered.connect(self.start_quiz)

        self.show_stats_action = QAction("Text Statistics", self)
        self.show_stats_action.triggered.connect(self.show_text_stats)

    def _build_ui(self) -> None:
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(20, 20))
        toolbar.setMovable(False)
        toolbar.addAction(self.open_pdf_action)
        toolbar.addAction(self.open_text_action)
        toolbar.addSeparator()
        toolbar.addAction(self.generate_flashcards_action)
        toolbar.addAction(self.predict_exam_questions_action)
        toolbar.addAction(self.start_quiz_action)
        toolbar.addAction(self.show_stats_action)
        self.addToolBar(toolbar)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(18, 18, 18, 12)
        main_layout.setSpacing(14)

        left_panel, right_panel = self._build_panels()
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self._wrap_scroll_area(left_panel))
        self.splitter.addWidget(self._wrap_scroll_area(right_panel))
        self.splitter.setStretchFactor(0, 4)
        self.splitter.setStretchFactor(1, 6)
        self.splitter.setChildrenCollapsible(False)
        main_layout.addWidget(self.splitter, 1)

        self._status_bar = QStatusBar(self)
        self.setStatusBar(self._status_bar)

    @staticmethod
    def _wrap_scroll_area(widget: QWidget) -> QScrollArea:
        scroll_area = QScrollArea()
        scroll_area.setWidget(widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        return scroll_area

    def _build_panels(self):
        left_panel = QFrame()
        left_panel.setObjectName("Panel")
        left_panel.setMinimumWidth(360)
        left_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(18, 18, 18, 18)
        left_layout.setSpacing(12)

        title = QLabel("Study Material")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        left_layout.addWidget(title)

        subtitle = QLabel("Paste notes, textbook sections, or extracted PDF text. Everything runs locally.")
        subtitle.setObjectName("MutedLabel")
        subtitle.setWordWrap(True)
        left_layout.addWidget(subtitle)

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Paste or type study material here...")
        self.text_input.setMinimumHeight(260)
        self.text_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        left_layout.addWidget(self.text_input, 1)

        controls = QGridLayout()
        controls.setHorizontalSpacing(10)
        controls.setVerticalSpacing(10)

        load_text_button = QPushButton("Load Text")
        load_text_button.clicked.connect(self.load_text_file)
        load_pdf_button = QPushButton("Load PDF")
        load_pdf_button.clicked.connect(self.load_pdf)
        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self._clear_text)

        self.flashcard_count_input = QSpinBox()
        self.flashcard_count_input.setRange(5, 200)
        self.flashcard_count_input.setValue(50)
        self.flashcard_count_input.setMinimumWidth(120)
        self.exam_count_input = QSpinBox()
        self.exam_count_input.setRange(5, 100)
        self.exam_count_input.setValue(20)
        self.exam_count_input.setMinimumWidth(120)

        controls.addWidget(load_text_button, 0, 0)
        controls.addWidget(load_pdf_button, 0, 1)
        controls.addWidget(clear_button, 0, 2)
        controls.addWidget(QLabel("Flashcards"), 1, 0)
        controls.addWidget(self.flashcard_count_input, 1, 1)
        controls.addWidget(QLabel("Exam Questions"), 2, 0)
        controls.addWidget(self.exam_count_input, 2, 1)
        left_layout.addLayout(controls)

        note = QLabel("The window opens fast; offline NLP initializes when you generate cards, questions, or stats.")
        note.setWordWrap(True)
        note.setObjectName("MutedLabel")
        left_layout.addWidget(note)

        right_panel = QFrame()
        right_panel.setObjectName("Panel")
        right_panel.setMinimumWidth(480)
        right_panel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(12)

        results_title = QLabel("Study Workspace")
        results_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        right_layout.addWidget(results_title)

        action_buttons = QGridLayout()
        action_buttons.setHorizontalSpacing(10)
        action_buttons.setVerticalSpacing(10)
        flashcards_button = QPushButton("Generate Flashcards")
        flashcards_button.setObjectName("PrimaryButton")
        flashcards_button.clicked.connect(self.generate_flashcards)
        exam_button = QPushButton("Predict Exam Questions")
        exam_button.clicked.connect(self.predict_exam_questions)
        quiz_button = QPushButton("Start Quiz")
        quiz_button.clicked.connect(self.start_quiz)
        save_flashcards_button = QPushButton("Save Flashcards")
        save_flashcards_button.clicked.connect(self.save_flashcards_quick)
        save_exam_button = QPushButton("Save Exam Questions")
        save_exam_button.clicked.connect(self.save_exam_predictions_quick)

        for button in [flashcards_button, exam_button, quiz_button, save_flashcards_button, save_exam_button]:
            button.setMinimumHeight(40)
            button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        action_buttons.addWidget(flashcards_button, 0, 0)
        action_buttons.addWidget(exam_button, 0, 1)
        action_buttons.addWidget(quiz_button, 0, 2)
        action_buttons.addWidget(save_flashcards_button, 1, 0)
        action_buttons.addWidget(save_exam_button, 1, 1, 1, 2)
        right_layout.addLayout(action_buttons)

        self.result_tabs = QTabWidget()
        self.result_tabs.setDocumentMode(True)
        self.result_tabs.setUsesScrollButtons(True)
        self.result_tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)
        self.result_tabs.addTab(self.output_display, "Results")

        self.summary_display = QTextEdit()
        self.summary_display.setReadOnly(True)
        self.result_tabs.addTab(self.summary_display, "Summary")

        self.concepts_display = QTextEdit()
        self.concepts_display.setReadOnly(True)
        self.result_tabs.addTab(self.concepts_display, "Concepts")

        self.flashcards_panel = self._build_flashcard_editor()
        self.result_tabs.addTab(self.flashcards_panel, "Flashcards")

        self.quiz_panel = self._build_quiz_panel()
        self.result_tabs.addTab(self.quiz_panel, "Quiz")

        if self.local_ai_active:
            self.chat_panel = self._build_chat_panel()
            self.result_tabs.addTab(self.chat_panel, "AI Chat")
        else:
            self.chat_notice_panel = self._build_chat_notice_panel()
            self.result_tabs.addTab(self.chat_notice_panel, "AI Chat")

        self.saved_group = QGroupBox("Saved Study Items")
        saved_layout = QVBoxLayout(self.saved_group)
        self.saved_files_list = QListWidget()
        self.saved_files_list.itemClicked.connect(self._load_saved_item)
        self.saved_files_list.setMaximumHeight(150)
        saved_layout.addWidget(self.saved_files_list)

        right_layout.addWidget(self.result_tabs, 6)
        right_layout.addWidget(self.saved_group, 1)
        return left_panel, right_panel

    def _build_chat_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.chat_history_display = QTextEdit()
        self.chat_history_display.setReadOnly(True)
        self.chat_history_display.setMinimumHeight(300)
        self.chat_history_display.setPlaceholderText("Local AI chat history")
        layout.addWidget(self.chat_history_display, 1)

        self.chat_input = QTextEdit()
        self.chat_input.setMinimumHeight(90)
        self.chat_input.setMaximumHeight(130)
        self.chat_input.setPlaceholderText("Ask about the material, request flashcards, or create quiz questions...")
        layout.addWidget(self.chat_input)

        button_row = QHBoxLayout()
        self.chat_send_button = QPushButton("Send")
        self.chat_send_button.setObjectName("PrimaryButton")
        self.chat_send_button.clicked.connect(self.send_chat_message)
        self.chat_clear_button = QPushButton("Clear Chat")
        self.chat_clear_button.clicked.connect(self.clear_chat)
        button_row.addWidget(self.chat_send_button)
        button_row.addWidget(self.chat_clear_button)
        layout.addLayout(button_row)
        return panel

    def _build_chat_notice_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        notice = QLabel("⚠️ Full AI Chat Feature requires Ollama to be installed and running locally.")
        notice.setWordWrap(True)
        notice.setObjectName("MutedLabel")
        notice.setFont(QFont("Segoe UI", 13))
        layout.addWidget(notice)
        layout.addStretch(1)
        return panel

    def _build_flashcard_editor(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        editor_splitter = QSplitter(Qt.Orientation.Vertical)
        editor_splitter.setChildrenCollapsible(False)

        self.flashcards_list = QListWidget()
        self.flashcards_list.itemClicked.connect(self._on_flashcard_selected)
        self.flashcards_list.setMinimumHeight(130)
        self.flashcards_list.setAlternatingRowColors(True)
        self.flashcards_list.setStyleSheet("font-size: 12pt;")
        editor_splitter.addWidget(self.flashcards_list)

        editor_panel = QWidget()
        editor_layout = QVBoxLayout(editor_panel)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(12)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setFormAlignment(Qt.AlignmentFlag.AlignTop)
        form_layout.setHorizontalSpacing(14)
        form_layout.setVerticalSpacing(12)
        self.card_question_edit = QTextEdit()
        self.card_question_edit.setMinimumHeight(96)
        self.card_question_edit.setMaximumHeight(140)
        self.card_question_edit.setFont(QFont("Segoe UI", 12))
        self.card_answer_edit = QTextEdit()
        self.card_answer_edit.setMinimumHeight(190)
        self.card_answer_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.card_answer_edit.setFont(QFont("Segoe UI", 12))
        self.card_tags_edit = QLineEdit()
        self.card_tags_edit.setMinimumHeight(44)
        self.card_tags_edit.setFont(QFont("Segoe UI", 12))
        self.card_difficulty_edit = QComboBox()
        self.card_difficulty_edit.setMinimumHeight(44)
        self.card_difficulty_edit.setFont(QFont("Segoe UI", 12))
        self.card_difficulty_edit.addItems(["EASY", "MEDIUM", "HARD"])

        form_layout.addRow("Question:", self.card_question_edit)
        form_layout.addRow("Answer:", self.card_answer_edit)
        form_layout.addRow("Tags:", self.card_tags_edit)
        form_layout.addRow("Difficulty:", self.card_difficulty_edit)
        editor_layout.addLayout(form_layout, 1)

        self.card_save_button = QPushButton("Save Card Changes")
        self.card_save_button.setMinimumHeight(44)
        self.card_save_button.clicked.connect(self._save_flashcard_changes)
        card_button_row = QHBoxLayout()
        card_button_row.addWidget(self.card_save_button)
        save_deck_button = QPushButton("Save Flashcards")
        save_deck_button.setMinimumHeight(44)
        save_deck_button.clicked.connect(self.save_flashcards_quick)
        card_button_row.addWidget(save_deck_button)
        editor_layout.addLayout(card_button_row)

        editor_splitter.addWidget(editor_panel)
        editor_splitter.setStretchFactor(0, 2)
        editor_splitter.setStretchFactor(1, 5)
        layout.addWidget(editor_splitter, 1)
        return panel

    def _build_quiz_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        controls = QGridLayout()
        controls.setHorizontalSpacing(10)
        controls.setVerticalSpacing(10)

        self.quiz_source_combo = QComboBox()
        self.quiz_source_combo.addItems(["Flashcards", "Exam Questions"])
        self.quiz_count_input = QSpinBox()
        self.quiz_count_input.setRange(1, 100)
        self.quiz_count_input.setValue(10)
        self.quiz_start_button = QPushButton("Start Quiz")
        self.quiz_start_button.setObjectName("PrimaryButton")
        self.quiz_start_button.clicked.connect(self.start_quiz)

        controls.addWidget(QLabel("Source"), 0, 0)
        controls.addWidget(self.quiz_source_combo, 0, 1)
        controls.addWidget(QLabel("Questions"), 0, 2)
        controls.addWidget(self.quiz_count_input, 0, 3)
        controls.addWidget(self.quiz_start_button, 0, 4)
        layout.addLayout(controls)

        self.quiz_progress_label = QLabel("No quiz started")
        self.quiz_progress_label.setObjectName("MutedLabel")
        layout.addWidget(self.quiz_progress_label)

        self.quiz_question_display = QTextEdit()
        self.quiz_question_display.setReadOnly(True)
        self.quiz_question_display.setMinimumHeight(170)
        self.quiz_question_display.setFont(QFont("Segoe UI", 12))
        layout.addWidget(self.quiz_question_display, 2)

        self.quiz_answer_edit = QTextEdit()
        self.quiz_answer_edit.setPlaceholderText("Type your answer here...")
        self.quiz_answer_edit.setMinimumHeight(120)
        self.quiz_answer_edit.setFont(QFont("Segoe UI", 12))
        layout.addWidget(self.quiz_answer_edit, 1)

        quiz_buttons = QHBoxLayout()
        self.quiz_submit_button = QPushButton("Submit Answer")
        self.quiz_submit_button.clicked.connect(self.submit_quiz_answer)
        self.quiz_reveal_button = QPushButton("Show Answer")
        self.quiz_reveal_button.clicked.connect(self.reveal_quiz_answer)
        self.quiz_finish_button = QPushButton("Finish Quiz")
        self.quiz_finish_button.clicked.connect(self.finish_quiz)
        for button in [self.quiz_submit_button, self.quiz_reveal_button, self.quiz_finish_button]:
            button.setMinimumHeight(42)
            quiz_buttons.addWidget(button)
        layout.addLayout(quiz_buttons)

        self.quiz_feedback_display = QTextEdit()
        self.quiz_feedback_display.setReadOnly(True)
        self.quiz_feedback_display.setMinimumHeight(120)
        layout.addWidget(self.quiz_feedback_display, 1)
        return panel

    def _apply_style(self) -> None:
        self.setFont(QFont("Segoe UI", 10))
        self.setStyleSheet(
            """
            QMainWindow {
                background: #f4f6f8;
                color: #17202a;
            }
            QToolBar {
                background: #ffffff;
                border: 0;
                border-bottom: 1px solid #d8dee6;
                spacing: 8px;
                padding: 8px;
            }
            QFrame#Panel, QGroupBox {
                background: #ffffff;
                border: 1px solid #d8dee6;
                border-radius: 8px;
            }
            QGroupBox {
                margin-top: 12px;
                padding: 14px 10px 10px 10px;
                font-weight: 600;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
            QLabel#MutedLabel {
                color: #5d6b7a;
            }
            QTextEdit, QLineEdit, QListWidget, QComboBox, QSpinBox {
                background: #fbfcfd;
                border: 1px solid #cfd7e1;
                border-radius: 6px;
                padding: 8px;
                selection-background-color: #2563eb;
            }
            QTextEdit:focus, QLineEdit:focus, QListWidget:focus, QComboBox:focus, QSpinBox:focus {
                border: 1px solid #2563eb;
                background: #ffffff;
            }
            QPushButton {
                background: #edf2f7;
                border: 1px solid #ccd6e0;
                border-radius: 6px;
                padding: 9px 12px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #e2e8f0;
            }
            QPushButton#PrimaryButton {
                background: #2563eb;
                border-color: #1d4ed8;
                color: white;
            }
            QPushButton#PrimaryButton:hover {
                background: #1d4ed8;
            }
            QTabWidget::pane {
                border: 1px solid #d8dee6;
                border-radius: 6px;
                background: #ffffff;
            }
            QTabBar::tab {
                background: #edf2f7;
                border: 1px solid #d8dee6;
                border-bottom: 0;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                padding: 9px 14px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                color: #1d4ed8;
            }
            QStatusBar {
                background: #ffffff;
                border-top: 1px solid #d8dee6;
                color: #5d6b7a;
            }
            """
        )

    def _update_status(self, text: str) -> None:
        self._status_bar.showMessage(text)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self.splitter is None:
            return

        if self.width() < 900:
            self.splitter.setOrientation(Qt.Orientation.Vertical)
            self.splitter.setSizes([self.height() // 2, self.height() // 2])
            if self.saved_files_list is not None:
                self.saved_files_list.setMaximumHeight(110)
        else:
            self.splitter.setOrientation(Qt.Orientation.Horizontal)
            self.splitter.setSizes([max(360, self.width() * 4 // 10), max(480, self.width() * 6 // 10)])
            if self.saved_files_list is not None:
                self.saved_files_list.setMaximumHeight(150)

    def _get_nlp_engine(self):
        if self.nlp_engine is None:
            self._update_status("Loading offline NLP engine...")
            QApplication.processEvents()
            self.nlp_engine = NLPEngine()
            if self.nlp_engine.is_ready():
                self._update_status(f"NLP ready: {self.nlp_engine.model_name}")
            else:
                self._update_status("NLP engine unavailable")
        return self.nlp_engine

    def _clear_text(self) -> None:
        self.text_input.clear()
        self.current_text = ""
        self._update_status("Input cleared")

    def _remember_document(self, text: str, source: str) -> None:
        try:
            summary = ""
            nlp_engine = self._get_nlp_engine()
            if nlp_engine and nlp_engine.is_ready():
                summary = nlp_engine.generate_summary(text, sentence_count=3)
            self.memory.add_document(text, source=source, summary=summary)
        except Exception:
            self.memory.add_document(text, source=source, summary=text[:500])

    def _refresh_saved_files(self) -> None:
        self.saved_files_list.clear()
        files = [
            filename
            for filename in self.data_manager.list_saved_files("*.json")
            if not filename.startswith("study_memory")
        ]
        for filename in sorted(files, reverse=True):
            self.saved_files_list.addItem(filename)

    def _load_saved_item(self, item) -> None:
        filename = item.text()
        saved = self.data_manager.load_saved_item(filename)
        if not saved:
            QMessageBox.warning(self, "Load Failed", f"Unable to load {filename}")
            return

        if isinstance(saved, dict) and "cards" in saved and isinstance(saved["cards"], list):
            self.current_flashcards = saved["cards"]
            self._refresh_flashcard_editor()
            self.result_tabs.setCurrentWidget(self.flashcards_panel)
            self._update_status(f"Loaded flashcards from {filename}")
            return

        if isinstance(saved, dict) and "questions" in saved and isinstance(saved["questions"], list):
            self.current_exam_predictions = saved["questions"]
            self.output_display.setPlainText(self._format_exam_predictions(self.current_exam_predictions))
            self.result_tabs.setCurrentWidget(self.output_display)
            self._update_status(f"Loaded exam questions from {filename}")
            return

        if isinstance(saved, list) and all(isinstance(row, dict) and "question" in row for row in saved):
            if all("answer" in row and "difficulty" in row for row in saved):
                self.current_flashcards = saved
                self._refresh_flashcard_editor()
                self.result_tabs.setCurrentWidget(self.flashcards_panel)
                self._update_status(f"Loaded flashcards from {filename}")
            else:
                self.current_exam_predictions = saved
                self.output_display.setPlainText(self._format_exam_predictions(self.current_exam_predictions))
                self.result_tabs.setCurrentWidget(self.output_display)
                self._update_status(f"Loaded exam questions from {filename}")
            return

        self.output_display.setPlainText(f"Loaded {filename}\n\n{saved}")
        self._update_status(f"Loaded saved data: {filename}")

    def load_pdf(self) -> None:
        filepath, _ = QFileDialog.getOpenFileName(self, "Open PDF", str(Path.cwd()), "PDF Files (*.pdf);;All Files (*)")
        if filepath:
            text = FileReader.read_file(filepath)
            if text:
                self.text_input.setPlainText(text)
                self.current_text = text
                self._remember_document(text, str(Path(filepath).name))
                self._update_status(f"Loaded PDF: {Path(filepath).name}")
            else:
                QMessageBox.critical(self, "Read Error", "Unable to read the selected PDF file.")

    def load_text_file(self) -> None:
        filepath, _ = QFileDialog.getOpenFileName(self, "Open Text File", str(Path.cwd()), "Text Files (*.txt *.md);;All Files (*)")
        if filepath:
            text = FileReader.read_file(filepath)
            if text:
                self.text_input.setPlainText(text)
                self.current_text = text
                self._remember_document(text, str(Path(filepath).name))
                self._update_status(f"Loaded file: {Path(filepath).name}")

    def generate_flashcards(self) -> None:
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Missing Input", "Please enter or load text before generating flashcards.")
            return

        card_count = self.flashcard_count_input.value()
        self._update_status("Generating flashcards...")
        QApplication.processEvents()

        nlp_engine = self._get_nlp_engine()
        if not nlp_engine.is_ready() and not self.ai_manager.is_active():
            QMessageBox.critical(self, "NLP Error", "NLP engine not initialized.")
            self._update_status("NLP engine unavailable")
            return

        self.current_text = text
        cards = []
        if self.ai_manager.is_active():
            self._update_status("Generating local AI flashcards...")
            QApplication.processEvents()
            ai_cards = self.ai_manager.generate_flashcards(
                text,
                card_count,
                self.memory.build_context(text),
            )
            cards = self._flashcards_from_dicts(ai_cards)

        if not cards:
            self._update_status("Generating offline fallback flashcards...")
            QApplication.processEvents()
            generator = FlashcardGenerator(nlp_engine)
            cards = generator.generate_all(text, num_cards=card_count)

        self.current_deck = FlashcardDeck("Premium Offline Deck")
        self.current_deck.add_cards(cards)
        self.current_flashcards = self.current_deck.to_dict_list()
        summary = nlp_engine.generate_summary(text, sentence_count=3) if nlp_engine.is_ready() else text[:500]
        self.memory.add_document(text, source="current_input", summary=summary)
        self.memory.add_flashcards(self.current_flashcards)
        self._refresh_flashcard_editor()

        output_lines = [f"Generated {len(cards)} flashcards:\n"]
        for index, card in enumerate(cards[:12], 1):
            output_lines.append(f"{index}. Q: {card.question}")
            output_lines.append(f"   A: {card.answer}")
            output_lines.append(f"   Tags: {', '.join(card.tags)}")
            output_lines.append(f"   Difficulty: {card.difficulty.name}\n")
        if len(cards) > 12:
            output_lines.append(f"...and {len(cards) - 12} more cards")

        self.output_display.setPlainText("\n".join(output_lines))
        self.summary_display.setPlainText(nlp_engine.generate_summary(text, sentence_count=5) if nlp_engine.is_ready() else summary)
        if nlp_engine.is_ready():
            self._render_concepts(text)
        self.result_tabs.setCurrentWidget(self.flashcards_panel)
        self._update_status(f"Generated {len(cards)} flashcards")

    def predict_exam_questions(self) -> None:
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Missing Input", "Please enter or load text before predicting exam questions.")
            return

        question_count = self.exam_count_input.value()
        self._update_status("Predicting exam questions...")
        QApplication.processEvents()

        nlp_engine = self._get_nlp_engine()
        if not nlp_engine.is_ready() and not self.ai_manager.is_active():
            QMessageBox.critical(self, "NLP Error", "NLP engine not initialized.")
            self._update_status("NLP engine unavailable")
            return

        self.current_text = text
        predictor = None
        questions = []
        if self.ai_manager.is_active():
            self._update_status("Predicting with local AI...")
            QApplication.processEvents()
            ai_questions = self.ai_manager.generate_exam_questions(
                text,
                question_count,
                self.memory.build_context(text),
            )
            questions = self._exam_questions_from_dicts(ai_questions)

        if not questions:
            self._update_status("Predicting with offline fallback...")
            QApplication.processEvents()
            predictor = ExamPredictor(nlp_engine)
            questions = predictor.predict_questions(text, num_questions=question_count)

        self.current_exam_predictions = [question.to_dict() for question in questions]
        summary = nlp_engine.generate_summary(text, sentence_count=3) if nlp_engine.is_ready() else text[:500]
        self.memory.add_document(text, source="current_input", summary=summary)
        self.memory.add_exam_questions(self.current_exam_predictions)

        output_lines = [f"Predicted {len(questions)} exam questions:\n"]
        ranked_questions = predictor.rank_by_probability() if predictor else sorted(
            questions,
            key=lambda question: question.probability.value,
            reverse=True,
        )
        for index, question in enumerate(ranked_questions[:12], 1):
            output_lines.append(f"{index}. [{question.probability.name}] {question.question_type.value}")
            output_lines.append(f"   Q: {question.question}")
            output_lines.append(f"   Topic: {question.topic}")
            if question.options:
                output_lines.append("   Options: " + " | ".join(question.options))
            output_lines.append("")
        if len(questions) > 12:
            output_lines.append(f"...and {len(questions) - 12} more questions")

        self.output_display.setPlainText("\n".join(output_lines))
        self.summary_display.setPlainText(nlp_engine.generate_summary(text, sentence_count=5) if nlp_engine.is_ready() else summary)
        if nlp_engine.is_ready():
            self._render_concepts(text)
        self.result_tabs.setCurrentWidget(self.output_display)
        self._update_status(f"Predicted {len(questions)} exam questions")

    def show_text_stats(self) -> None:
        text = self.text_input.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "No Text", "Load or paste study material to view statistics.")
            return

        nlp_engine = self._get_nlp_engine()
        if not nlp_engine.is_ready():
            QMessageBox.critical(self, "NLP Error", "NLP engine not initialized.")
            self._update_status("NLP engine unavailable")
            return

        stats = nlp_engine.analyze_text_complexity(text)
        lines = ["Text Statistics:\n"]
        for key, value in stats.items():
            label = key.replace("_", " ").title()
            if isinstance(value, float):
                lines.append(f"{label}: {value:.2f}")
            else:
                lines.append(f"{label}: {value}")

        self.output_display.setPlainText("\n".join(lines))
        self._render_concepts(text)
        self.result_tabs.setCurrentWidget(self.output_display)
        self._update_status("Calculated text statistics")

    def _render_concepts(self, text: str) -> None:
        nlp_engine = self._get_nlp_engine()
        concepts = nlp_engine.extract_concepts(text)
        lines = ["Key Topics:"]
        topics = concepts.get("topics", [])
        lines.extend(f"- {topic}" for topic in topics[:12])
        if not topics:
            lines.append("- No strong topics detected.")

        lines.append("\nKeywords:")
        keywords = concepts.get("keywords", [])
        lines.extend(f"- {keyword}" for keyword in keywords[:18])
        if not keywords:
            lines.append("- No keywords detected.")

        lines.append("\nDefinitions:")
        definitions = concepts.get("definitions", [])
        if definitions:
            lines.extend(f"- {term}: {definition}" for term, definition in definitions[:10])
        else:
            lines.append("- No explicit definitions found.")

        lines.append("\nTop Evidence Sentences:")
        top_sentences = concepts.get("top_sentences", [])
        lines.extend(f"- {sentence}" for sentence in top_sentences[:8])
        if not top_sentences:
            lines.append("- No evidence sentences ranked.")

        self.concepts_display.setPlainText("\n".join(lines))

    def send_chat_message(self) -> None:
        if not self.local_ai_active:
            self.output_display.setPlainText("⚠️ Full AI Chat Feature requires Ollama to be installed and running locally.")
            return

        message = self.chat_input.toPlainText().strip()
        if not message:
            return

        current_text = self.text_input.toPlainText().strip()
        self.chat_input.clear()
        self.chat_history_display.append(f"Student:\n{message}\n")
        self.chat_history_display.append("AI:\nThinking locally...\n")
        self.chat_send_button.setEnabled(False)
        self._update_status("Local AI chat is responding...")

        self.chat_worker = ChatWorker(self.ai_manager, self.memory, message, current_text)
        self.chat_worker.response_ready.connect(self._chat_response_ready)
        self.chat_worker.start()

    def _chat_response_ready(self, response: str) -> None:
        history = self.chat_history_display.toPlainText()
        marker = "AI:\nThinking locally...\n"
        if marker in history:
            history = history.replace(marker, f"AI:\n{response}\n", 1)
            self.chat_history_display.setPlainText(history)
        else:
            self.chat_history_display.append(f"AI:\n{response}\n")
        self.chat_send_button.setEnabled(True)
        self._update_status("Local AI chat ready")

    def clear_chat(self) -> None:
        if self.local_ai_active:
            self.chat_history_display.clear()
            self._update_status("Chat cleared")

    def export_flashcards(self) -> None:
        if not self.current_flashcards:
            QMessageBox.warning(self, "No Flashcards", "Generate flashcards before exporting.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Flashcards",
            str(Path.cwd() / "flashcards.json"),
            "JSON Files (*.json)",
        )
        if filename:
            self.data_manager.save_json(Path(filename).name, {"cards": self.current_flashcards})
            self._update_status(f"Saved flashcards to {Path(filename).name}")
            self._refresh_saved_files()

    def save_flashcards_quick(self) -> None:
        if not self.current_flashcards:
            QMessageBox.warning(self, "No Flashcards", "Generate or open flashcards before saving.")
            return

        filename = self.data_manager.save_flashcards(self.current_flashcards, "gui")
        self._refresh_saved_files()
        self._update_status(f"Saved flashcards: {filename}")
        QMessageBox.information(self, "Flashcards Saved", f"Saved flashcards to study_data/{filename}")

    def export_exam_predictions(self) -> None:
        if not self.current_exam_predictions:
            QMessageBox.warning(self, "No Predictions", "Predict exam questions before exporting.")
            return

        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Exam Predictions",
            str(Path.cwd() / "exam_predictions.json"),
            "JSON Files (*.json)",
        )
        if filename:
            self.data_manager.save_json(Path(filename).name, {"questions": self.current_exam_predictions})
            self._update_status(f"Saved exam predictions to {Path(filename).name}")
            self._refresh_saved_files()

    def save_exam_predictions_quick(self) -> None:
        if not self.current_exam_predictions:
            QMessageBox.warning(self, "No Predictions", "Predict exam questions before saving.")
            return

        filename = self.data_manager.save_exam_predictions(self.current_exam_predictions, "gui")
        self._refresh_saved_files()
        self._update_status(f"Saved exam questions: {filename}")
        QMessageBox.information(self, "Exam Questions Saved", f"Saved exam questions to study_data/{filename}")

    def start_quiz(self) -> None:
        source = self.quiz_source_combo.currentText() if hasattr(self, "quiz_source_combo") else "Flashcards"
        count = self.quiz_count_input.value() if hasattr(self, "quiz_count_input") else 10

        if source == "Flashcards":
            flashcards = self._flashcards_from_dicts(self.current_flashcards)
            if not flashcards:
                QMessageBox.warning(self, "No Flashcards", "Generate or open flashcards before starting a quiz.")
                return
            self.current_quiz = QuizGenerator.create_from_flashcards(
                flashcards,
                quiz_name="Flashcard Practice",
                num_questions=count,
            )
        else:
            exam_questions = self._exam_questions_from_dicts(self.current_exam_predictions)
            if not exam_questions:
                QMessageBox.warning(self, "No Exam Questions", "Predict exam questions before starting this quiz.")
                return
            self.current_quiz = QuizGenerator.create_from_exam_questions(
                exam_questions,
                quiz_name="Exam Question Practice",
                num_questions=count,
            )

        self.last_quiz_results = None
        self.quiz_feedback_display.clear()
        self.quiz_answer_edit.clear()
        self.result_tabs.setCurrentWidget(self.quiz_panel)
        self._show_current_quiz_question()
        self._update_status(f"Started quiz: {self.current_quiz.quiz_name}")

    def submit_quiz_answer(self) -> None:
        if not self.current_quiz:
            QMessageBox.warning(self, "No Quiz", "Start a quiz first.")
            return

        question = self.current_quiz.get_current_question()
        if not question:
            self.finish_quiz()
            return

        answer = self.quiz_answer_edit.toPlainText().strip()
        if not answer:
            QMessageBox.warning(self, "Missing Answer", "Type an answer before submitting.")
            return

        correct = self.current_quiz.submit_answer(answer)
        correct_answer = self._question_answer(question)
        status = "Correct" if correct else "Review needed"
        self.quiz_feedback_display.setPlainText(
            f"{status}\n\nYour answer:\n{answer}\n\nSuggested answer:\n{correct_answer}"
        )
        self.quiz_answer_edit.clear()

        if self.current_quiz.get_current_question() is None:
            self.finish_quiz()
        else:
            self._show_current_quiz_question()

    def reveal_quiz_answer(self) -> None:
        if not self.current_quiz:
            QMessageBox.warning(self, "No Quiz", "Start a quiz first.")
            return

        question = self.current_quiz.get_current_question()
        if not question:
            self.finish_quiz()
            return

        self.quiz_feedback_display.setPlainText(f"Suggested answer:\n{self._question_answer(question)}")

    def finish_quiz(self) -> None:
        if not self.current_quiz:
            QMessageBox.warning(self, "No Quiz", "Start a quiz first.")
            return

        self.last_quiz_results = self.current_quiz.finish()
        self.memory.add_quiz_result(self.last_quiz_results)
        analysis = WeaknessAnalyzer.analyze_session(self.last_quiz_results)
        filename = self.data_manager.save_quiz_results(self.last_quiz_results, "gui")
        self._refresh_saved_files()

        self.quiz_progress_label.setText("Quiz finished")
        self.quiz_question_display.setPlainText("Quiz complete.")
        self.quiz_feedback_display.setPlainText(
            "\n".join(
                [
                    f"Score: {analysis['accuracy']}",
                    f"Performance: {analysis['performance_level']}",
                    f"Correct: {self.last_quiz_results['correct']}",
                    f"Incorrect: {self.last_quiz_results['incorrect']}",
                    f"Saved results: study_data/{filename}",
                    "",
                    "Recommendations:",
                    *[f"- {item}" for item in analysis["recommendations"]],
                ]
            )
        )
        self._update_status(f"Quiz finished with {analysis['accuracy']} score")

    def _show_current_quiz_question(self) -> None:
        question = self.current_quiz.get_current_question()
        current, total = self.current_quiz.get_progress()
        self.quiz_progress_label.setText(f"Question {current + 1} of {total}")

        lines = [self._question_prompt(question)]
        options = getattr(question, "options", None)
        if options:
            lines.append("")
            lines.append("Options:")
            lines.extend(f"{index}. {option}" for index, option in enumerate(options, 1))

        self.quiz_question_display.setPlainText("\n".join(lines))

    @staticmethod
    def _question_prompt(question) -> str:
        return getattr(question, "question", "Question unavailable")

    @staticmethod
    def _question_answer(question) -> str:
        if isinstance(question, Flashcard):
            return question.answer
        return getattr(question, "answer_key", None) or "See study material."

    @staticmethod
    def _flashcards_from_dicts(cards) -> list:
        flashcards = []
        for card in cards:
            difficulty_name = card.get("difficulty", "MEDIUM")
            difficulty = Difficulty.__members__.get(difficulty_name, Difficulty.MEDIUM)
            flashcards.append(
                Flashcard(
                    question=card.get("question", ""),
                    answer=card.get("answer", ""),
                    tags=card.get("tags", []) if isinstance(card.get("tags", []), list) else [],
                    difficulty=difficulty,
                    source_sentence=card.get("source"),
                )
            )
        return [card for card in flashcards if card.question and card.answer]

    @staticmethod
    def _exam_questions_from_dicts(questions) -> list:
        exam_questions = []
        type_by_value = {item.value: item for item in QuestionType}
        for question in questions:
            question_type = type_by_value.get(question.get("type"), QuestionType.SHORT_ANSWER)
            probability = ExamProbability.__members__.get(question.get("probability", "MEDIUM"), ExamProbability.MEDIUM)
            exam_questions.append(
                ExamQuestion(
                    question=question.get("question", ""),
                    question_type=question_type,
                    probability=probability,
                    topic=question.get("topic", "General"),
                    reasoning=question.get("reasoning", ""),
                    answer_key=question.get("answer") or "See study material.",
                    options=question.get("options") or [],
                )
            )
        return [question for question in exam_questions if question.question]

    @staticmethod
    def _format_exam_predictions(questions) -> str:
        lines = [f"Loaded {len(questions)} exam questions:\n"]
        for index, question in enumerate(questions[:25], 1):
            lines.append(f"{index}. [{question.get('probability', 'MEDIUM')}] {question.get('type', 'Question')}")
            lines.append(f"   Q: {question.get('question', '')}")
            lines.append(f"   Topic: {question.get('topic', 'General')}")
            if question.get("options"):
                lines.append("   Options: " + " | ".join(question["options"]))
            if question.get("answer"):
                lines.append(f"   Answer: {question.get('answer')}")
            lines.append("")
        if len(questions) > 25:
            lines.append(f"...and {len(questions) - 25} more questions")
        return "\n".join(lines)

    def _refresh_flashcard_editor(self) -> None:
        self.flashcards_list.clear()
        for index, card in enumerate(self.current_flashcards, start=1):
            question = card.get("question", "Untitled")
            self.flashcards_list.addItem(f"{index}. {question}")

        if self.current_flashcards:
            self.flashcards_list.setCurrentRow(0)
            self._populate_card_fields(0)

    def _on_flashcard_selected(self, item) -> None:
        row = self.flashcards_list.currentRow()
        if 0 <= row < len(self.current_flashcards):
            self._populate_card_fields(row)

    def _populate_card_fields(self, index: int) -> None:
        card = self.current_flashcards[index]
        self.card_question_edit.setPlainText(card.get("question", ""))
        self.card_answer_edit.setPlainText(card.get("answer", ""))
        tags = card.get("tags", [])
        self.card_tags_edit.setText(", ".join(tags) if isinstance(tags, list) else str(tags))
        difficulty = card.get("difficulty", "MEDIUM")
        difficulty_index = self.card_difficulty_edit.findText(difficulty)
        self.card_difficulty_edit.setCurrentIndex(difficulty_index if difficulty_index >= 0 else 1)

    def _save_flashcard_changes(self) -> None:
        row = self.flashcards_list.currentRow()
        if row < 0 or row >= len(self.current_flashcards):
            QMessageBox.warning(self, "No Card Selected", "Select a flashcard to save your changes.")
            return

        card = self.current_flashcards[row]
        card["question"] = self.card_question_edit.toPlainText().strip()
        card["answer"] = self.card_answer_edit.toPlainText().strip()
        tags_text = self.card_tags_edit.text().strip()
        card["tags"] = [tag.strip() for tag in tags_text.split(",") if tag.strip()]
        card["difficulty"] = self.card_difficulty_edit.currentText()

        self.flashcards_list.currentItem().setText(f"{row + 1}. {card['question']}")
        self._update_status(f"Saved changes for card {row + 1}")


def run_gui() -> None:
    app = QApplication([])
    window = PremiumStudyApp()
    window.show()
    app.exec()
