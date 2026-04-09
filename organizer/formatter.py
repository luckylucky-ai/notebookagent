"""Obsidian markdown formatter - generates well-structured notes."""

from organizer.config import NoteCategory, CATEGORY_CONFIG
from organizer.models import Note


class ObsidianFormatter:
    """Formats Note objects into Obsidian-compatible markdown."""

    def format(self, note: Note) -> str:
        """Format a note into full Obsidian markdown with frontmatter."""
        parts = [
            self._frontmatter(note),
            "",
            self._heading(note),
            "",
            self._body(note),
        ]

        links_section = self._links_section(note)
        if links_section:
            parts.extend(["", links_section])

        parts.extend(["", self._footer(note)])

        return "\n".join(parts) + "\n"

    def _frontmatter(self, note: Note) -> str:
        """Generate YAML frontmatter."""
        config = CATEGORY_CONFIG[note.category]
        all_tags = list(dict.fromkeys(config["default_tags"] + note.tags))

        lines = [
            "---",
            f"id: {note.id}",
            f"category: {note.category.value}",
            f"created: {note.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"tags: [{', '.join(all_tags)}]",
        ]

        if note.source:
            lines.append(f"source: \"{note.source}\"")
        if note.mood_score is not None:
            lines.append(f"mood_score: {note.mood_score}")
        if note.stock_symbol:
            lines.append(f"stock_symbol: {note.stock_symbol}")
            if note.stock_action:
                lines.append(f"stock_action: {note.stock_action}")
            if note.stock_price is not None:
                lines.append(f"stock_price: {note.stock_price}")
        if note.exercise_type:
            lines.append(f"exercise_type: {note.exercise_type}")
            if note.duration_minutes:
                lines.append(f"duration_minutes: {note.duration_minutes}")
            if note.intensity:
                lines.append(f"intensity: {note.intensity}")

        lines.append("---")
        return "\n".join(lines)

    def _heading(self, note: Note) -> str:
        """Generate the main heading."""
        config = CATEGORY_CONFIG[note.category]
        return f"# {config['icon']} {note.title}"

    def _body(self, note: Note) -> str:
        """Generate the body content based on category."""
        formatter_map = {
            NoteCategory.STOCK: self._stock_body,
            NoteCategory.FITNESS: self._fitness_body,
            NoteCategory.VIDEO: self._video_body,
            NoteCategory.MOOD: self._mood_body,
        }
        formatter = formatter_map.get(note.category, self._default_body)
        return formatter(note)

    def _default_body(self, note: Note) -> str:
        """Default body format."""
        sections = [note.content]

        if note.key_points:
            sections.append("")
            sections.append("## 要点")
            for point in note.key_points:
                sections.append(f"- {point}")

        return "\n".join(sections)

    def _stock_body(self, note: Note) -> str:
        """Stock operation body."""
        lines = []

        if note.stock_symbol:
            lines.append("## 操作概要")
            lines.append("")
            lines.append(f"| 项目 | 内容 |")
            lines.append(f"|------|------|")
            lines.append(f"| 标的 | **{note.stock_symbol}** |")
            if note.stock_action:
                action_map = {"buy": "买入 🟢", "sell": "卖出 🔴", "watch": "观望 👀"}
                lines.append(f"| 操作 | {action_map.get(note.stock_action, note.stock_action)} |")
            if note.stock_price is not None:
                lines.append(f"| 价格 | {note.stock_price} |")
            lines.append("")

        if note.stock_reasoning:
            lines.append("## 操作逻辑")
            lines.append("")
            lines.append(note.stock_reasoning)
            lines.append("")

        lines.append("## 记录")
        lines.append("")
        lines.append(note.content)

        if note.key_points:
            lines.append("")
            lines.append("## 复盘要点")
            for point in note.key_points:
                lines.append(f"- {point}")

        return "\n".join(lines)

    def _fitness_body(self, note: Note) -> str:
        """Fitness record body."""
        lines = []

        if note.exercise_type:
            lines.append("## 训练概要")
            lines.append("")
            lines.append(f"| 项目 | 内容 |")
            lines.append(f"|------|------|")
            lines.append(f"| 类型 | **{note.exercise_type}** |")
            if note.duration_minutes:
                lines.append(f"| 时长 | {note.duration_minutes} 分钟 |")
            if note.intensity:
                intensity_map = {"low": "低强度 🟢", "medium": "中等强度 🟡", "high": "高强度 🔴"}
                lines.append(f"| 强度 | {intensity_map.get(note.intensity, note.intensity)} |")
            lines.append("")

        lines.append("## 训练详情")
        lines.append("")
        lines.append(note.content)

        if note.key_points:
            lines.append("")
            lines.append("## 训练心得")
            for point in note.key_points:
                lines.append(f"- {point}")

        return "\n".join(lines)

    def _video_body(self, note: Note) -> str:
        """Video bookmark body."""
        lines = []

        if note.source:
            lines.append(f"> 🔗 链接: {note.source}")
            lines.append("")

        lines.append("## 简介")
        lines.append("")
        lines.append(note.content)

        if note.key_points:
            lines.append("")
            lines.append("## 要点 & 收获")
            for point in note.key_points:
                lines.append(f"- {point}")

        return "\n".join(lines)

    def _mood_body(self, note: Note) -> str:
        """Mood journal body."""
        lines = []

        if note.mood_score is not None:
            bar = "█" * note.mood_score + "░" * (10 - note.mood_score)
            lines.append(f"> 心情指数: {bar} {note.mood_score}/10")
            lines.append("")

        lines.append(note.content)

        if note.key_points:
            lines.append("")
            lines.append("## 反思")
            for point in note.key_points:
                lines.append(f"- {point}")

        return "\n".join(lines)

    def _links_section(self, note: Note) -> str:
        """Generate related links section."""
        if not note.related_links:
            return ""

        lines = ["## 相关笔记", ""]
        for link in note.related_links:
            lines.append(f"- [[{link}]]")
        return "\n".join(lines)

    def _footer(self, note: Note) -> str:
        """Generate footer with metadata."""
        date_str = note.created_at.strftime("%Y-%m-%d")
        config = CATEGORY_CONFIG[note.category]
        tags_str = " ".join(f"#{t}" for t in config["default_tags"] + note.tags)
        return f"---\n*记录于 {date_str}* | {tags_str}"
