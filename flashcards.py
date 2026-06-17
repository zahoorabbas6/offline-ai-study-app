"""
Flashcard generation module.
Converts text into study flashcards automatically.
"""

from typing import List, Dict, Optional, Tuple
from enum import Enum
from collections import Counter
from utils import Logger
from nlp_engine import NLPEngine


class Difficulty(Enum):
    """Flashcard difficulty levels."""
    EASY = 1
    MEDIUM = 2
    HARD = 3


class Flashcard:
    """Represents a single flashcard."""

    def __init__(
        self,
        question: str,
        answer: str,
        tags: List[str],
        difficulty: Difficulty = Difficulty.MEDIUM,
        source_sentence: Optional[str] = None,
    ):
        self.question = question
        self.answer = answer
        self.tags = tags
        self.difficulty = difficulty
        self.source_sentence = source_sentence

    def to_dict(self) -> Dict:
        return {
            "question": self.question,
            "answer": self.answer,
            "tags": self.tags,
            "difficulty": self.difficulty.name,
            "source": self.source_sentence,
        }

    def __repr__(self) -> str:
        return f"Flashcard(Q: {self.question[:50]}..., Tags: {self.tags})"


class FlashcardGenerator:
    """Generates flashcards from text."""

    def __init__(self, nlp_engine: NLPEngine):
        self.nlp = nlp_engine
        self.generated_cards = []

    def generate_from_definitions(self, text: str) -> List[Flashcard]:
        doc = self.nlp.process(text)
        if not doc:
            return []

        cards = []
        definitions = self.nlp.extract_definitions(text)

        for term, definition in definitions:
            question = f"Define: {term}"
            answer = definition.rstrip('.!?') + '.'
            difficulty = self._estimate_difficulty(term, definition)

            cards.append(
                Flashcard(
                    question=question,
                    answer=answer,
                    tags=["definition", term.lower()],
                    difficulty=difficulty,
                    source_sentence=definition,
                )
            )

        Logger.log(f"Generated {len(cards)} flashcards from definitions")
        return cards

    def generate_from_concepts(self, text: str, max_cards: int = 50) -> List[Flashcard]:
        doc = self.nlp.process(text)
        if not doc:
            return []

        cards = []
        topics = self.nlp.extract_topics(text, top_n=max_cards)
        definitions = dict(self.nlp.extract_definitions(text))

        for topic in topics[:max_cards]:
            topic_lower = topic.lower()
            sentences = [sent.text for sent in doc.sents if topic_lower in sent.text.lower()]
            if not sentences:
                continue

            answer = sentences[0].rstrip('.!?') + '.'
            question = f"Explain the concept of {topic}."
            difficulty = self._estimate_difficulty(topic, answer)
            tags = ["concept", topic_lower]
            if topic in definitions:
                tags.append("definition")

            cards.append(
                Flashcard(
                    question=question,
                    answer=answer,
                    tags=tags,
                    difficulty=difficulty,
                    source_sentence=answer,
                )
            )

        Logger.log(f"Generated {len(cards)} flashcards from concepts")
        return cards

    def generate_from_relations(self, text: str, max_cards: int = 20) -> List[Flashcard]:
        relations = self.nlp.extract_relations(text)
        cards = []

        for subject, action, obj in relations[:max_cards]:
            question = f"How does {subject} {action} {obj}?"
            answer = f"{subject} {action} {obj}."
            difficulty = self._estimate_difficulty(subject, answer)
            tags = ["relation", subject.lower(), obj.lower()]

            cards.append(
                Flashcard(
                    question=question,
                    answer=answer,
                    tags=tags,
                    difficulty=difficulty,
                    source_sentence=answer,
                )
            )

        Logger.log(f"Generated {len(cards)} flashcards from relations")
        return cards

    def generate_qa_from_sentences(self, text: str, max_cards: int = 30) -> List[Flashcard]:
        doc = self.nlp.process(text)
        if not doc:
            return []

        cards = []
        ranked_sentences = self.nlp.rank_sentences(doc, top_n=max_cards * 2)

        for sentence in ranked_sentences[:max_cards]:
            sent_doc = self.nlp.process(sentence)
            if not sent_doc:
                continue

            noun_phrases = self.nlp.extract_noun_phrases(sent_doc)
            subject = noun_phrases[0] if noun_phrases else sentence.split()[0]
            question = self._generate_question_from_sentence(sentence, subject)
            answer = sentence.rstrip('.!?') + '.'
            difficulty = self._estimate_difficulty(subject, sentence)

            cards.append(
                Flashcard(
                    question=question,
                    answer=answer,
                    tags=["comprehension", subject.lower()],
                    difficulty=difficulty,
                    source_sentence=sentence,
                )
            )

        Logger.log(f"Generated {len(cards)} Q&A flashcards from sentences")
        return cards

    def generate_all(self, text: str, num_cards: int = 50) -> List[Flashcard]:
        Logger.log(f"Generating {num_cards} flashcards from text...")

        cards = []
        cards.extend(self.generate_from_definitions(text)[: int(num_cards * 0.25)])
        cards.extend(self.generate_from_concepts(text, int(num_cards * 0.3)))
        cards.extend(self.generate_from_relations(text, int(num_cards * 0.2)))
        cards.extend(self.generate_qa_from_sentences(text, int(num_cards * 0.35)))

        unique_cards = self._deduplicate_cards(cards)
        final_cards = unique_cards[:num_cards]

        Logger.log(f"Generated {len(final_cards)} unique flashcards")
        self.generated_cards = final_cards
        return final_cards

    @staticmethod
    def _estimate_difficulty(term: str, context: str) -> Difficulty:
        term_length = len(term.split())
        context_length = len(context.split())

        if term_length == 1 and context_length < 12:
            return Difficulty.EASY
        if context_length > 30 or term_length > 3:
            return Difficulty.HARD
        return Difficulty.MEDIUM

    @staticmethod
    def _generate_question_from_sentence(sentence: str, subject: str) -> str:
        lower = sentence.lower()
        if "because" in lower:
            return f"Why is {subject} important?"
        if "why" in lower:
            return f"Why does {subject} matter?"
        if "how" in lower:
            return f"How does {subject} work?"
        return f"Explain the role of {subject}."

    @staticmethod
    def _deduplicate_cards(cards: List[Flashcard]) -> List[Flashcard]:
        seen = set()
        unique_cards = []
        for card in cards:
            key = card.question.lower().strip()
            if key not in seen:
                seen.add(key)
                unique_cards.append(card)
        return unique_cards


