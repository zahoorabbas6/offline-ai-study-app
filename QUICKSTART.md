# Quick Start Guide

## 30-Second Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download NLP model
python -m spacy download en_core_web_sm

# 3. Run the app
python main.py
```

## First Use

### GUI Mode (Recommended)
1. **Load Study Material**
   - Click "Load PDF" or "Load Text" button
   - Or use "Enter Text" menu option

2. **Generate Flashcards**
   - Click "Generate Flashcards" button
   - Review generated cards in output panel
   - Click "Export Flashcards" to save

3. **Predict Exam Questions**
   - Click "Predict Exam Questions"
   - View questions ranked by probability
   - High probability = likely to appear on exam

4. **Create & Take Quiz**
   - Generate flashcards first
   - Click "Create Quiz"
   - Answer questions interactively
   - Get instant score and recommendations

5. **Check Statistics**
   - Click "Text Statistics"
   - View complexity metrics and analysis

### CLI Mode
```bash
python main.py --cli
```
Follow on-screen prompts to:
- Load files
- Generate flashcards
- Predict exam questions
- View statistics
- Export data

## File Support

| Format | Support | Notes |
|--------|---------|-------|
| PDF | ✅ Yes | Automatic text extraction |
| TXT | ✅ Yes | Plain text files |
| Markdown | ✅ Yes | .md files |
| Direct Text | ✅ Yes | Paste/type in app |

## Features Overview

### 🎯 Flashcards
- **Automatic Generation**: Creates cards from study material
- **Multiple Types**: Definitions, concepts, Q&A
- **Difficulty Levels**: Easy, Medium, Hard
- **Export**: Save as JSON for backup

### 📝 Exam Prediction
- **Question Types**: Multiple choice, short answer, long answer, definitions
- **Probability Ranking**: HIGH, MEDIUM, LOW
- **Auto Answer Keys**: Includes correct answers
- **Complete Exams**: Generate full practice papers

### 🧪 Practice Quizzes
- **Interactive**: Real-time feedback
- **Difficulty Scaling**: Beginner to Advanced
- **Topic-Based**: Focus on specific subjects
- **Scoring**: Percentage + recommendations

### 📊 Analysis
- **Text Metrics**: Word count, complexity, readability
- **Performance Tracking**: Quiz scores and trends
- **Weakness Detection**: Identifies problem areas
- **Smart Recommendations**: Personalized study advice

## Tips for Best Results

✅ **DO:**
- Use well-structured, clear study materials
- Include definitions and key concepts
- Use technical notes or textbooks
- Generate 30-100 flashcards for optimal coverage

❌ **DON'T:**
- Use poorly scanned PDFs
- Mix multiple unrelated topics
- Generate too few cards (< 10)
- Ignore statistics and recommendations

## Common Tasks

### Create Topic-Specific Quiz
```python
from quiz_generator import QuizGenerator

quiz = QuizGenerator.create_topic_based(
    flashcards,
    topic="photosynthesis",
    num_questions=15
)
```

### Export Flashcards
**GUI**: Tools → Export Flashcards

**CLI**: Option 7 in menu

**Python**:
```python
engine.export_flashcards()
```

### Generate Advanced Quiz
**GUI**: Create Quiz → Select Difficulty (Advanced)

**Python**:
```python
from quiz_generator import QuizDifficulty, QuizGenerator

quiz = QuizGenerator.create_difficulty_based(
    cards,
    difficulty=QuizDifficulty.ADVANCED,
    num_questions=20
)
```

## Keyboard Shortcuts (GUI)

| Shortcut | Action |
|----------|--------|
| Ctrl+O | Open File |
| Ctrl+E | Export |
| Ctrl+Q | Quit |
| Tab | Next control |

## Troubleshooting Quick Fix

| Issue | Solution |
|-------|----------|
| spaCy model missing | `python -m spacy download en_core_web_sm` |
| GUI won't start | Try CLI: `python main.py --cli` |
| PDF not reading | Ensure PDF is text-based (not scanned image) |
| Out of memory | Reduce num_cards or close other apps |
| No flashcards generated | Increase input text length (min 50 chars) |

## System Requirements

- **Python**: 3.8+
- **RAM**: 4GB minimum
- **Disk**: 500MB
- **OS**: Windows, macOS, Linux

## What Gets Generated?

```
Generated Files:
├── study_data/
│   ├── flashcards_<name>_<timestamp>.json
│   └── quiz_results_<name>_<timestamp>.json
└── Console Output:
    ├── Statistics
    ├── Flashcards preview
    ├── Exam predictions
    └── Quiz scores
```

## Next Steps

1. ✅ Install & run the app
2. 📄 Load your study material
3. 🎯 Generate 50 flashcards
4. 📝 Review predicted exam questions
5. 🧪 Take a practice quiz
6. 📊 Check your performance
7. 💾 Export flashcards for later
8. 🔄 Review weak areas and repeat

## Advanced Features

- **Batch Processing**: Process multiple files
- **Custom Decks**: Mix flashcards from different sources
- **Performance Analytics**: Track progress over time
- **Spaced Repetition Ready**: Export for Anki integration
- **Concept Mapping**: Understand topic relationships

## Getting Help

1. **Check README.md** for detailed docs
2. **Review docstrings** in modules (hover/inspect)
3. **Run with sample text** to test features
4. **Check logs** for error messages
5. **Verify Python version**: `python --version`

---

**Start studying offline with AI! 🚀**

Questions? Check the main README.md file.
