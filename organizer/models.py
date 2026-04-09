"""Data models for the note organizer."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from organizer.config import NoteCategory


@dataclass
class Note:
    """A structured note ready for Obsidian."""

    category: NoteCategory
    title: str
    content: str
    tags: list[str] = field(default_factory=list)
    key_points: list[str] = field(default_factory=list)
    related_links: list[str] = field(default_factory=list)
    source: Optional[str] = None  # URL, book name, etc.
    mood_score: Optional[int] = None  # 1-10 for mood entries
    # Stock-specific
    stock_symbol: Optional[str] = None
    stock_action: Optional[str] = None  # buy/sell/watch
    stock_price: Optional[float] = None
    stock_reasoning: Optional[str] = None
    # Fitness-specific
    exercise_type: Optional[str] = None
    duration_minutes: Optional[int] = None
    intensity: Optional[str] = None  # low/medium/high
    # Auto-generated
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Serialize to dict for JSON storage."""
        return {
            "id": self.id,
            "category": self.category.value,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "key_points": self.key_points,
            "related_links": self.related_links,
            "source": self.source,
            "mood_score": self.mood_score,
            "stock_symbol": self.stock_symbol,
            "stock_action": self.stock_action,
            "stock_price": self.stock_price,
            "stock_reasoning": self.stock_reasoning,
            "exercise_type": self.exercise_type,
            "duration_minutes": self.duration_minutes,
            "intensity": self.intensity,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Note:
        """Deserialize from dict."""
        data = data.copy()
        data["category"] = NoteCategory(data["category"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class KnowledgeEntry:
    """An entry in the knowledge base for similarity/contradiction tracking."""

    note_id: str
    category: NoteCategory
    title: str
    key_points: list[str]
    tags: list[str]
    created_at: datetime
    content_summary: str  # short summary for comparison
    # For stock notes
    stock_symbol: Optional[str] = None
    stock_action: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "note_id": self.note_id,
            "category": self.category.value,
            "title": self.title,
            "key_points": self.key_points,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "content_summary": self.content_summary,
            "stock_symbol": self.stock_symbol,
            "stock_action": self.stock_action,
        }

    @classmethod
    def from_dict(cls, data: dict) -> KnowledgeEntry:
        data = data.copy()
        data["category"] = NoteCategory(data["category"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class SimilarityResult:
    """Result from knowledge base comparison."""

    related_note_id: str
    related_title: str
    relation_type: str  # "similar" or "contradictory"
    reason: str
    related_date: datetime
    matching_keywords: list[str] = field(default_factory=list)
