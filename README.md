# Offline AI Study Engine

A complete, production-ready offline AI study assistant that converts study materials into flashcards, predicted exam questions, practice quizzes, and weakness analysis—all running locally on your machine.

## Features

✨ **Core Features:**
- 📄 **Multi-format Input**: PDF, TXT, Markdown, or direct text entry
- 🎯 **AI Flashcard Generation**: Automatically creates study flashcards from materials
- 📝 **Exam Question Prediction**: Predicts likely exam questions with probability ranking
- 🧪 **Practice Quizzes**: Generate interactive practice quizzes with difficulty scaling
- 📊 **Weakness Analysis**: Identify weak topics and get personalized study recommendations
- 🎨 **Clean GUI**: Intuitive Tkinter interface for easy access to all features
- 📱 **CLI Interface**: Command-line interface for automation and advanced usage

## System Requirements

- **Python**: 3.8 or higher
- **RAM**: 4GB minimum (8GB+ recommended)
- **Disk Space**: 500MB for spaCy model and dependencies
- **OS**: Windows, macOS, or Linux

## Installation

### 1. Clone or Download the Project
  1.Clone the repository
  2.Install requirements 
  ```bash
pip install -r requirements```


### 2. Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download spaCy Model
```bash
python -m spacy download en_core_web_sm
```

This downloads the English NLP model (~40MB) required for text processing.

## Quick Start

### GUI Mode (Default)
```bash
python main.py
```

This launches the graphical interface with all features accessible through buttons and menus.

### CLI Interactive Mode
```bash
python main.py --cli
```

Interactive command-line interface for power users.

## Project Structure

```
offline-ai-study-engine/
├── main.py                 # Entry point with CLI & orchestration
├── gui.py                  # Tkinter GUI interface
├── nlp_engine.py          # spaCy NLP processing pipeline
├── pdf_reader.py          # PDF/TXT file handling
├── flashcards.py          # Flashcard generation engine
├── exam_predictor.py      # Exam question prediction
├── quiz_generator.py      # Quiz creation & tracking
├── utils.py               # Utility functions & helpers
├── requirements.txt       # Python dependencies
├── study_data/            # Saved flashcards & data (auto-created)
└── README.md             # This file
```

## Module Details

### 1. **utils.py** - Utilities & Helpers
- `DataManager`: JSON data persistence
- `TextCleaner`: Text normalization and cleaning
- `TextAnalyzer`: Text statistics and metrics
- `ConceptExtractor`: Basic concept extraction
- `Logger`: Timestamped logging

### 2. **pdf_reader.py** - File Input Handling
- `FileReader`: Multi-format file reading (PDF, TXT, MD)
- `TextInputHandler`: Direct text input validation
- PDF extraction using PyPDF2

### 3. **nlp_engine.py** - NLP Pipeline
- `NLPEngine`: spaCy-based text processing
  - Tokenization & sentence segmentation
  - Named Entity Recognition (NER)
  - POS tagging & lemmatization
  - Noun phrase extraction
  - Dependency parsing
- `ConceptGraphBuilder`: Builds concept relationships

### 4. **flashcards.py** - Flashcard Generation
- `Flashcard`: Individual card representation
- `FlashcardGenerator`: Multi-strategy flashcard creation
  - From explicit definitions
  - From key concepts
  - From sentence Q&A conversion
- `FlashcardDeck`: Deck management with statistics
- `Difficulty`: Easy/Medium/Hard classification

### 5. **exam_predictor.py** - Exam Question Prediction
- `ExamQuestion`: Predicted question representation
- `ExamPredictor`: Question prediction engine
  - Definition questions
  - Concept questions
  - Multiple choice questions
  - Short answer questions
  - Probability ranking
- `ExamPaperGenerator`: Complete practice exam creation

### 6. **quiz_generator.py** - Quiz Creation
- `QuizSession`: Interactive quiz tracking
  - Progress tracking
  - Answer validation
  - Session scoring
- `QuizGenerator`: Quiz creation from various sources
  - Flashcard quizzes
  - Exam question quizzes
  - Difficulty-based filtering
- `WeaknessAnalyzer`: Performance analysis
- `QuizRecommender`: Personalized study recommendations

### 7. **gui.py** - Graphical Interface
- `StudyAppGUI`: Main application window
  - File upload & text input
  - Real-time flashcard generation
  - Exam question prediction display
  - Quiz interface
  - Statistics dashboard
- `QuizUI`: Interactive quiz window

### 8. **main.py** - Orchestration & Entry Point
- `StudyEngineCore`: Core engine coordinating all modules
- `CLIInterface`: Command-line interface
- Entry point with argument parsing

## Usage Examples

### Example 1: Generate Flashcards from PDF

**GUI Method:**
1. Click "Load PDF" button
2. Select your PDF file
3. Click "Generate Flashcards"
4. Review generated cards in output panel

**CLI Method:**
```bash
python main.py --cli
# Follow prompts to load PDF and generate flashcards
```

**Python Script:**
```python
from main import StudyEngineCore

engine = StudyEngineCore()
engine.load_text("my_study_material.pdf")
deck = engine.generate_flashcards(num_cards=50)

# Export to JSON
engine.export_flashcards()
```

### Example 2: Predict Exam Questions

**GUI Method:**
1. Load study material
2. Click "Predict Exam Questions"
3. Review predictions sorted by probability

**Python Script:**
```python
from main import StudyEngineCore

engine = StudyEngineCore()
engine.load_text("chemistry_notes.txt")
questions = engine.predict_exam_questions(num_questions=20)

# High probability questions only
high_prob = [q for q in questions if q.probability.name == "HIGH"]
```