class FlashcardDeck:
    """Manages a deck of flashcards."""

    def __init__(self, name: str = "Default Deck"):
        self.name = name
        self.cards: List[Flashcard] = []
        self.study_stats = {
            "total_reviews": 0,
            "correct": 0,
            "incorrect": 0,
        }

    def add_card(self, card: Flashcard) -> None:
        self.cards.append(card)

    def add_cards(self, cards: List[Flashcard]) -> None:
        self.cards.extend(cards)

    def get_by_tag(self, tag: str) -> List[Flashcard]:
        return [card for card in self.cards if tag in card.tags]

    def get_by_difficulty(self, difficulty: Difficulty) -> List[Flashcard]:
        return [card for card in self.cards if card.difficulty == difficulty]

    def get_stats(self) -> Dict:
        return {
            "total_cards": len(self.cards),
            "easy": len(self.get_by_difficulty(Difficulty.EASY)),
            "medium": len(self.get_by_difficulty(Difficulty.MEDIUM)),
            "hard": len(self.get_by_difficulty(Difficulty.HARD)),
            "study_stats": self.study_stats,
        }

    def to_dict_list(self) -> List[Dict]:
        return [card.to_dict() for card in self.cards]

    def __len__(self) -> int:
        return len(self.cards)

    def __repr__(self) -> str:
        return f"FlashcardDeck('{self.name}', {len(self.cards)} cards)"


__all__ = [
    'Flashcard',
    'FlashcardGenerator',
    'FlashcardDeck',
    'Difficulty',
]
