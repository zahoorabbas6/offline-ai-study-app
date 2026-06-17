"""
Exam question prediction module.
Predicts likely exam questions based on study material.
"""

from typing import List, Dict, Optional
from enum import Enum
import random
from collections import Counter
from utils import Logger
from nlp_engine import NLPEngine


class QuestionType(Enum):
    """Types of exam questions."""
    MULTIPLE_CHOICE = "MCQ"
    SHORT_ANSWER = "Short Answer"
    LONG_ANSWER = "Long Answer"
    DEFINITION = "Definition"
    TRUE_FALSE = "True/False"


class ExamProbability(Enum):
    """Likelihood of question appearing on exam."""
    HIGH = 3
    MEDIUM = 2
    LOW = 1


class ExamQuestion:
    """Represents a predicted exam question."""

    def __init__(
        self,
        question: str,
        question_type: QuestionType,
        probability: ExamProbability,
        topic: str,
        reasoning: str = "",
        answer_key: Optional[str] = None,
        options: Optional[List[str]] = None,
    ):
        self.question = question
        self.question_type = question_type
        self.probability = probability
        self.topic = topic
        self.reasoning = reasoning
        self.answer_key = answer_key
        self.options = options or []

    def to_dict(self) -> Dict:
        return {
            "question": self.question,
            "type": self.question_type.value,
            "probability": self.probability.name,
            "topic": self.topic,
            "reasoning": self.reasoning,
            "answer": self.answer_key,
            "options": self.options if self.options else None,
        }

    def __repr__(self) -> str:
        return f"ExamQuestion({self.probability.name} - {self.question_type.value})"


