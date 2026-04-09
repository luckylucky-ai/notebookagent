"""Core organizer - ties everything together."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from organizer.config import DEFAULT_DATA_PATH, DEFAULT_VAULT_PATH, NoteCategory
from organizer.knowledge_base import KnowledgeBase
from organizer.models import Note, SimilarityResult
from organizer.vault import VaultManager


@dataclass
class OrganizeResult:
    """Result of organizing a note."""

    note: Note
    file_path: Path
    similar_notes: list[SimilarityResult]
    contradictions: list[SimilarityResult]

    def summary(self) -> str:
        """Generate a human-readable summary."""
        lines = [
            f"✅ 笔记已保存: {self.file_path.name}",
            f"   分类: {self.note.category.value}",
            f"   标签: {', '.join(self.note.tags)}",
        ]

        if self.contradictions:
            lines.append("")
            lines.append("⚠️  发现与之前笔记的矛盾:")
            for c in self.contradictions:
                date_str = c.related_date.strftime("%Y-%m-%d")
                lines.append(f"   - [{date_str}] {c.related_title}")
                lines.append(f"     {c.reason}")

        if self.similar_notes:
            lines.append("")
            lines.append("💡 发现相关笔记:")
            for s in self.similar_notes:
                date_str = s.related_date.strftime("%Y-%m-%d")
                keywords = ", ".join(s.matching_keywords[:5])
                lines.append(f"   - [{date_str}] {s.related_title}")
                lines.append(f"     相关关键词: {keywords}")

        return "\n".join(lines)


class NoteOrganizer:
    """Main organizer that processes raw thoughts into structured Obsidian notes."""

    def __init__(
        self,
        vault_path: Path | None = None,
        data_path: Path | None = None,
    ):
        self.vault = VaultManager(vault_path or DEFAULT_VAULT_PATH)
        self.kb = KnowledgeBase(data_path or DEFAULT_DATA_PATH)

    def organize(
        self,
        category: NoteCategory | str,
        title: str,
        content: str,
        tags: list[str] | None = None,
        key_points: list[str] | None = None,
        related_links: list[str] | None = None,
        source: Optional[str] = None,
        mood_score: Optional[int] = None,
        stock_symbol: Optional[str] = None,
        stock_action: Optional[str] = None,
        stock_price: Optional[float] = None,
        stock_reasoning: Optional[str] = None,
        exercise_type: Optional[str] = None,
        duration_minutes: Optional[int] = None,
        intensity: Optional[str] = None,
    ) -> OrganizeResult:
        """
        Organize a raw thought into a structured Obsidian note.

        This is the main entry point. Pass in the categorized and structured
        information, and this method will:
        1. Create a Note object
        2. Check the knowledge base for similar/contradictory notes
        3. Save the note to the vault
        4. Update the knowledge base
        5. Update the MOC index
        6. Return a result with any findings
        """
        # Normalize category
        if isinstance(category, str):
            category = NoteCategory(category)

        # Create note
        note = Note(
            category=category,
            title=title,
            content=content,
            tags=tags or [],
            key_points=key_points or [],
            related_links=related_links or [],
            source=source,
            mood_score=mood_score,
            stock_symbol=stock_symbol,
            stock_action=stock_action,
            stock_price=stock_price,
            stock_reasoning=stock_reasoning,
            exercise_type=exercise_type,
            duration_minutes=duration_minutes,
            intensity=intensity,
        )

        # Check knowledge base BEFORE adding this note
        related = self.kb.find_related(note)
        similar = [r for r in related if r.relation_type == "similar"]
        contradictions = [r for r in related if r.relation_type == "contradictory"]

        # Add related note links
        for r in related[:3]:
            note.related_links.append(r.related_title)

        # Save to vault
        file_path = self.vault.save_note(note)

        # Update knowledge base
        self.kb.add(note)

        # Update MOC
        self.vault.update_moc(note.category)

        return OrganizeResult(
            note=note,
            file_path=file_path,
            similar_notes=similar,
            contradictions=contradictions,
        )

    def list_notes(self, category: NoteCategory | str | None = None) -> list[Path]:
        """List all notes, optionally filtered by category."""
        if isinstance(category, str):
            category = NoteCategory(category)
        return self.vault.list_notes(category)

    def get_stats(self) -> dict:
        """Get statistics about the knowledge base."""
        stats: dict = {
            "total_notes": len(self.kb.entries),
            "categories": {},
            "top_tags": self.kb.get_all_tags(),
        }
        for cat in NoteCategory:
            count = len(self.kb.get_entries_by_category(cat))
            if count > 0:
                stats["categories"][cat.value] = count
        return stats
