# Offline AI Study App

A production-ready offline study assistant that turns PDFs, text files, Markdown, and raw notes into flashcards, predicted exam questions, quizzes, summaries, and weakness analysis. The app runs locally and can optionally use Ollama for stronger local AI output when Ollama is installed and running.

## What It Does

- Reads PDF, TXT, Markdown, and pasted raw text
- Generates flashcards from study material
- Predicts likely exam questions with probability labels
- Creates practice quizzes from flashcards or exam predictions
- Tracks quiz results and weakness analysis
- Saves study data locally
- Detects Ollama automatically for enhanced local AI mode
- Enables full GUI AI chat only when Ollama is available
- Falls back safely to the built-in offline NLP system when Ollama is missing or fails

## Local AI Mode

The app checks Ollama on startup and before local AI requests.

Detection flow:

```text
Check if Ollama is installed
Check if Ollama is running at http://localhost:11434
Check if at least one local model is available
If all checks pass, enable Local AI Mode
Otherwise, keep the app in offline fallback mode
```

When Local AI Mode is active, Ollama can enhance:

- Flashcard generation
- Exam question prediction
- AI chat responses
- Memory-aware study output

When Local AI Mode is not active:

- Flashcards still work
- Quizzes still work
- Exam prediction still works
- Text extraction still works
- The full AI chat feature is not enabled
- The GUI shows this warning:

```text
Full AI Chat Feature requires Ollama to be installed and running locally.
```

## Full GUI AI Chat

The PySide GUI includes a full AI chat tab only when Ollama is installed, running, and has a local model.

Chat features:

- Chat input box
- Scrollable conversation history
- Send button
- Clear chat option
- Study question answering
- Flashcard requests from chat
- Quiz requests from chat
- Explanations based on uploaded PDF or text
- Memory-aware responses

Chat requests run in a background Qt worker thread so the GUI does not freeze while a local model is thinking.

## Memory System

The app stores learning memory locally in:

```text
study_data/study_memory.json
```

Memory can include:

- Uploaded document summaries and metadata
- Flashcard history
- Quiz result history
- Exam question history
- Chat history, only when Ollama chat is active

The memory system is defensive:

- It auto-loads on startup
- It persists between sessions
- It is used as context for local AI prompts
- If the memory file is corrupted, the app resets memory safely instead of crashing

## Fallback Safety

Every AI route follows this rule:

```text
Input -> Check Ollama status
If Ollama is active -> use local AI with memory
If Ollama is inactive or fails -> use offline fallback
Always return a result or a clear message
```

The existing offline study tools remain available even without Ollama.

## System Requirements

- Python 3.8 or higher
- Windows, macOS, or Linux
- 4 GB RAM minimum, 8 GB recommended
- Optional: Ollama for enhanced local AI and chat
- Optional: spaCy or transformer models for advanced local NLP

The default NLP engine is a fast built-in offline rules engine, so downloading a spaCy model is not required for normal use.

## Installation

### 1. Clone or Open the Project

```bash
cd Offline-AI-Study-App
```

### 2. Create a Virtual Environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Optional: Enable Ollama Local AI

Install Ollama from the official Ollama site, then run:

```bash
ollama serve
ollama pull llama3.2
```

Start the app after Ollama is running.

## Quick Start

### GUI Mode

```bash
python main.py
```

The app defaults to the PySide GUI when available. If PySide is unavailable, it attempts the CustomTkinter GUI and then falls back to CLI mode.

### CLI Mode

```bash
python main.py --cli
```

Use CLI mode for simple interactive workflows and automation.

## Project Structure

```text
Offline-AI-Study-App/
|-- main.py              # App entry point, CLI, and core orchestration
|-- gui_pyside.py        # Main PySide GUI with conditional AI chat
|-- gui_custom.py        # CustomTkinter fallback GUI
|-- gui.py               # Tkinter fallback GUI
|-- local_ai.py          # Safe Ollama detection and request routing
|-- memory_store.py      # Persistent safe local memory system
|-- nlp_engine.py        # Built-in offline NLP and optional advanced NLP hooks
|-- pdf_reader.py        # PDF/TXT/Markdown/raw text handling
|-- flashcards.py        # Flashcard generation fallback engine
|-- exam_predictor.py    # Exam question prediction fallback engine
|-- quiz_generator.py    # Quiz sessions, scoring, and weakness analysis
|-- utils.py             # Data persistence, text utilities, logging
|-- requirements.txt     # Python dependencies
|-- study_data/          # Saved outputs and memory, auto-created
|-- README.md            # Project documentation
```

## Core Modules

### `main.py`

- `StudyEngineCore`: Coordinates loading, generation, prediction, quiz creation, memory, and local AI routing
- `CLIInterface`: Interactive command-line interface
- GUI launch fallback chain

### `local_ai.py`

- Detects whether Ollama is installed and running
- Checks available local models
- Sends safe non-streaming requests to Ollama
- Parses AI-generated flashcards and exam questions
- Returns `None` or fallback-safe messages on failure

### `memory_store.py`

- Stores local learning memory as JSON
- Adds document, flashcard, quiz, exam, and chat records
- Builds compact memory context for local AI prompts
- Handles missing or corrupted memory without crashing

