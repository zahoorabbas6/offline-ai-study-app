"""
Quiz generation and tracking module.
Creates and manages interactive practice quizzes with scoring.
"""

from typing import List, Dict, Optional, Tuple
from enum import Enum
import random
from datetime import datetime
from utils import Logger
from flashcards import Flashcard, Difficulty
from exam_predictor import ExamQuestion, QuestionType


class QuizDifficulty(Enum):
    """Quiz difficulty levels."""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3


class QuizSession:
    """Tracks a quiz session."""

    def __init__(self, quiz_name: str, questions: List):
        """
        Initialize quiz session.
        
        Args:
            quiz_name: Name of the quiz
            questions: List of questions (Flashcard or ExamQuestion)
        """
        self.quiz_name = quiz_name
        self.questions = questions
        self.current_index = 0
        self.answers = []
        self.start_time = datetime.now()
        self.end_time = None

    def get_current_question(self):
        """Get current question."""
        if self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None

    def submit_answer(self, answer: str) -> bool:
        """
        Submit answer to current question.
        
        Args:
            answer: User's answer
            
        Returns:
            True if answer is correct
        """
        question = self.get_current_question()
        if not question:
            return False

        is_correct = self._check_answer(answer, question)
        self.answers.append({"question_index": self.current_index, "answer": answer, "correct": is_correct})

        self.current_index += 1
        return is_correct

    @staticmethod
    def _check_answer(answer: str, question) -> bool:
        """
        Check if answer is correct.
        Simple string matching.
        
        Args:
            answer: User answer
            question: Question object
            
        Returns:
            True if correct
        """
        if isinstance(question, Flashcard):
            correct = question.answer.lower()
        elif isinstance(question, ExamQuestion):
            correct = question.answer_key.lower() if question.answer_key else ""
        else:
            return False

        # Simple matching (can be enhanced with fuzzy matching)
        return answer.lower().strip() in correct

    def finish(self) -> Dict:
        """
        Finish quiz session.
        
        Returns:
            Session results
        """
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()

        correct_count = sum(1 for a in self.answers if a["correct"])
        total_count = len(self.answers)
        score_percentage = (correct_count / total_count * 100) if total_count > 0 else 0

        return {
            "quiz_name": self.quiz_name,
            "total_questions": total_count,
            "correct": correct_count,
            "incorrect": total_count - correct_count,
            "score_percentage": score_percentage,
            "duration_seconds": duration,
            "answers": self.answers,
        }

    def get_progress(self) -> Tuple[int, int]:
        """Get current progress (current, total)."""
        return self.current_index, len(self.questions)

    def __repr__(self) -> str:
        progress = self.get_progress()
        return f"QuizSession('{self.quiz_name}', {progress[0]}/{progress[1]})"


class QuizGenerator:
    """Generates practice quizzes from flashcards or exam questions."""

    @staticmethod
    def create_from_flashcards(
        flashcards: List[Flashcard],
        quiz_name: str = "Flashcard Quiz",
        num_questions: Optional[int] = None,
        shuffle: bool = True,
    ) -> QuizSession:
        """
        Create quiz from flashcards.
        
        Args:
            flashcards: List of flashcards
            quiz_name: Name of quiz
            num_questions: Number of questions to include
            shuffle: Shuffle question order
            
        Returns:
            QuizSession object
        """
        questions = flashcards.copy()

        if num_questions:
            questions = random.sample(questions, min(num_questions, len(questions)))

        if shuffle:
            random.shuffle(questions)

        Logger.log(f"Created quiz '{quiz_name}' with {len(questions)} flashcard questions")
        return QuizSession(quiz_name, questions)

    @staticmethod
    def create_from_exam_questions(
        exam_questions: List[ExamQuestion],
        quiz_name: str = "Exam Practice",
        num_questions: Optional[int] = None,
        shuffle: bool = True,
    ) -> QuizSession:
        """
        Create quiz from predicted exam questions.
        
        Args:
            exam_questions: List of exam questions
            quiz_name: Name of quiz
            num_questions: Number of questions to include
            shuffle: Shuffle question order
            
        Returns:
            QuizSession object
        """
        questions = exam_questions.copy()

        if num_questions:
            questions = random.sample(questions, min(num_questions, len(questions)))

        if shuffle:
            random.shuffle(questions)

        Logger.log(f"Created quiz '{quiz_name}' with {len(questions)} exam questions")
        return QuizSession(quiz_name, questions)

    @staticmethod
    def create_difficulty_based(
        flashcards: List[Flashcard],
        difficulty: QuizDifficulty = QuizDifficulty.INTERMEDIATE,
        num_questions: int = 10,
    ) -> QuizSession:
        """
        Create quiz with specific difficulty level.
        
        Args:
            flashcards: List of flashcards
            difficulty: Target difficulty
            num_questions: Number of questions
            
        Returns:
            QuizSession object
        """
        difficulty_map = {
            QuizDifficulty.BEGINNER: Difficulty.EASY,
            QuizDifficulty.INTERMEDIATE: Difficulty.MEDIUM,
            QuizDifficulty.ADVANCED: Difficulty.HARD,
        }

        target_difficulty = difficulty_map[difficulty]
        filtered = [card for card in flashcards if card.difficulty == target_difficulty]

        if not filtered:
            Logger.log_warning(f"No {difficulty.name} cards found, using all")
            filtered = flashcards

        questions = random.sample(filtered, min(num_questions, len(filtered)))

        quiz_name = f"{difficulty.name} Quiz"
        Logger.log(f"Created {difficulty.name} quiz with {len(questions)} questions")
        return QuizSession(quiz_name, questions)

    @staticmethod
    def create_topic_based(
        flashcards: List[Flashcard],
        topic: str,
        num_questions: Optional[int] = None,
    ) -> QuizSession:
        """
        Create quiz for specific topic.
        
        Args:
            flashcards: List of flashcards
            topic: Topic to focus on
            num_questions: Number of questions
            
        Returns:
            QuizSession object
        """
        filtered = [card for card in flashcards if topic in card.tags]

        if not filtered:
            Logger.log_warning(f"No cards found for topic: {topic}")
            return None

        if num_questions:
            questions = random.sample(filtered, min(num_questions, len(filtered)))
        else:
            questions = filtered

        quiz_name = f"Quiz: {topic}"
        Logger.log(f"Created quiz for topic '{topic}' with {len(questions)} questions")
        return QuizSession(quiz_name, questions)


