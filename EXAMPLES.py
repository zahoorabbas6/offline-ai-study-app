"""
Example usage of Offline AI Study Engine.
Demonstrates both programmatic and GUI usage.
"""

# ============================================================================
# EXAMPLE 1: Using the Study Engine Programmatically
# ============================================================================

def example_basic_usage():
    """Basic usage example."""
    from main import StudyEngineCore
    
    # Initialize engine
    engine = StudyEngineCore()
    
    # Load study material (PDF, TXT, or direct text)
    engine.load_text("biology_notes.txt")
    
    # Generate flashcards
    deck = engine.generate_flashcards(num_cards=50)
    
    # Show deck info
    print(f"Generated {len(deck)} flashcards")
    print(f"Deck stats: {deck.get_stats()}")
    
    # Export flashcards
    filename = engine.export_flashcards()
    print(f"Saved to: {filename}")


# ============================================================================
# EXAMPLE 2: Custom Flashcard Generation
# ============================================================================

def example_custom_flashcards():
    """Generate specific types of flashcards."""
    from nlp_engine import NLPEngine
    from flashcards import FlashcardGenerator
    
    # Initialize
    nlp = NLPEngine()
    generator = FlashcardGenerator(nlp)
    
    with open("study_material.txt", "r") as f:
        text = f.read()
    
    # Generate different types
    definitions = generator.generate_from_definitions(text)
    concepts = generator.generate_from_concepts(text, max_cards=30)
    qa_cards = generator.generate_qa_from_sentences(text, max_cards=20)
    
    print(f"Definitions: {len(definitions)}")
    print(f"Concepts: {len(concepts)}")
    print(f"Q&A: {len(qa_cards)}")


# ============================================================================
# EXAMPLE 3: Exam Question Prediction
# ============================================================================

def example_exam_prediction():
    """Predict exam questions with probability ranking."""
    from main import StudyEngineCore
    
    engine = StudyEngineCore()
    engine.load_text("lecture_notes.pdf")
    
    # Predict questions
    questions = engine.predict_exam_questions(num_questions=20)
    
    # Sort by probability
    from exam_predictor import ExamPredictor, ExamProbability
    high_prob = ExamPredictor(engine.nlp_engine)
    high_prob.predicted_questions = questions
    ranked = high_prob.rank_by_probability()
    
    # Display high probability questions
    for q in ranked[:5]:
        print(f"[{q.probability.name}] {q.question_type.value}")
        print(f"  Q: {q.question}")
        print(f"  Expected Answer: {q.answer_key}\n")


# ============================================================================
# EXAMPLE 4: Interactive Quiz
# ============================================================================

def example_quiz_session():
    """Create and run an interactive quiz."""
    from main import StudyEngineCore
    from quiz_generator import QuizGenerator, QuizDifficulty
    
    engine = StudyEngineCore()
    engine.load_text("physics_notes.txt")
    deck = engine.generate_flashcards(num_cards=50)
    
    # Create difficulty-based quiz
    quiz = QuizGenerator.create_difficulty_based(
        deck.cards,
        difficulty=QuizDifficulty.INTERMEDIATE,
        num_questions=10
    )
    
    # Run quiz programmatically
    print(f"Starting quiz: {quiz.quiz_name}")
    
    while quiz.current_index < len(quiz.questions):
        question = quiz.get_current_question()
        print(f"\nQuestion {quiz.current_index + 1}:")
        print(f"Q: {question.question}")
        
        # In real usage, get user input
        user_answer = input("Your answer: ")
        
        is_correct = quiz.submit_answer(user_answer)
        print(f"{'Correct!' if is_correct else 'Incorrect'}")
    
    # Get results
    results = quiz.finish()
    print(f"\n{'='*50}")
    print(f"Quiz Complete!")
    print(f"Score: {results['score_percentage']:.1f}%")
    print(f"Correct: {results['correct']}/{results['total_questions']}")
    print(f"Time: {results['duration_seconds']:.0f} seconds")


# ============================================================================
# EXAMPLE 5: Topic-Based Quiz
# ============================================================================

def example_topic_quiz():
    """Create quiz for specific topic."""
    from main import StudyEngineCore
    from quiz_generator import QuizGenerator
    
    engine = StudyEngineCore()
    engine.load_text("chemistry_notes.txt")
    deck = engine.generate_flashcards()
    
    # Create topic-specific quiz
    quiz = QuizGenerator.create_topic_based(
        deck.cards,
        topic="photosynthesis",
        num_questions=15
    )
    
    print(f"Created quiz with {len(quiz.questions)} questions on photosynthesis")


# ============================================================================
# EXAMPLE 6: Performance Analysis
# ============================================================================

