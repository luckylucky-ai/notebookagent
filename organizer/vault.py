"""Vault file manager - handles reading/writing notes to the Obsidian vault."""

from __future__ import annotations

from pathlib import Path

from organizer.config import CATEGORY_CONFIG, DEFAULT_VAULT_PATH, NoteCategory
from organizer.formatter import ObsidianFormatter
from organizer.models import Note


class VaultManager:
    """Manages the Obsidian vault file structure."""

    def __init__(self, vault_path: Path | None = None):
        self.vault_path = vault_path or DEFAULT_VAULT_PATH
        self.formatter = ObsidianFormatter()
        self._ensure_structure()

    def _ensure_structure(self):
        """Ensure all category folders exist."""
        self.vault_path.mkdir(parents=True, exist_ok=True)
        for config in CATEGORY_CONFIG.values():
            (self.vault_path / config["folder"]).mkdir(exist_ok=True)
        (self.vault_path / "01-daily").mkdir(exist_ok=True)
        (self.vault_path / "09-moc").mkdir(exist_ok=True)

    def save_note(self, note: Note) -> Path:
        """Save a note to the vault and return the file path."""
        config = CATEGORY_CONFIG[note.category]
        folder = self.vault_path / config["folder"]

        # Generate filename: YYYY-MM-DD_title.md
        date_prefix = note.created_at.strftime("%Y-%m-%d")
        safe_title = self._safe_filename(note.title)
        filename = f"{date_prefix}_{safe_title}.md"
        filepath = folder / filename

        # Handle duplicates
        counter = 1
        while filepath.exists():
            filename = f"{date_prefix}_{safe_title}_{counter}.md"
            filepath = folder / filename
            counter += 1

        # Format and write
        content = self.formatter.format(note)
        filepath.write_text(content, encoding="utf-8")

        # Update daily note
        self._update_daily_note(note, filepath)

        return filepath

    def _update_daily_note(self, note: Note, note_path: Path):
        """Append entry to today's daily note."""
        date_str = note.created_at.strftime("%Y-%m-%d")
        daily_file = self.vault_path / "01-daily" / f"{date_str}.md"

        config = CATEGORY_CONFIG[note.category]
        relative_path = note_path.stem  # filename without .md for Obsidian link

        if not daily_file.exists():
            header = (
                f"---\n"
                f"date: {date_str}\n"
                f"type: daily\n"
                f"---\n\n"
                f"# 📅 {date_str} 日记\n\n"
                f"## 今日记录\n\n"
            )
            daily_file.write_text(header, encoding="utf-8")

        entry = f"- {config['icon']} [[{relative_path}|{note.title}]]\n"
        with open(daily_file, "a", encoding="utf-8") as f:
            f.write(entry)

    def update_moc(self, category: NoteCategory):
        """Update the Map of Content for a given category."""
        config = CATEGORY_CONFIG[category]
        folder = self.vault_path / config["folder"]
        moc_file = self.vault_path / "09-moc" / f"MOC-{category.value}.md"

        # Collect all notes in the category folder
        notes = sorted(folder.glob("*.md"), reverse=True)

        lines = [
            f"---",
            f"type: moc",
            f"category: {category.value}",
            f"---",
            f"",
            f"# {config['icon']} {category.value.title()} 索引",
            f"",
        ]

        for note_path in notes:
            stem = note_path.stem
            lines.append(f"- [[{stem}]]")

        lines.append("")
        moc_file.write_text("\n".join(lines), encoding="utf-8")

    def list_notes(self, category: NoteCategory | None = None) -> list[Path]:
        """List all notes, optionally filtered by category."""
        if category:
            config = CATEGORY_CONFIG[category]
            folder = self.vault_path / config["folder"]
            return sorted(folder.glob("*.md"), reverse=True)

        all_notes = []
        for config in CATEGORY_CONFIG.values():
            folder = self.vault_path / config["folder"]
            all_notes.extend(folder.glob("*.md"))
        return sorted(all_notes, reverse=True)

    def _safe_filename(self, title: str) -> str:
        """Convert title to a safe filename."""
        # Keep Chinese characters, alphanumeric, and basic punctuation
        safe = []
        for ch in title:
            if ch.isalnum() or ch in "-_ " or "\u4e00" <= ch <= "\u9fff":
                safe.append(ch)
        result = "".join(safe).strip().replace(" ", "-")
        # Truncate to reasonable length
        if len(result) > 60:
            result = result[:60]
        return result or "untitled"
