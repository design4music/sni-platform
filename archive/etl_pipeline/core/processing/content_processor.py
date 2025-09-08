"""
Content Processing Framework for Strategic Narrative Intelligence ETL Pipeline

This module handles content filtering, Named Entity Recognition (NER), and
multilingual processing using spaCy and HuggingFace transformers.
"""

import asyncio
import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple

import spacy
import structlog
import torch
from langdetect import DetectorFactory, detect
from transformers import (AutoModelForSequenceClassification,
                          AutoModelForTokenClassification, AutoTokenizer,
                          Pipeline, pipeline)

from ..config import ProcessingConfig
from ..database import get_db_session
from ..database.models import (Article, ContentCategory, EntityMention,
                               LanguageCode, ProcessingStatus)
from ..exceptions import ContentError, ProcessingError
from ..monitoring import MetricsCollector

logger = structlog.get_logger(__name__)

# Set seed for consistent language detection
DetectorFactory.seed = 0


@dataclass
class ProcessingResult:
    """Result of content processing operation"""

    processed_count: int
    filtered_count: int
    failed_count: int
    categories_assigned: Dict[str, int]
    entities_extracted: int
    processing_time_seconds: float
    errors: List[str]


@dataclass
class ContentAnalysis:
    """Content analysis results"""

    is_relevant: bool
    primary_category: Optional[ContentCategory]
    categories: Dict[ContentCategory, float]
    relevance_score: float
    quality_score: float
    sentiment_score: float
    language: LanguageCode
    reasons: List[str]


@dataclass
class EntityResult:
    """Named entity extraction result"""

    entity_text: str
    entity_type: str
    entity_label: str
    start_char: int
    end_char: int
    confidence_score: float
    context_snippet: str
    knowledge_base_id: Optional[str] = None