class ExamPredictor:
    """Predicts likely exam questions from study material."""

    def __init__(self, nlp_engine: NLPEngine):
        self.nlp = nlp_engine
        self.predicted_questions = []

    def predict_questions(self, text: str, num_questions: int = 20) -> List[ExamQuestion]:
        Logger.log(f"Predicting {num_questions} exam questions...")

        doc = self.nlp.process(text)
        if not doc:
            return []

        questions = []
        questions.extend(self._generate_definition_questions(text, max(1, int(num_questions * 0.2))))
        questions.extend(self._generate_concept_questions(text, max(1, int(num_questions * 0.3))))
        questions.extend(self._generate_mcq(text, max(1, int(num_questions * 0.25))))
        questions.extend(self._generate_short_answer_questions(text, max(1, int(num_questions * 0.25))))

        final_questions = questions[:num_questions]
        Logger.log(f"Generated {len(final_questions)} predicted exam questions")

        self.predicted_questions = final_questions
        return final_questions

    def _generate_definition_questions(self, text: str, num: int) -> List[ExamQuestion]:
        questions = []
        definitions = self.nlp.extract_definitions(text)

        for term, definition in definitions[:num]:
            question = f"Define the term: {term}"
            probability = self._estimate_probability(term, text)
            questions.append(
                ExamQuestion(
                    question=question,
                    question_type=QuestionType.DEFINITION,
                    probability=probability,
                    topic=term,
                    reasoning=f"'{term}' is explicitly defined in material",
                    answer_key=definition,
                )
            )

        return questions

    def _generate_concept_questions(self, text: str, num: int) -> List[ExamQuestion]:
        questions = []
        topics = self.nlp.extract_topics(text, top_n=max(5, num * 2))

        for topic in topics[:num]:
            templates = [
                f"Explain the concept of {topic}",
                f"What is {topic}?",
                f"Discuss {topic} in detail",
                f"How does {topic} relate to the material?",
            ]
            question = random.choice(templates)
            probability = self._estimate_probability(topic, text)
            sentences = [sent.text for sent in self.nlp.process(text).sents if topic.lower() in sent.text.lower()]
            answer = sentences[0] if sentences else "See study material"

            questions.append(
                ExamQuestion(
                    question=question,
                    question_type=QuestionType.LONG_ANSWER,
                    probability=probability,
                    topic=topic,
                    reasoning=f"'{topic}' is a key concept in material",
                    answer_key=answer,
                )
            )

        return questions

    def _generate_mcq(self, text: str, num: int) -> List[ExamQuestion]:
        questions = []
        topics = self.nlp.extract_topics(text, top_n=max(5, num * 2))
        phrase_pool = [phrase for phrase in self.nlp.extract_noun_phrases(self.nlp.process(text)) if phrase]

        for topic in topics[:num]:
            question = f"Which statement best describes {topic}?"
            wrong_answers = self._generate_distractors(topic, phrase_pool, num_distractors=3)
            sentences = [sent.text for sent in self.nlp.process(text).sents if topic.lower() in sent.text.lower()]
            correct_answer = sentences[0] if sentences else f"{topic} is important"

            options = [correct_answer] + wrong_answers
            random.shuffle(options)
            probability = self._estimate_probability(topic, text)

            questions.append(
                ExamQuestion(
                    question=question,
                    question_type=QuestionType.MULTIPLE_CHOICE,
                    probability=probability,
                    topic=topic,
                    reasoning=f"'{topic}' is frequently featured in the material",
                    answer_key=correct_answer,
                    options=options,
                )
            )

        return questions

    def _generate_short_answer_questions(self, text: str, num: int) -> List[ExamQuestion]:
        questions = []
        keywords = self.nlp.extract_keywords_nlp(self.nlp.process(text), top_n=num)

        for keyword, _ in keywords[:num]:
            templates = [
                f"What is {keyword}?",
                f"Briefly explain {keyword}",
                f"Describe {keyword}",
                f"Give an example of {keyword}",
            ]
            question = random.choice(templates)
            probability = self._estimate_probability(keyword, text)
            sentences = [sent.text for sent in self.nlp.process(text).sents if keyword.lower() in sent.text.lower()]
            answer = sentences[0] if sentences else f"{keyword} is discussed in the material"

            questions.append(
                ExamQuestion(
                    question=question,
                    question_type=QuestionType.SHORT_ANSWER,
                    probability=probability,
                    topic=keyword,
                    reasoning=f"'{keyword}' is a key term",
                    answer_key=answer,
                )
            )

        return questions

    def _estimate_probability(self, term: str, text: str) -> ExamProbability:
        freq = text.lower().count(term.lower())
        position_ratio = text.lower().find(term.lower()) / max(len(text), 1)
        score = freq + 2 * (1 - position_ratio)

        if score > 8:
            return ExamProbability.HIGH
        if score > 4:
            return ExamProbability.MEDIUM
        return ExamProbability.LOW

    @staticmethod
    def _generate_distractors(topic: str, phrase_pool: List[str], num_distractors: int = 3) -> List[str]:
        candidates = [phrase for phrase in phrase_pool if topic.lower() not in phrase.lower()]
        if len(candidates) >= num_distractors:
            return random.sample(candidates, num_distractors)

        return [
            f"{topic} is related to general knowledge",
            f"{topic} has no connection to the main topic",
            f"{topic} is only relevant in specific contexts",
        ][:num_distractors]

    def rank_by_probability(self) -> List[ExamQuestion]:
        return sorted(self.predicted_questions, key=lambda q: q.probability.value, reverse=True)

    def get_high_probability_questions(self) -> List[ExamQuestion]:
        return [q for q in self.predicted_questions if q.probability == ExamProbability.HIGH]

    def get_by_type(self, question_type: QuestionType) -> List[ExamQuestion]:
        return [q for q in self.predicted_questions if q.question_type == question_type]


class ExamPaperGenerator:
    """Generates complete practice exam papers."""

    def __init__(self, predictor: ExamPredictor):
        self.predictor = predictor

    def generate_exam_paper(
        self,
        num_mcq: int = 10,
        num_short_answer: int = 5,
        num_long_answer: int = 3,
    ) -> Dict:
        mcq = self.predictor.get_by_type(QuestionType.MULTIPLE_CHOICE)[:num_mcq]
        short_ans = self.predictor.get_by_type(QuestionType.SHORT_ANSWER)[:num_short_answer]
        long_ans = self.predictor.get_by_type(QuestionType.LONG_ANSWER)[:num_long_answer]

        return {
            "title": "Practice Exam Paper",
            "total_questions": len(mcq) + len(short_ans) + len(long_ans),
            "sections": {
                "mcq": {"count": len(mcq), "questions": [q.to_dict() for q in mcq]},
                "short_answer": {"count": len(short_ans), "questions": [q.to_dict() for q in short_ans]},
                "long_answer": {"count": len(long_ans), "questions": [q.to_dict() for q in long_ans]},
            },
        }


__all__ = [
    'ExamQuestion',
    'ExamPredictor',
    'ExamPaperGenerator',
    'QuestionType',
    'ExamProbability',
]