### `gui_pyside.py`

- Main premium GUI
- Study material input
- Flashcard editor
- Quiz panel
- Saved study item browser
- Conditional AI chat tab
- Background worker thread for local AI chat

### `nlp_engine.py`

- Fast built-in offline rules engine
- Text processing, summaries, concepts, keywords, and complexity metrics
- Optional advanced local NLP support

## Usage Examples

### Generate Flashcards From a PDF

GUI:

1. Click `Load PDF`
2. Select your PDF
3. Click `Generate Flashcards`
4. Review and edit generated cards

CLI:

```bash
python main.py --cli
```

Python:

```python
from main import StudyEngineCore

engine = StudyEngineCore()
engine.load_text("my_study_material.pdf")
deck = engine.generate_flashcards(num_cards=50)
engine.export_flashcards()
```

### Predict Exam Questions

```python
from main import StudyEngineCore

engine = StudyEngineCore()
engine.load_text("chemistry_notes.txt")
questions = engine.predict_exam_questions(num_questions=20)

high_probability = [
    question for question in questions
    if question.probability.name == "HIGH"
]
```

### Use Local AI Chat

1. Start Ollama.
2. Pull at least one model.
3. Run the app.
4. Open the `AI Chat` tab in the GUI.

Example prompts:

```text
Explain this chapter in simpler terms.
Create 10 flashcards from the uploaded material.
Make a quiz about the weakest topics from my recent results.
What exam questions are most likely from this PDF?
```

### Create a Quiz

GUI:

1. Generate flashcards or exam questions
2. Open the `Quiz` tab
3. Choose a source
4. Click `Start Quiz`
5. Answer questions and finish to save results

Python:

```python
from main import StudyEngineCore
from quiz_generator import QuizGenerator

engine = StudyEngineCore()
engine.load_text("biology_notes.txt")
deck = engine.generate_flashcards(num_cards=30)

quiz = QuizGenerator.create_from_flashcards(
    deck.cards,
    quiz_name="Biology Practice",
    num_questions=10,
)
```

## Saved Data

Saved files are stored under `study_data/`.

Examples:

- `flashcards_gui_YYYYMMDD_HHMMSS.json`
- `exam_predictions_gui_YYYYMMDD_HHMMSS.json`
- `quiz_results_gui_YYYYMMDD_HHMMSS.json`
- `study_memory.json`

The GUI hides `study_memory.json` from the saved item browser because it is internal app memory.

## Output Formats

Flashcards:

```json
{
  "timestamp": "20260621_120000",
  "type": "flashcards",
  "cards": [
    {
      "question": "Define: Photosynthesis",
      "answer": "Photosynthesis is the process by which plants convert light energy into chemical energy.",
      "tags": ["definition", "photosynthesis"],
      "difficulty": "MEDIUM",
      "source": "Original source sentence"
    }
  ]
}
```

Quiz results:

```json
{
  "timestamp": "20260621_120000",
  "type": "quiz_results",
  "quiz_name": "Flashcard Practice",
  "total_questions": 10,
  "correct": 8,
  "incorrect": 2,
  "score_percentage": 80.0,
  "duration_seconds": 300,
  "answers": []
}
```

## Troubleshooting

### Full AI Chat Is Not Available

Make sure Ollama is installed, running, and has a model:

```bash
ollama serve
ollama list
ollama pull llama3.2
```

Then restart the app.

### Ollama Is Installed But Not Detected

- Confirm `ollama` is available on your system PATH
- Confirm the server is reachable at `http://localhost:11434`
- Run `ollama list` to verify at least one local model exists

### App Works But Uses Fallback Output

This is expected when Ollama is inactive, unavailable, slow, or returns invalid JSON. The app keeps using the built-in offline generators.

### PDF Reading Fails

Install or update PyPDF2:

```bash
pip install PyPDF2
```

Some scanned PDFs contain images instead of selectable text. OCR is not currently included.

### GUI Does Not Start

Install GUI dependencies:

```bash
pip install PySide6 customtkinter
```

Or use CLI mode:

```bash
python main.py --cli
```

### Memory File Is Corrupted

The app should recover automatically. It may rename the corrupted memory file and start with fresh memory.

## Performance Tips

- Use shorter excerpts for faster local AI generation.
- Generate fewer flashcards on low-end devices.
- Pull a smaller Ollama model if chat responses are slow.
- Save useful flashcard decks instead of regenerating them repeatedly.
- Keep Ollama running before launching the app if you want chat enabled immediately.

## Design Principles

- Offline-first
- Local data ownership
- Optional local AI enhancement
- No crash on missing Ollama
- No crash on memory corruption
- Existing fallback study tools remain functional
- GUI chat is conditional, not a hard dependency

## Changelog

### Final Upgraded Version

- Added Ollama local AI detection
- Added safe AI routing with fallback
- Added persistent local memory
- Added conditional PySide GUI AI chat
- Added background chat worker to avoid GUI freezing
- Preserved existing flashcard, quiz, exam, and extraction tools

### Initial Release

- Offline study engine
- PDF/TXT/raw text input
- Flashcard generation
- Exam question prediction
- Quiz system
- Weakness analysis
- GUI and CLI interfaces

## Author

Zahoor Abbas

---

Happy studying!
