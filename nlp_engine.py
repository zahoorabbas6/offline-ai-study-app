"""
Offline-first NLP engine.
Provides robust extraction, ranking, summarization, semantic search, and analytics
without requiring network access or hosted services.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from collections import Counter, defaultdict
import math
import re

spacy = None
SPACY_AVAILABLE = None

try:
    import numpy as np
except ImportError:
    np = None

from utils import Logger, TextCleaner, TextAnalyzer


class LightweightToken:
    """Small token object used by the fast offline fallback engine."""

    def __init__(self, text: str):
        self.text = text
        self.lemma_ = text.lower()
        self.pos_ = "NOUN" if text[:1].isupper() else "X"
        self.ent_type_ = ""
        self.dep_ = ""
        self.head = self
        self.children = []
        self.is_space = not text.strip()
        self.is_punct = bool(re.fullmatch(r"\W+", text))
        self.is_alpha = text.isalpha()
        self.is_stop = text.lower() in NLPEngine.STOP_WORDS if "NLPEngine" in globals() else False


class LightweightSpan:
    """Sentence span for the fast offline fallback engine."""

    def __init__(self, text: str):
        self.text = text


class LightweightDoc:
    """Minimal spaCy-like document for deterministic offline analysis."""

    def __init__(self, text: str, stop_words: set):
        self.text = text
        self.ents = []
        self._sents = [LightweightSpan(sentence) for sentence in TextCleaner.extract_sentences(text)]
        self._tokens = []
        for raw in re.findall(r"\b[A-Za-z][A-Za-z\-']*\b|[^\w\s]", text):
            token = LightweightToken(raw)
            token.is_stop = raw.lower() in stop_words
            self._tokens.append(token)

    @property
    def sents(self):
        return self._sents

    def __iter__(self):
        return iter(self._tokens)

    def __len__(self):
        return len(self._tokens)


class NLPEngine:
    """Premium NLP engine for the study application."""

    PREMIUM_MODEL_NAME = "en_core_web_trf"
    MODEL_NAME = "en_core_web_sm"
    EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
    SUMMARIZER_MODEL = "facebook/bart-large-cnn"
    STOP_WORDS = {
        "a", "an", "and", "are", "as", "at", "be", "been", "but", "by", "can",
        "could", "did", "do", "does", "for", "from", "had", "has", "have",
        "he", "her", "his", "how", "i", "if", "in", "into", "is", "it", "its",
        "may", "might", "must", "not", "of", "on", "or", "our", "she", "should",
        "such", "than", "that", "the", "their", "there", "these", "they", "this",
        "those", "to", "was", "we", "were", "what", "when", "where", "which",
        "who", "why", "will", "with", "would", "you", "your",
    }

    def __init__(
        self,
        load_optional_models: bool = False,
        prefer_transformer_spacy: bool = False,
        use_spacy_model: bool = False,
    ):
        self.nlp = None
        self.model_name = None
        self.embedding_model = None
        self.summarizer = None
        self.load_optional_models = load_optional_models
        self.prefer_transformer_spacy = prefer_transformer_spacy
        self.use_spacy_model = use_spacy_model
        self._load_model()
        if self.load_optional_models:
            self._load_optional_models()

    def _load_model(self) -> bool:
        if not self.use_spacy_model:
            self.model_name = "fast_offline_rules"
            Logger.log("Loaded fast offline NLP engine.")
            return True

        global spacy, SPACY_AVAILABLE
        if SPACY_AVAILABLE is None:
            try:
                import spacy as spacy_module

                spacy = spacy_module
                SPACY_AVAILABLE = True
            except ImportError:
                SPACY_AVAILABLE = False

        if not SPACY_AVAILABLE:
            Logger.log_error("spaCy is not installed. Install with: pip install spacy")
            Logger.log("Then download a model with: python -m spacy download en_core_web_sm")
            return False

        model_names = [self.MODEL_NAME]
        if self.prefer_transformer_spacy:
            model_names.insert(0, self.PREMIUM_MODEL_NAME)

        for model_name in model_names:
            try:
                self.nlp = spacy.load(model_name)
                self.model_name = model_name
                Logger.log(f"Loaded spaCy model: {model_name}")
                return True
            except OSError as exc:
                Logger.log_warning(f"spaCy model '{model_name}' not found: {exc}")
            except Exception as exc:
                Logger.log_warning(f"Failed to load spaCy model '{model_name}': {exc}")

        try:
            self.nlp = spacy.blank("en")
            if "sentencizer" not in self.nlp.pipe_names:
                self.nlp.add_pipe("sentencizer")
            self.model_name = "blank_en"
            Logger.log("Loaded blank spaCy English pipeline as fallback.")
            return True
        except Exception as exc:
            Logger.log_error(f"Failed to create fallback spaCy pipeline: {exc}")
            return False

    def _load_optional_models(self) -> None:
        self.embedding_model = None
        self.summarizer = None

        try:
            from sentence_transformers import SentenceTransformer

            self.embedding_model = SentenceTransformer(
                self.EMBEDDING_MODEL_NAME,
                local_files_only=True,
            )
            Logger.log(f"Loaded embedding model: {self.EMBEDDING_MODEL_NAME}")
        except Exception as exc:
            Logger.log_warning(f"Local sentence-transformers model unavailable: {exc}")

        try:
            from transformers import pipeline

            self.summarizer = pipeline(
                "summarization",
                model=self.SUMMARIZER_MODEL,
                tokenizer=self.SUMMARIZER_MODEL,
                local_files_only=True,
            )
            Logger.log(f"Loaded summarization model: {self.SUMMARIZER_MODEL}")
        except Exception as exc:
            Logger.log_warning(f"Local summarization model unavailable: {exc}")

    def is_ready(self) -> bool:
        return self.model_name == "fast_offline_rules" or self.nlp is not None

    def process(self, text: str) -> Optional[Any]:
        if not self.is_ready():
            return None

        cleaned = TextCleaner.clean_text(text)
        if not cleaned.strip():
            return None

        try:
            if len(cleaned) > 20000:
                cleaned = cleaned[:20000]
            if self.model_name == "fast_offline_rules":
                return LightweightDoc(cleaned, self.STOP_WORDS)
            return self.nlp(cleaned)
        except Exception as exc:
            Logger.log_error(f"Error processing text: {exc}")
            return None

    def extract_entities(self, doc: Any) -> Dict[str, List[str]]:
        entities = defaultdict(list)
        for ent in getattr(doc, "ents", []):
            entities[ent.label_].append(ent.text)
        return {label: sorted(set(values), key=str.lower) for label, values in entities.items()}

    def extract_noun_phrases(self, doc: Any) -> List[str]:
        phrases = []
        try:
            for chunk in getattr(doc, "noun_chunks", []):
                phrase = self._clean_candidate(chunk.text)
                if self._is_good_phrase(phrase):
                    phrases.append(phrase)
        except Exception:
            pass

        if not phrases:
            phrases.extend(self._extract_rule_based_phrases(doc.text))

        return sorted(set(phrases), key=lambda value: (-len(value), value.lower()))

    def extract_keywords_nlp(self, doc: Any, top_n: int = 15) -> List[Tuple[str, str]]:
        keyword_scores = Counter()
        token_pos = {}

        for token in doc:
            text = token.text.lower().strip()
            if token.is_punct or token.is_space or len(text) < 3:
                continue

            lemma = token.lemma_.lower().strip() if token.lemma_ and token.lemma_ != "-PRON-" else text
            if not lemma.isalpha():
                continue
            if getattr(token, "is_stop", False) or lemma in self.STOP_WORDS:
                continue

            if token.pos_ in {"NOUN", "PROPN"}:
                score = 3.0
            elif token.pos_ == "ADJ":
                score = 2.0
            elif token.pos_ == "VERB":
                score = 1.2
            else:
                score = 0.6

            if token.ent_type_:
                score += 1.5

            keyword_scores[lemma] += score
            token_pos[lemma] = token.pos_

        if not keyword_scores:
            for word, score in self._term_scores(doc.text).most_common(top_n * 2):
                keyword_scores[word] = score
                token_pos[word] = "NOUN"

        top_keywords = keyword_scores.most_common(top_n * 2)
        keywords = []
        for lemma, _ in top_keywords:
            if len(keywords) >= top_n:
                break
            keywords.append((lemma, token_pos.get(lemma, "NOUN")))
        return keywords

    def extract_sentences(self, doc: Any) -> List[str]:
        return [sent.text.strip() for sent in getattr(doc, "sents", []) if sent.text.strip()]

    def extract_topics(self, text: str, top_n: int = 10) -> List[str]:
        doc = self.process(text)
        if not doc:
            return []

        candidates = []
        candidates.extend(self.extract_noun_phrases(doc)[: top_n * 4])
        candidates.extend([term for term, _ in self.extract_keywords_nlp(doc, top_n=top_n * 3)])
        for values in self.extract_entities(doc).values():
            candidates.extend(values)

        term_scores = self._term_scores(text)
        phrase_scores = Counter()

        for candidate in candidates:
            candidate = self._clean_candidate(candidate)
            if not self._is_good_phrase(candidate):
                continue
            tokens = self._tokenize(candidate)
            score = sum(term_scores.get(token, 0) for token in tokens)
            phrase_scores[candidate] += score + min(len(tokens), 4) * 0.35

        sorted_topics = sorted(
            phrase_scores.items(),
            key=lambda item: (item[1], len(item[0])),
            reverse=True,
        )
        unique_topics = []
        seen = set()
        for topic, _ in sorted_topics:
            key = topic.lower()
            if key in seen or any(key in existing or existing in key for existing in seen):
                continue
            seen.add(key)
            unique_topics.append(topic)
            if len(unique_topics) >= top_n:
                break

        return unique_topics

    def extract_definitions(self, text: str) -> List[Tuple[str, str]]:
        doc = self.process(text)
        if not doc:
            return []

        definitions = []
        patterns = [
            r"^(?:the\s+)?(.{2,80}?)\s+(?:is|are|refers to|means|can be defined as|is defined as)\s+(.{8,260})$",
            r"^(?:the term|called)\s+(.{2,80}?)\s+(?:is|means|refers to)\s+(.{8,260})$",
            r"^(.{2,80}?)\s*[:\-]\s*(.{8,260})$",
        ]

        for sent in getattr(doc, "sents", []):
            sent_text = sent.text.strip()
            if not sent_text:
                continue

            for pattern in patterns:
                match = re.search(pattern, sent_text, re.IGNORECASE)
                if not match:
                    continue

                term = self._clean_candidate(match.group(1))
                definition = match.group(2).rstrip('.!?').strip()
                if self._is_good_phrase(term) and len(definition.split()) >= 3:
                    definitions.append((term, definition))
                    break

        if not definitions and self.nlp is not None:
            for sent in getattr(doc, "sents", []):
                sent_doc = self.nlp(sent.text)
                root = sent_doc.root
                if root.lemma_ in {"define", "mean", "refer", "describe"}:
                    subjects = [tok.text for tok in sent_doc if tok.dep_ in {"nsubj", "nsubjpass"}]
                    objects = [tok.text for tok in sent_doc if tok.dep_ in {"dobj", "pobj", "attr"}]
                    if subjects and objects:
                        definitions.append((subjects[0], " ".join(objects)))

        return definitions

    def extract_relations(self, text: str) -> List[Tuple[str, str, str]]:
        doc = self.process(text)
        if not doc:
            return []

        relations = []
        for token in doc:
            if token.dep_ in {"nsubj", "nsubjpass"} and token.head.pos_ == "VERB":
                subject = token.text
                relation = token.head.lemma_
                obj = " ".join(child.text for child in token.head.children if child.dep_ in {"dobj", "pobj", "attr", "prep"}).strip()
                if subject and obj:
                    relations.append((subject, relation, obj))

        if not relations:
            for sent in self.extract_sentences(doc)[:40]:
                match = re.search(r"\b(.{3,60}?)\s+(causes|creates|requires|includes|contains|produces|supports|prevents|improves|reduces)\s+(.{3,100})", sent, re.IGNORECASE)
                if match:
                    relations.append(
                        (
                            self._clean_candidate(match.group(1)),
                            match.group(2).lower(),
                            self._clean_candidate(match.group(3)),
                        )
                    )

        return relations

    def rank_sentences(self, text_or_doc: Union[str, Any], top_n: int = 10) -> List[str]:
        doc = self.process(text_or_doc) if isinstance(text_or_doc, str) else text_or_doc
        if not doc:
            return []

        term_scores = self._term_scores(doc.text)
        keywords = {term for term, _ in self.extract_keywords_nlp(doc, top_n=50)}
        scored = []
        sentences = self.extract_sentences(doc)
        for index, sentence in enumerate(sentences):
            tokens = self._tokenize(sentence)
            if not tokens:
                continue
            keyword_hits = sum(1 for token in tokens if token in keywords)
            tfidf_score = sum(term_scores.get(token, 0.0) for token in tokens) / math.sqrt(len(tokens))
            position_bonus = 1.0 if index == 0 else max(0.0, 0.35 - (index / max(len(sentences), 1)))
            length_score = min(max(len(tokens), 1), 36) / 36
            score = tfidf_score + keyword_hits * 0.7 + position_bonus + length_score
            if len(tokens) <= 5:
                score *= 0.8
            scored.append((sentence.strip(), score))

        scored.sort(key=lambda item: item[1], reverse=True)
        return [text for text, _ in scored[:top_n]]

    def extract_concepts(self, text: str) -> Dict[str, List[str]]:
        doc = self.process(text)
        if not doc:
            return {}

        return {
            "entities": self.extract_entities(doc),
            "topics": self.extract_topics(text),
            "noun_phrases": self.extract_noun_phrases(doc),
            "keywords": [kw for kw, _ in self.extract_keywords_nlp(doc)],
            "definitions": self.extract_definitions(text),
            "relations": self.extract_relations(text),
            "summary": self.generate_summary(text),
            "top_sentences": self.rank_sentences(doc, top_n=5),
        }

    def generate_summary(self, text: str, sentence_count: int = 3) -> str:
        if self.summarizer is not None and len(text.split()) > 20:
            try:
                summary = self.summarizer(text[:3500], max_length=130, min_length=45, do_sample=False)
                if isinstance(summary, list) and summary and "summary_text" in summary[0]:
                    return summary[0]["summary_text"].strip()
            except Exception:
                pass

        ranked = self.rank_sentences(text, top_n=sentence_count)
        original_order = []
        for sentence in TextCleaner.extract_sentences(text):
            if sentence in ranked:
                original_order.append(sentence)
        return " ".join(original_order[:sentence_count] or ranked)

    def get_embeddings(self, texts: List[str]):
        if self.embedding_model is None:
            raise RuntimeError("Embedding model unavailable")
        return self.embedding_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)

    def semantic_search(self, query: str, texts: List[str], top_n: int = 5) -> List[Tuple[str, float]]:
        if self.embedding_model is None or np is None:
            return self._lexical_search(query, texts, top_n=top_n)

        query_vec = self.embedding_model.encode([query], convert_to_numpy=True)[0]
        candidate_embeddings = self.get_embeddings(texts)
        scores = []
        for idx, candidate in enumerate(texts):
            vector = candidate_embeddings[idx]
            score = float(np.dot(query_vec, vector) / (np.linalg.norm(query_vec) * np.linalg.norm(vector) + 1e-9))
            scores.append((candidate, score))

        scores.sort(key=lambda item: item[1], reverse=True)
        return scores[:top_n]

    def extract_key_facts(self, text: str, top_n: int = 10) -> List[str]:
        topics = self.extract_topics(text, top_n=top_n)
        definitions = self.extract_definitions(text)
        relations = self.extract_relations(text)
        facts = []
        for topic in topics[:top_n]:
            facts.append(f"Topic: {topic}")
        for term, definition in definitions[:top_n]:
            facts.append(f"Definition: {term} = {definition}")
        for subject, rel, obj in relations[:top_n]:
            facts.append(f"Relation: {subject} {rel} {obj}")
        return facts

    def analyze_text_complexity(self, text: str) -> Dict[str, float]:
        doc = self.process(text)
        if not doc:
            return {}

        stats = TextAnalyzer.get_stats(text)
        sentence_count = max(1, len(self.extract_sentences(doc)))
        words = [token.text for token in doc if token.is_alpha]
        word_count = max(1, len(words))
        syllables = sum(self._count_syllables(word) for word in words)
        readability_score = 206.835 - 1.015 * (word_count / sentence_count) - 84.6 * (syllables / word_count)
        terms = self._tokenize(text)
        top_terms = self._term_scores(text).most_common(8)

        return {
            "readability_score": readability_score,
            "avg_token_length": sum(len(token.text) for token in doc) / max(len(doc), 1),
            "complex_word_ratio": sum(1 for token in doc if len(token.text) > 7) / max(len(doc), 1),
            "unique_word_ratio": stats["unique_words"] / max(stats["word_count"], 1),
            "sentence_count": sentence_count,
            "word_count": word_count,
            "study_density": len(set(terms)) / max(sentence_count, 1),
            "key_term_count": float(len(top_terms)),
        }

    @staticmethod
    def _count_syllables(word: str) -> int:
        word = word.lower().strip()
        word = re.sub(r'[^a-z]', '', word)
        if not word:
            return 0

        vowels = "aeiouy"
        count = 0
        if word[0] in vowels:
            count += 1

        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                count += 1

        if word.endswith("e") and not word.endswith("le"):
            count = max(1, count - 1)

        return max(count, 1)

    def _term_scores(self, text: str) -> Counter:
        sentences = TextCleaner.extract_sentences(text)
        doc_count = max(len(sentences), 1)
        term_frequency = Counter()
        document_frequency = Counter()

        for sentence in sentences or [text]:
            tokens = self._tokenize(sentence)
            term_frequency.update(tokens)
            document_frequency.update(set(tokens))

        scores = Counter()
        for term, freq in term_frequency.items():
            idf = math.log((doc_count + 1) / (document_frequency[term] + 1)) + 1
            length_bonus = 1.15 if len(term) > 7 else 1.0
            scores[term] = freq * idf * length_bonus
        return scores

    def _lexical_search(self, query: str, texts: List[str], top_n: int = 5) -> List[Tuple[str, float]]:
        query_terms = set(self._tokenize(query))
        scored = []
        for text in texts:
            terms = self._tokenize(text)
            if not terms:
                scored.append((text, 0.0))
                continue
            overlap = len(query_terms.intersection(terms))
            score = overlap / math.sqrt(len(set(terms)) or 1)
            scored.append((text, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_n]

    def _extract_rule_based_phrases(self, text: str) -> List[str]:
        phrases = []
        for sentence in TextCleaner.extract_sentences(text):
            words = re.findall(r"\b[A-Za-z][A-Za-z\-']+\b", sentence)
            buffer = []
            for word in words:
                lower = word.lower()
                if lower in self.STOP_WORDS or len(lower) < 3:
                    if 1 <= len(buffer) <= 4:
                        phrases.append(" ".join(buffer))
                    buffer = []
                    continue
                buffer.append(word)
                if len(buffer) == 4:
                    phrases.append(" ".join(buffer))
                    buffer = buffer[-2:]
            if 1 <= len(buffer) <= 4:
                phrases.append(" ".join(buffer))
        return [phrase for phrase in phrases if self._is_good_phrase(phrase)]

    def _tokenize(self, text: str) -> List[str]:
        return [
            token
            for token in re.findall(r"\b[a-z][a-z\-']{2,}\b", text.lower())
            if token not in self.STOP_WORDS
        ]

    @staticmethod
    def _clean_candidate(value: str) -> str:
        value = re.sub(r"\s+", " ", value).strip(" \t\n\r:;,.!?()[]{}")
        value = re.sub(r"^(a|an|the)\s+", "", value, flags=re.IGNORECASE)
        return value.strip()

    def _is_good_phrase(self, phrase: str) -> bool:
        if not phrase or len(phrase) < 3 or len(phrase) > 90:
            return False
        tokens = self._tokenize(phrase)
        if not tokens:
            return False
        if len(tokens) > 6:
            return False
        return True


class ConceptGraphBuilder:
    """Builds concept relationships (simplified knowledge graph)."""

    @staticmethod
    def build_from_text(text: str, nlp_engine: NLPEngine) -> Dict[str, List[str]]:
        doc = nlp_engine.process(text)
        if not doc:
            return {}

        concept_graph = {}
        noun_phrases = nlp_engine.extract_noun_phrases(doc)

        for sent in doc.sents:
            sent_phrases = [phrase for phrase in noun_phrases if phrase.lower() in sent.text.lower()]
            for phrase in sent_phrases:
                if phrase not in concept_graph:
                    concept_graph[phrase] = []
                for other_phrase in sent_phrases:
                    if other_phrase != phrase and other_phrase not in concept_graph[phrase]:
                        concept_graph[phrase].append(other_phrase)

        return concept_graph


# Export commonly used classes
__all__ = [
    'NLPEngine',
    'ConceptGraphBuilder',
]
