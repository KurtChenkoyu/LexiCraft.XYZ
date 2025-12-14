"""
Learning Point Pydantic Models

Data models for LearningPoint nodes in Neo4j.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class LearningPoint(BaseModel):
    """Learning Point node model."""
    
    id: str = Field(..., description="Unique identifier (e.g., 'beat_around_the_bush')")
    word: str = Field(..., description="The word/phrase itself")
    type: str = Field(..., description="'word', 'phrase', 'idiom', 'prefix', 'suffix'")
    tier: int = Field(..., ge=1, le=7, description="Earning tier (1-7)")
    definition: str = Field(..., description="Primary definition")
    example: str = Field(..., description="Usage example")
    frequency_rank: int = Field(..., ge=1, description="Corpus frequency rank")
    difficulty: str = Field(..., description="'A1', 'A2', 'B1', 'B2', 'C1', 'C2'")
    register: str = Field(..., description="'formal', 'informal', 'both'")
    contexts: List[str] = Field(default_factory=list, description="Context tags like ['financial', 'geographic', 'idiomatic']")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional data (pronunciation, synonyms, etc.)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "beat_around_the_bush",
                "word": "beat around the bush",
                "type": "idiom",
                "tier": 4,
                "definition": "To avoid talking about something directly",
                "example": "Stop beating around the bush and tell me what happened.",
                "frequency_rank": 1250,
                "difficulty": "B2",
                "register": "informal",
                "contexts": ["idiomatic", "conversational"],
                "metadata": {
                    "pronunciation": "/biːt əˈraʊnd ðə bʊʃ/",
                    "synonyms": ["avoid the issue", "prevaricate"]
                }
            }
        }


class RelationshipType:
    """Relationship type constants."""
    PREREQUISITE_OF = "PREREQUISITE_OF"
    COLLOCATES_WITH = "COLLOCATES_WITH"
    RELATED_TO = "RELATED_TO"
    PART_OF = "PART_OF"
    OPPOSITE_OF = "OPPOSITE_OF"
    MORPHOLOGICAL = "MORPHOLOGICAL"
    REGISTER_VARIANT = "REGISTER_VARIANT"
    FREQUENCY_RANK = "FREQUENCY_RANK"


class Relationship(BaseModel):
    """Relationship model between LearningPoints."""
    
    source_id: str = Field(..., description="Source learning point ID")
    target_id: str = Field(..., description="Target learning point ID")
    relationship_type: str = Field(..., description="Type of relationship")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional relationship properties")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_id": "beat",
                "target_id": "beat_around_the_bush",
                "relationship_type": "PREREQUISITE_OF",
                "properties": {}
            }
        }

# NEW: Validation Engine Models (V6.1)

class VerificationQ(BaseModel):
    """
    A Multiple Choice Question to verify understanding.
    """
    question: str = Field(description="The question text (e.g., 'Which sentence uses the word correctly?')")
    options: List[str] = Field(description="List of 4 options (1 correct, 3 distractors)")
    answer: int = Field(description="Index of the correct answer (0-3)")
    explanation: Optional[str] = Field(description="Brief explanation of why the answer is correct")

class EnrichedSense(BaseModel):
    """
    Enriched data for a specific sense.
    """
    sense_id: str
    definition_en: str = Field(description="Simplified English definition (B1/B2 level)")
    definition_zh_translation: str = Field(description="Literal, word-for-word translation of definition (helps learners see English structure)")
    definition_zh_explanation: str = Field(description="Natural Chinese explanation that identifies what the definition really means, especially nuances that might be missed")
    example_en: str = Field(description="Modern, natural English example sentence")
    example_zh_translation: str = Field(description="Literal, word-for-word translation (shows how English constructs meaning)")
    example_zh_explanation: str = Field(description="Natural Chinese explanation that identifies what the sentence really means, especially nuances, cultural context, and implied meanings that might be easily missed when going from English to Chinese")
    
    # NEW: Validation Engine Assets
    quiz: VerificationQ = Field(description="A challenging MCQ to verify this specific sense")
    mapped_phrases: List[str] = Field(default_factory=list, description="List of phrases from the skeleton that map to this sense")

class EnrichmentBatch(BaseModel):
    senses: List[EnrichedSense]

# Stage 2: Multi-Layer Example Models

class ExamplePair(BaseModel):
    """A single example sentence pair (English + Chinese)."""
    example_en: str = Field(description="English example sentence")
    example_zh_translation: str = Field(description="Literal, word-for-word translation (shows how English constructs meaning)")
    example_zh_explanation: str = Field(description="Natural Chinese explanation that identifies what the sentence really means, especially nuances, cultural context, and implied meanings that might be easily missed when going from English to Chinese")
    context_label: Optional[str] = Field(
        default=None, 
        description="Context tag: 'formal', 'casual', 'written', 'spoken', etc."
    )
    relationship_word: Optional[str] = Field(
        default=None,
        description="The related word used in this example (for Layers 2-4)"
    )
    relationship_type: Optional[str] = Field(
        default=None,
        description="'opposite', 'similar', 'confused' (for Layers 2-4)"
    )

class MultiLayerExamples(BaseModel):
    """Stage 2: Multi-layer example enrichment for a sense (Enhanced for MCQ efficacy)."""
    sense_id: str
    
    # Layer 1: Contextual Support (tiered by usage: 15-20 primary, 10 common, 5-8 rare)
    examples_contextual: List[ExamplePair] = Field(
        min_items=2,
        max_items=25,  # Allow up to 25 examples (primary senses get 15-20)
        description="Multiple examples that clearly illustrate this sense (one MEANING MCQ per example)"
    )
    
    # Layer 2: Opposites (2-3 per relationship from OPPOSITE_TO)
    examples_opposite: List[ExamplePair] = Field(
        default_factory=list,
        max_items=15,  # Allow 2-3 examples × up to 5 relationships
        description="Examples using antonyms to contrast meaning (2-3 per relationship)"
    )
    
    # Layer 3: Similar (2-3 per relationship from RELATED_TO)
    examples_similar: List[ExamplePair] = Field(
        default_factory=list,
        max_items=15,  # Allow 2-3 examples × up to 5 relationships
        description="Examples using synonyms to show subtle differences (2-3 per relationship)"
    )
    
    # Layer 4: Confused (2-3 per relationship from CONFUSED_WITH)
    examples_confused: List[ExamplePair] = Field(
        default_factory=list,
        max_items=15,  # Allow 2-3 examples × up to 5 relationships
        description="Examples showing commonly confused words in context (2-3 per relationship)"
    )