### Example 3: Create & Run a Quiz

**GUI Method:**
1. Generate flashcards (or predict exam questions)
2. Click "Create Quiz"
3. Answer questions interactively
4. View score and recommendations

**Python Script:**
```python
from main import StudyEngineCore
from quiz_generator import QuizGenerator, QuizDifficulty

engine = StudyEngineCore()
engine.load_text("biology_notes.txt")
deck = engine.generate_flashcards()

# Create intermediate difficulty quiz
quiz = QuizGenerator.create_difficulty_based(
    deck.cards,
    difficulty=QuizDifficulty.INTERMEDIATE,
    num_questions=10
)

# Run quiz programmatically
# (GUI provides interactive experience)
```

### Example 4: Analyze Text Statistics

**GUI Method:**
1. Load study material
2. Click "Text Statistics"
3. View complexity metrics

**Python Script:**
```python
from main import StudyEngineCore

engine = StudyEngineCore()
engine.load_text("lecture_notes.txt")
engine.show_statistics()
```

## Advanced Usage

### Custom Flashcard Generation

```python
from nlp_engine import NLPEngine
from flashcards import FlashcardGenerator

nlp = NLPEngine()
generator = FlashcardGenerator(nlp)

# Generate specific types
definition_cards = generator.generate_from_definitions(text)
concept_cards = generator.generate_from_concepts(text, max_cards=30)
qa_cards = generator.generate_qa_from_sentences(text, max_cards=30)
```

### Topic-Based Quiz

```python
from quiz_generator import QuizGenerator

# Create quiz for specific topic
quiz = QuizGenerator.create_topic_based(
    flashcards,
    topic="photosynthesis",
    num_questions=15
)
```

### Performance Analysis

```python
from quiz_generator import WeaknessAnalyzer

# Analyze quiz session
results = quiz_session.finish()
analysis = WeaknessAnalyzer.analyze_session(results)
print(f"Performance: {analysis['performance_level']}")
print(f"Recommendations: {analysis['recommendations']}")
```

## Configuration

### NLP Model
Edit `nlp_engine.py` to change the spaCy model:
```python
MODEL_NAME = "en_core_web_sm"  # or "en_core_web_md", "en_core_web_lg"
```

### Data Storage Location
Edit `utils.py` to change where data is saved:
```python
def __init__(self, data_dir: str = "study_data"):
    # Change "study_data" to your preferred directory
```

### Flashcard Generation Parameters
```python
# In main.py or FlashcardGenerator
num_cards = 50  # Total flashcards to generate
```

## Output Formats

### Exported Flashcards (JSON)
```json
{
  "timestamp": "2024-06-16 10:30:45",
  "cards": [
    {
      "question": "Define: Photosynthesis",
      "answer": "The process by which plants...",
      "tags": ["definition", "photosynthesis"],
      "difficulty": "MEDIUM",
      "source": "Original sentence from text"
    }
  ]
}
```

### Quiz Results
```json
{
  "quiz_name": "Study Quiz",
  "total_questions": 10,
  "correct": 8,
  "incorrect": 2,
  "score_percentage": 80.0,
  "duration_seconds": 300,
  "answers": [...]
}
```

## Troubleshooting

### spaCy Model Not Found
```bash
python -m spacy download en_core_web_sm
```

### PyPDF2 Not Installed
```bash
pip install PyPDF2
```

### GUI Not Starting
- Ensure tkinter is installed: `pip install tk`
- Try CLI mode: `python main.py --cli`

### Memory Issues on Low-End Devices
- Generate fewer flashcards: `num_cards=25`
- Use smaller spaCy model
- Close other applications

### Poor Flashcard Quality
- Use longer, more detailed source material
- Ensure text is properly formatted
- Try different sections of material

## Performance Tips

1. **Optimal RAM Usage**: 4-8GB sufficient for most tasks
2. **Processing Speed**: 
   - Text: ~100k words processed in 10-30 seconds
   - Flashcard generation: ~2-5 seconds per 50 cards
3. **Storage**: Save frequently used decks to avoid regeneration
4. **Batch Processing**: Generate multiple flashcard sets before creating quizzes

## Limitations & Future Enhancements

### Current Limitations
- English language only
- No internet connection required (fully offline)
- Flashcards based on text extraction (no hallucinations)
- Simple answer matching for quizzes

### Future Enhancements
- Multi-language support
- Advanced fuzzy matching for quiz answers
- Spaced repetition algorithm
- ML-based difficulty estimation
- Concept clustering visualization
- Export to Anki format
- Mobile companion app

## Contributing

This is a production-ready standalone application. For improvements:
1. Test thoroughly before modifying core modules
2. Maintain the modular architecture
3. Keep all features offline
4. Add type hints to new code
5. Include comprehensive docstrings

## License

Open source project - use freely for personal/educational purposes.

## Credits

Built with:
- **spaCy**: Advanced NLP
- **PyPDF2**: PDF processing
- **Tkinter**: GUI framework
- **Python 3.8+**

## Contact & Support

For issues or questions:
1. Check the troubleshooting section
2. Review module docstrings
3. Test with sample text files first

## Changelog

### Version 1.0 (Initial Release)
- Complete offline AI study engine
- 8 core modules fully integrated
- GUI and CLI interfaces
- Flashcard generation
- Exam question prediction
- Quiz system with scoring
- Weakness analysis
- Production-ready code

### Author
**Zahoor Abbas**
---

**Happy studying! 📚✨**