class ContentProcessor:
    """
    Handles content filtering, categorization, and NER processing
    with multilingual support and quality assessment.
    """

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.logger = structlog.get_logger(__name__)
        self.metrics_collector = MetricsCollector(config.monitoring)

        # Initialize language models
        self.spacy_models = {}
        self.hf_pipelines = {}
        self.thread_pool = ThreadPoolExecutor(max_workers=config.max_workers)

        # Content filtering patterns
        self._initialize_filtering_patterns()

        # Quality assessment thresholds
        self.min_word_count = 50
        self.max_word_count = 10000
        self.min_sentence_count = 3

        # Initialize models asynchronously
        asyncio.create_task(self._initialize_models())

    async def _initialize_models(self):
        """Initialize NLP models for different languages"""
        try:
            # Initialize spaCy models for supported languages
            spacy_models = {
                "en": "en_core_web_sm",
                "ru": "ru_core_news_sm",
                "de": "de_core_news_sm",
                "fr": "fr_core_news_sm",
            }

            for lang, model_name in spacy_models.items():
                try:
                    self.spacy_models[lang] = spacy.load(model_name)
                    self.logger.info(
                        "Loaded spaCy model", language=lang, model=model_name
                    )
                except OSError:
                    self.logger.warning(
                        "spaCy model not found", language=lang, model=model_name
                    )
                    # Fallback to English model
                    if lang != "en":
                        self.spacy_models[lang] = self.spacy_models.get("en")

            # Initialize HuggingFace pipelines
            await self._initialize_hf_pipelines()

        except Exception as exc:
            self.logger.error("Failed to initialize NLP models", error=str(exc))
            raise ProcessingError(f"Model initialization failed: {str(exc)}") from exc

    async def _initialize_hf_pipelines(self):
        """Initialize HuggingFace pipelines for classification and NER"""
        try:
            # Sentiment analysis pipeline
            self.hf_pipelines["sentiment"] = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=0 if torch.cuda.is_available() else -1,
            )

            # Content classification pipeline
            self.hf_pipelines["classification"] = pipeline(
                "text-classification",
                model="microsoft/DialoGPT-medium",  # Replace with domain-specific model
                device=0 if torch.cuda.is_available() else -1,
            )

            # Multilingual NER pipeline
            self.hf_pipelines["ner"] = pipeline(
                "ner",
                model="Davlan/bert-base-multilingual-cased-ner-hrl",
                aggregation_strategy="simple",
                device=0 if torch.cuda.is_available() else -1,
            )

            # Topic classification pipeline
            self.hf_pipelines["topic"] = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=0 if torch.cuda.is_available() else -1,
            )

            self.logger.info("HuggingFace pipelines initialized successfully")

        except Exception as exc:
            self.logger.error(
                "Failed to initialize HuggingFace pipelines", error=str(exc)
            )
            # Continue with spaCy-only processing

    def _initialize_filtering_patterns(self):
        """Initialize content filtering patterns and keywords"""

        # Relevant topic keywords by category
        self.topic_keywords = {
            ContentCategory.GEOPOLITICS: {
                "en": [
                    "diplomacy",
                    "foreign policy",
                    "international relations",
                    "treaty",
                    "alliance",
                    "sanctions",
                    "embargo",
                    "geopolitical",
                    "sovereignty",
                    "territorial",
                ],
                "ru": [
                    "дипломатия",
                    "внешняя политика",
                    "международные отношения",
                    "договор",
                    "альянс",
                    "санкции",
                    "эмбарго",
                    "геополитический",
                    "суверенитет",
                    "территориальный",
                ],
                "de": [
                    "diplomatie",
                    "außenpolitik",
                    "internationale beziehungen",
                    "vertrag",
                    "bündnis",
                    "sanktionen",
                    "embargo",
                    "geopolitisch",
                    "souveränität",
                    "territorial",
                ],
                "fr": [
                    "diplomatie",
                    "politique étrangère",
                    "relations internationales",
                    "traité",
                    "alliance",
                    "sanctions",
                    "embargo",
                    "géopolitique",
                    "souveraineté",
                    "territorial",
                ],
            },
            ContentCategory.MILITARY: {
                "en": [
                    "military",
                    "defense",
                    "armed forces",
                    "warfare",
                    "weapons",
                    "combat",
                    "strategic",
                    "tactical",
                    "deployment",
                    "operations",
                    "conflict",
                    "war",
                ],
                "ru": [
                    "военный",
                    "оборона",
                    "вооруженные силы",
                    "война",
                    "оружие",
                    "боевые действия",
                    "стратегический",
                    "тактический",
                    "развертывание",
                    "операции",
                    "конфликт",
                ],
                "de": [
                    "militär",
                    "verteidigung",
                    "streitkräfte",
                    "kriegsführung",
                    "waffen",
                    "kampf",
                    "strategisch",
                    "taktisch",
                    "einsatz",
                    "operationen",
                    "konflikt",
                    "krieg",
                ],
                "fr": [
                    "militaire",
                    "défense",
                    "forces armées",
                    "guerre",
                    "armes",
                    "combat",
                    "stratégique",
                    "tactique",
                    "déploiement",
                    "opérations",
                    "conflit",
                ],
            },
            ContentCategory.ENERGY: {
                "en": [
                    "energy",
                    "oil",
                    "gas",
                    "petroleum",
                    "renewable",
                    "nuclear",
                    "pipeline",
                    "electricity",
                    "power grid",
                    "fossil fuels",
                    "carbon",
                    "climate",
                ],
                "ru": [
                    "энергия",
                    "нефть",
                    "газ",
                    "нефтепродукты",
                    "возобновляемый",
                    "ядерный",
                    "трубопровод",
                    "электричество",
                    "энергосеть",
                    "ископаемое топливо",
                    "углерод",
                ],
                "de": [
                    "energie",
                    "öl",
                    "gas",
                    "erdöl",
                    "erneuerbar",
                    "nuklear",
                    "pipeline",
                    "elektrizität",
                    "stromnetz",
                    "fossile brennstoffe",
                    "kohlenstoff",
                    "klima",
                ],
                "fr": [
                    "énergie",
                    "pétrole",
                    "gaz",
                    "pétrole",
                    "renouvelable",
                    "nucléaire",
                    "pipeline",
                    "électricité",
                    "réseau électrique",
                    "combustibles fossiles",
                    "carbone",
                    "climat",
                ],
            },
            ContentCategory.AI_TECHNOLOGY: {
                "en": [
                    "artificial intelligence",
                    "machine learning",
                    "AI",
                    "ML",
                    "neural network",
                    "deep learning",
                    "algorithm",
                    "automation",
                    "robotics",
                    "technology",
                ],
                "ru": [
                    "искусственный интеллект",
                    "машинное обучение",
                    "ИИ",
                    "нейронная сеть",
                    "глубокое обучение",
                    "алгоритм",
                    "автоматизация",
                    "робототехника",
                    "технология",
                ],
                "de": [
                    "künstliche intelligenz",
                    "maschinelles lernen",
                    "KI",
                    "neuronales netzwerk",
                    "deep learning",
                    "algorithmus",
                    "automatisierung",
                    "robotik",
                    "technologie",
                ],
                "fr": [
                    "intelligence artificielle",
                    "apprentissage automatique",
                    "IA",
                    "réseau de neurones",
                    "apprentissage profond",
                    "algorithme",
                    "automatisation",
                    "robotique",
                    "technologie",
                ],
            },
        }

        # Irrelevant content patterns (things to filter out)
        self.irrelevant_patterns = {
            "en": [
                r"panda.*birth|birth.*panda",
                r"celebrity.*divorce|divorce.*celebrity",
                r"sports.*score|score.*sports",
                r"weather.*forecast|forecast.*weather",
                r"recipe.*cooking|cooking.*recipe",
                r"fashion.*trend|trend.*fashion",
                r"entertainment.*news|news.*entertainment",
            ],
            "ru": [
                r"панда.*рождение|рождение.*панда",
                r"знаменитость.*развод|развод.*знаменитость",
                r"спорт.*счет|счет.*спорт",
                r"погода.*прогноз|прогноз.*погода",
                r"рецепт.*кулинария|кулинария.*рецепт",
            ],
            "de": [
                r"panda.*geburt|geburt.*panda",
                r"prominente.*scheidung|scheidung.*prominente",
                r"sport.*ergebnis|ergebnis.*sport",
                r"wetter.*vorhersage|vorhersage.*wetter",
                r"rezept.*kochen|kochen.*rezept",
            ],
            "fr": [
                r"panda.*naissance|naissance.*panda",
                r"célébrité.*divorce|divorce.*célébrité",
                r"sport.*score|score.*sport",
                r"météo.*prévision|prévision.*météo",
                r"recette.*cuisine|cuisine.*recette",
            ],
        }

        # High-priority entity types for strategic intelligence
        self.priority_entity_types = {
            "PERSON",
            "ORG",
            "GPE",
            "NORP",
            "EVENT",
            "FAC",
            "LOC",
        }

    async def process_articles(self, article_ids: List[str]) -> ProcessingResult:
        """
        Process a batch of articles for content filtering and NER.

        Args:
            article_ids: List of article IDs to process

        Returns:
            ProcessingResult with processing statistics
        """
        start_time = datetime.utcnow()

        self.logger.info("Starting content processing", article_count=len(article_ids))

        processed_count = 0
        filtered_count = 0
        failed_count = 0
        categories_assigned = {}
        entities_extracted = 0
        errors = []

        # Process articles in parallel batches
        batch_size = self.config.batch_size
        for i in range(0, len(article_ids), batch_size):
            batch = article_ids[i : i + batch_size]

            batch_results = await self._process_article_batch(batch)

            for result in batch_results:
                if result["success"]:
                    processed_count += 1
                    if result.get("filtered_out", False):
                        filtered_count += 1

                    category = result.get("primary_category")
                    if category:
                        categories_assigned[category] = (
                            categories_assigned.get(category, 0) + 1
                        )

                    entities_extracted += result.get("entities_count", 0)
                else:
                    failed_count += 1
                    if result.get("error"):
                        errors.append(result["error"])

        processing_time = (datetime.utcnow() - start_time).total_seconds()

        result = ProcessingResult(
            processed_count=processed_count,
            filtered_count=filtered_count,
            failed_count=failed_count,
            categories_assigned=categories_assigned,
            entities_extracted=entities_extracted,
            processing_time_seconds=processing_time,
            errors=errors,
        )

        self.logger.info(
            "Content processing completed",
            processed=processed_count,
            filtered=filtered_count,
            failed=failed_count,
            entities=entities_extracted,
            processing_time=processing_time,
        )

        return result

    async def _process_article_batch(
        self, article_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Process a batch of articles in parallel"""
        tasks = []

        with get_db_session() as db:
            articles = db.query(Article).filter(Article.id.in_(article_ids)).all()

            for article in articles:
                task = asyncio.create_task(self._process_single_article(article))
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    {
                        "success": False,
                        "error": str(result),
                        "article_id": (
                            article_ids[i] if i < len(article_ids) else "unknown"
                        ),
                    }
                )
            else:
                processed_results.append(result)

        return processed_results

    async def _process_single_article(self, article: Article) -> Dict[str, Any]:
        """Process a single article for filtering and NER"""
        try:
            # Detect language if not set
            if not article.language or article.language == "en":
                detected_lang = await self._detect_language(
                    article.title + " " + (article.content or "")
                )
                article.language = detected_lang

            # Analyze content relevance and quality
            analysis = await self._analyze_content(article)

            # Update article with analysis results
            article.relevance_score = analysis.relevance_score
            article.quality_score = analysis.quality_score
            article.sentiment_score = analysis.sentiment_score
            article.primary_category = analysis.primary_category
            article.categories = {
                cat.value: score for cat, score in analysis.categories.items()
            }

            # Check if article should be filtered out
            if (
                not analysis.is_relevant
                or analysis.relevance_score < self.config.min_relevance_threshold
            ):
                article.filtering_status = ProcessingStatus.FILTERED_OUT
                article.processing_status = ProcessingStatus.COMPLETED
                article.processed_at = datetime.utcnow()

                return {
                    "success": True,
                    "filtered_out": True,
                    "article_id": str(article.id),
                    "reasons": analysis.reasons,
                }

            # Extract named entities
            entities = await self._extract_entities(article)
            entities_count = len(entities)

            # Store entities in database
            await self._store_entities(article.id, entities)

            # Update article status
            article.filtering_status = ProcessingStatus.COMPLETED
            article.ner_status = ProcessingStatus.COMPLETED
            article.processing_status = ProcessingStatus.COMPLETED
            article.processed_at = datetime.utcnow()

            return {
                "success": True,
                "filtered_out": False,
                "article_id": str(article.id),
                "primary_category": (
                    analysis.primary_category.value
                    if analysis.primary_category
                    else None
                ),
                "entities_count": entities_count,
                "relevance_score": analysis.relevance_score,
                "quality_score": analysis.quality_score,
            }

        except Exception as exc:
            self.logger.error(
                "Failed to process article",
                article_id=str(article.id),
                error=str(exc),
                exc_info=True,
            )

            # Update article with error status
            article.filtering_status = ProcessingStatus.FAILED
            article.processing_status = ProcessingStatus.FAILED

            return {"success": False, "article_id": str(article.id), "error": str(exc)}

    async def _detect_language(self, text: str) -> LanguageCode:
        """Detect language of text content"""
        try:
            if not text or len(text.strip()) < 20:
                return LanguageCode.EN  # Default to English

            # Use langdetect for language detection
            detected = detect(text)

            # Map to supported languages
            lang_mapping = {
                "en": LanguageCode.EN,
                "ru": LanguageCode.RU,
                "de": LanguageCode.DE,
                "fr": LanguageCode.FR,
            }

            return lang_mapping.get(detected, LanguageCode.EN)

        except Exception:
            return LanguageCode.EN  # Default fallback

    async def _analyze_content(self, article: Article) -> ContentAnalysis:
        """Analyze content for relevance, quality, and categorization"""
        try:
            content_text = (article.title + " " + (article.content or "")).strip()

            if not content_text:
                return ContentAnalysis(
                    is_relevant=False,
                    primary_category=None,
                    categories={},
                    relevance_score=0.0,
                    quality_score=0.0,
                    sentiment_score=0.0,
                    language=article.language,
                    reasons=["Empty content"],
                )

            # Check for irrelevant patterns first
            is_irrelevant, irrelevant_reasons = await self._check_irrelevant_patterns(
                content_text, article.language
            )
            if is_irrelevant:
                return ContentAnalysis(
                    is_relevant=False,
                    primary_category=None,
                    categories={},
                    relevance_score=0.0,
                    quality_score=0.0,
                    sentiment_score=0.0,
                    language=article.language,
                    reasons=irrelevant_reasons,
                )

            # Perform content analysis in parallel
            tasks = [
                self._calculate_relevance_score(content_text, article.language),
                self._calculate_quality_score(content_text),
                self._analyze_sentiment(content_text),
                self._categorize_content(content_text, article.language),
            ]

            relevance_score, quality_score, sentiment_score, categories = (
                await asyncio.gather(*tasks)
            )

            # Determine primary category
            primary_category = None
            if categories:
                primary_category = max(categories.items(), key=lambda x: x[1])[0]

            # Determine if content is relevant
            is_relevant = (
                relevance_score >= self.config.min_relevance_threshold
                and quality_score >= self.config.min_quality_threshold
                and len(categories) > 0
            )

            return ContentAnalysis(
                is_relevant=is_relevant,
                primary_category=primary_category,
                categories=categories,
                relevance_score=relevance_score,
                quality_score=quality_score,
                sentiment_score=sentiment_score,
                language=article.language,
                reasons=[],
            )

        except Exception as exc:
            self.logger.error("Content analysis failed", error=str(exc))
            return ContentAnalysis(
                is_relevant=False,
                primary_category=None,
                categories={},
                relevance_score=0.0,
                quality_score=0.0,
                sentiment_score=0.0,
                language=article.language,
                reasons=[f"Analysis error: {str(exc)}"],
            )

    async def _check_irrelevant_patterns(
        self, text: str, language: LanguageCode
    ) -> Tuple[bool, List[str]]:
        """Check if content matches irrelevant patterns"""
        text_lower = text.lower()
        lang_code = language.value
        reasons = []

        if lang_code in self.irrelevant_patterns:
            for pattern in self.irrelevant_patterns[lang_code]:
                if re.search(pattern, text_lower):
                    reasons.append(f"Matched irrelevant pattern: {pattern}")

        return len(reasons) > 0, reasons

    async def _calculate_relevance_score(
        self, text: str, language: LanguageCode
    ) -> float:
        """Calculate content relevance score based on keyword matching"""
        try:
            text_lower = text.lower()
            lang_code = language.value

            total_matches = 0
            total_keywords = 0

            # Check keywords for each category
            for category, lang_keywords in self.topic_keywords.items():
                if lang_code in lang_keywords:
                    keywords = lang_keywords[lang_code]
                    total_keywords += len(keywords)

                    for keyword in keywords:
                        if keyword.lower() in text_lower:
                            total_matches += 1

            # Calculate relevance score
            if total_keywords > 0:
                base_score = total_matches / total_keywords
            else:
                base_score = 0.0

            # Boost score for content length (longer articles often more relevant)
            word_count = len(text.split())
            length_multiplier = min(1.2, 1.0 + (word_count - 100) / 1000)

            relevance_score = min(1.0, base_score * length_multiplier)

            return relevance_score

        except Exception:
            return 0.0

    async def _calculate_quality_score(self, text: str) -> float:
        """Calculate content quality score"""
        try:
            # Basic quality metrics
            word_count = len(text.split())
            sentence_count = len([s for s in text.split(".") if s.strip()])

            # Quality indicators
            scores = []

            # Word count score
            if word_count < self.min_word_count:
                scores.append(0.3)
            elif word_count > self.max_word_count:
                scores.append(0.7)
            else:
                scores.append(1.0)

            # Sentence count score
            if sentence_count < self.min_sentence_count:
                scores.append(0.4)
            else:
                scores.append(1.0)

            # Check for quality indicators
            has_quotes = '"' in text or "'" in text
            has_sources = any(
                indicator in text.lower()
                for indicator in ["according to", "reported", "source"]
            )
            has_numbers = any(char.isdigit() for char in text)

            if has_quotes:
                scores.append(1.1)
            if has_sources:
                scores.append(1.1)
            if has_numbers:
                scores.append(1.05)

            # Check for quality detractors
            caps_ratio = sum(1 for c in text if c.isupper()) / len(text) if text else 0
            if caps_ratio > 0.1:  # Too many caps
                scores.append(0.8)

            # Calculate average score
            quality_score = min(1.0, sum(scores) / len(scores) if scores else 0.5)

            return quality_score

        except Exception:
            return 0.5  # Default middle score

    async def _analyze_sentiment(self, text: str) -> float:
        """Analyze sentiment of content"""
        try:
            if "sentiment" in self.hf_pipelines:
                # Use HuggingFace sentiment pipeline
                result = self.hf_pipelines["sentiment"](text[:512])  # Limit text length

                if result and len(result) > 0:
                    label = result[0]["label"].lower()
                    score = result[0]["score"]

                    # Convert to -1 to 1 scale
                    if "positive" in label:
                        return score
                    elif "negative" in label:
                        return -score
                    else:
                        return 0.0

            # Fallback to simple keyword-based sentiment
            positive_words = [
                "good",
                "great",
                "excellent",
                "positive",
                "success",
                "achievement",
            ]
            negative_words = [
                "bad",
                "terrible",
                "negative",
                "failure",
                "crisis",
                "problem",
            ]

            text_lower = text.lower()
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)

            total_sentiment_words = positive_count + negative_count
            if total_sentiment_words > 0:
                return (positive_count - negative_count) / total_sentiment_words

            return 0.0

        except Exception:
            return 0.0

    async def _categorize_content(
        self, text: str, language: LanguageCode
    ) -> Dict[ContentCategory, float]:
        """Categorize content into strategic intelligence categories"""
        try:
            categories = {}
            lang_code = language.value

            # Use HuggingFace zero-shot classification if available
            if "topic" in self.hf_pipelines:
                category_labels = [cat.value for cat in ContentCategory]
                result = self.hf_pipelines["topic"](text[:512], category_labels)

                for label, score in zip(result["labels"], result["scores"]):
                    try:
                        category = ContentCategory(label)
                        categories[category] = score
                    except ValueError:
                        continue

            # Fallback to keyword-based categorization
            if not categories:
                for category, lang_keywords in self.topic_keywords.items():
                    if lang_code in lang_keywords:
                        keywords = lang_keywords[lang_code]
                        text_lower = text.lower()

                        matches = sum(
                            1 for keyword in keywords if keyword.lower() in text_lower
                        )
                        if matches > 0:
                            score = min(1.0, matches / len(keywords))
                            categories[category] = score

            # Filter categories by minimum score
            filtered_categories = {
                cat: score
                for cat, score in categories.items()
                if score >= self.config.min_category_confidence
            }

            return filtered_categories

        except Exception as exc:
            self.logger.error("Content categorization failed", error=str(exc))
            return {}

    async def _extract_entities(self, article: Article) -> List[EntityResult]:
        """Extract named entities from article content"""
        try:
            text = (article.title + " " + (article.content or "")).strip()
            if not text:
                return []

            entities = []
            lang_code = article.language.value

            # Use spaCy for entity extraction
            if lang_code in self.spacy_models:
                spacy_entities = await self._extract_spacy_entities(text, lang_code)
                entities.extend(spacy_entities)

            # Use HuggingFace NER pipeline for additional entities
            if "ner" in self.hf_pipelines:
                hf_entities = await self._extract_hf_entities(text)
                entities.extend(hf_entities)

            # Deduplicate and merge entities
            entities = self._deduplicate_entities(entities)

            # Filter by priority and confidence
            filtered_entities = [
                entity
                for entity in entities
                if (
                    entity.entity_type in self.priority_entity_types
                    and entity.confidence_score >= self.config.min_entity_confidence
                )
            ]

            return filtered_entities

        except Exception as exc:
            self.logger.error(
                "Entity extraction failed", article_id=str(article.id), error=str(exc)
            )
            return []

    async def _extract_spacy_entities(
        self, text: str, lang_code: str
    ) -> List[EntityResult]:
        """Extract entities using spaCy"""
        try:
            nlp = self.spacy_models[lang_code]
            doc = nlp(text[:1000000])  # Limit text length for performance

            entities = []
            for ent in doc.ents:
                # Get context snippet
                start_context = max(0, ent.start_char - 50)
                end_context = min(len(text), ent.end_char + 50)
                context = text[start_context:end_context]

                entity = EntityResult(
                    entity_text=ent.text,
                    entity_type=ent.label_,
                    entity_label=ent.text.strip(),
                    start_char=ent.start_char,
                    end_char=ent.end_char,
                    confidence_score=0.9,  # spaCy doesn't provide confidence
                    context_snippet=context,
                )
                entities.append(entity)

            return entities

        except Exception as exc:
            self.logger.error("spaCy entity extraction failed", error=str(exc))
            return []

    async def _extract_hf_entities(self, text: str) -> List[EntityResult]:
        """Extract entities using HuggingFace NER pipeline"""
        try:
            results = self.hf_pipelines["ner"](text[:512])  # Limit text length

            entities = []
            for result in results:
                entity = EntityResult(
                    entity_text=result["word"],
                    entity_type=result["entity_group"],
                    entity_label=result["word"].strip(),
                    start_char=result["start"],
                    end_char=result["end"],
                    confidence_score=result["score"],
                    context_snippet=text[
                        max(0, result["start"] - 50) : result["end"] + 50
                    ],
                )
                entities.append(entity)

            return entities

        except Exception as exc:
            self.logger.error("HuggingFace entity extraction failed", error=str(exc))
            return []

    def _deduplicate_entities(self, entities: List[EntityResult]) -> List[EntityResult]:
        """Remove duplicate entities"""
        seen = set()
        deduplicated = []

        for entity in entities:
            # Create key for deduplication
            key = (entity.entity_text.lower(), entity.entity_type)

            if key not in seen:
                seen.add(key)
                deduplicated.append(entity)

        return deduplicated

    async def _store_entities(self, article_id: str, entities: List[EntityResult]):
        """Store extracted entities in database"""
        try:
            with get_db_session() as db:
                for entity in entities:
                    entity_mention = EntityMention(
                        article_id=article_id,
                        entity_text=entity.entity_text,
                        entity_type=entity.entity_type,
                        entity_label=entity.entity_label,
                        start_char=entity.start_char,
                        end_char=entity.end_char,
                        confidence_score=entity.confidence_score,
                        context_snippet=entity.context_snippet,
                        knowledge_base_id=entity.knowledge_base_id,
                    )
                    db.add(entity_mention)

                db.commit()

        except Exception as exc:
            self.logger.error(
                "Failed to store entities", article_id=article_id, error=str(exc)
            )