class WeaknessAnalyzer:
    """Analyzes quiz performance and identifies weak areas."""

    @staticmethod
    def analyze_session(session_results: Dict) -> Dict:
        """
        Analyze quiz session results.
        
        Args:
            session_results: Results from QuizSession.finish()
            
        Returns:
            Analysis with weak areas
        """
        incorrect_count = session_results["incorrect"]
        total = session_results["total_questions"]
        score_percentage = session_results["score_percentage"]

        analysis = {
            "overall_score": score_percentage,
            "performance_level": WeaknessAnalyzer._get_performance_level(score_percentage),
            "accuracy": f"{score_percentage:.1f}%",
            "strengths": [],
            "weaknesses": [],
            "recommendations": WeaknessAnalyzer._get_recommendations(score_percentage),
        }

        return analysis

    @staticmethod
    def _get_performance_level(score_percentage: float) -> str:
        """Determine performance level."""
        if score_percentage >= 90:
            return "Excellent"
        elif score_percentage >= 75:
            return "Good"
        elif score_percentage >= 60:
            return "Fair"
        else:
            return "Needs Improvement"

    @staticmethod
    def _get_recommendations(score_percentage: float) -> List[str]:
        """Get study recommendations based on performance."""
        if score_percentage >= 90:
            return [
                "Great work! Continue reinforcing these concepts.",
                "Try advanced difficulty quizzes.",
            ]
        elif score_percentage >= 75:
            return [
                "Good progress! Review weak areas.",
                "Focus on understanding underlying concepts.",
            ]
        elif score_percentage >= 60:
            return [
                "More practice needed. Review study materials.",
                "Try topic-specific quizzes.",
            ]
        else:
            return [
                "Revisit the fundamental concepts.",
                "Focus on easier difficulty levels first.",
                "Consider re-reading core material.",
            ]

    @staticmethod
    def identify_weak_topics(sessions: List[Dict]) -> List[Tuple[str, float]]:
        """
        Identify weak topics from multiple quiz sessions.
        
        Args:
            sessions: List of session results
            
        Returns:
            List of (topic, weak_score) sorted by weakness
        """
        topic_scores = {}

        for session in sessions:
            answers = session.get("answers", [])
            for answer in answers:
                if not answer["correct"]:
                    # This would need mapping of questions to topics
                    pass

        # Simple implementation - would need question-to-topic mapping
        return []


class QuizRecommender:
    """Recommends quizzes based on learning progress."""

    @staticmethod
    def recommend_next_quiz(
        recent_sessions: List[Dict],
        available_flashcards: List[Flashcard],
    ) -> str:
        """
        Recommend next quiz based on recent performance.
        
        Args:
            recent_sessions: List of recent quiz sessions
            available_flashcards: Available flashcards
            
        Returns:
            Recommendation string
        """
        if not recent_sessions:
            return "Start with a beginner difficulty quiz to assess baseline"

        avg_score = sum(s["score_percentage"] for s in recent_sessions) / len(recent_sessions)

        if avg_score >= 85:
            return "Try advanced difficulty quizzes or focus on weak topics"
        elif avg_score >= 70:
            return "Good progress! Continue with intermediate quizzes"
        else:
            return "Spend more time reviewing materials before attempting harder quizzes"


# Export commonly used classes
__all__ = [
    'QuizSession',
    'QuizGenerator',
    'WeaknessAnalyzer',
    'QuizRecommender',
    'QuizDifficulty',
]