def example_weakness_analysis():
    """Analyze quiz performance and get recommendations."""
    from quiz_generator import WeaknessAnalyzer
    
    # Simulated quiz results
    session_results = {
        "quiz_name": "Practice Quiz",
        "total_questions": 20,
        "correct": 14,
        "incorrect": 6,
        "score_percentage": 70.0,
        "duration_seconds": 600,
        "answers": []
    }
    
    # Analyze
    analysis = WeaknessAnalyzer.analyze_session(session_results)
    
    print(f"Performance Level: {analysis['performance_level']}")
    print(f"Accuracy: {analysis['accuracy']}")
    print(f"Recommendations:")
    for rec in analysis['recommendations']:
        print(f"  • {rec}")


# ============================================================================
# EXAMPLE 7: Text Statistics
# ============================================================================

def example_text_analysis():
    """Analyze text complexity and properties."""
    from utils import TextAnalyzer
    from nlp_engine import NLPEngine
    
    nlp = NLPEngine()
    
    with open("study_material.txt", "r") as f:
        text = f.read()
    
    # Basic statistics
    stats = TextAnalyzer.get_stats(text)
    print("Text Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Complexity analysis
    if nlp.is_ready():
        complexity = nlp.analyze_text_complexity(text)
        print("\nComplexity Metrics:")
        for key, value in complexity.items():
            print(f"  {key}: {value:.3f}")


# ============================================================================
# EXAMPLE 8: Batch Processing
# ============================================================================

def example_batch_processing():
    """Process multiple files at once."""
    from pathlib import Path
    from pdf_reader import FileReader
    from main import StudyEngineCore
    from utils import DataManager
    
    data_manager = DataManager()
    materials_dir = Path("study_materials")
    
    for file_path in materials_dir.glob("*.txt"):
        print(f"Processing {file_path.name}...")
        
        engine = StudyEngineCore()
        engine.load_text(str(file_path))
        deck = engine.generate_flashcards(num_cards=30)
        
        # Save deck
        engine.export_flashcards(f"deck_{file_path.stem}.json")
        print(f"  Generated {len(deck)} flashcards")


# ============================================================================
# EXAMPLE 9: Export and Reimport
# ============================================================================

def example_export_reimport():
    """Export flashcards and reimport for review."""
    import json
    from main import StudyEngineCore
    from flashcards import FlashcardDeck, Flashcard, Difficulty
    
    # Generate and export
    engine = StudyEngineCore()
    engine.load_text("sample_notes.txt")
    deck = engine.generate_flashcards()
    filename = engine.export_flashcards()
    
    # Reimport
    with open(f"study_data/{filename}", "r") as f:
        data = json.load(f)
    
    imported_deck = FlashcardDeck("Imported Deck")
    for card_data in data["cards"]:
        card = Flashcard(
            question=card_data["question"],
            answer=card_data["answer"],
            tags=card_data["tags"],
            difficulty=Difficulty[card_data["difficulty"]],
        )
        imported_deck.add_card(card)
    
    print(f"Reimported {len(imported_deck)} flashcards")


# ============================================================================
# EXAMPLE 10: Advanced NLP Processing
# ============================================================================

def example_advanced_nlp():
    """Advanced NLP text analysis."""
    from nlp_engine import NLPEngine, ConceptGraphBuilder
    
    nlp = NLPEngine()
    
    with open("study_material.txt", "r") as f:
        text = f.read()
    
    # Extract comprehensive concepts
    concepts = nlp.extract_concepts(text)
    print("Extracted Concepts:")
    print(f"  Entities: {len(concepts['entities'])} types")
    print(f"  Topics: {len(concepts['topics'])} main topics")
    print(f"  Keywords: {len(concepts['keywords'])} keywords")
    
    # Build concept graph
    concept_graph = ConceptGraphBuilder.build_from_text(text, nlp)
    print(f"\nConcept Relationships:")
    for concept, related in list(concept_graph.items())[:5]:
        print(f"  {concept} -> {related[:2]}")


# ============================================================================
# MAIN DEMO
# ============================================================================

if __name__ == "__main__":
    print("Offline AI Study Engine - Examples\n")
    print("Select an example to run:\n")
    
    examples = [
        ("Basic Usage", example_basic_usage),
        ("Custom Flashcards", example_custom_flashcards),
        ("Exam Prediction", example_exam_prediction),
        ("Interactive Quiz", example_quiz_session),
        ("Topic Quiz", example_topic_quiz),
        ("Weakness Analysis", example_weakness_analysis),
        ("Text Analysis", example_text_analysis),
        ("Batch Processing", example_batch_processing),
        ("Export/Reimport", example_export_reimport),
        ("Advanced NLP", example_advanced_nlp),
    ]
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"{i}. {name}")
    
    choice = input("\nSelect (1-10): ").strip()
    
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(examples):
            print(f"\n Running: {examples[idx][0]}\n")
            print("="*60)
            examples[idx][1]()
        else:
            print("Invalid choice")
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: Make sure required files exist (e.g., study_material.txt)")
