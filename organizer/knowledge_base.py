"""Knowledge base for tracking notes and detecting similarities/contradictions."""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from organizer.config import (
    DEFAULT_DATA_PATH,
    KNOWLEDGE_BASE_FILE,
    NoteCategory,
)
from organizer.models import KnowledgeEntry, Note, SimilarityResult


# Stopwords for Chinese + English (common words to ignore in comparison)
_STOPWORDS = {
    "的", "了", "在", "是", "我", "有", "和", "就", "不", "人", "都", "一",
    "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着",
    "没有", "看", "好", "自己", "这", "他", "她", "它", "们", "那", "些",
    "可以", "什么", "这个", "那个", "但是", "因为", "所以", "如果", "虽然",
    "还是", "或者", "而且", "不过", "然后", "已经", "可能", "应该", "觉得",
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "about", "it", "its",
    "this", "that", "and", "but", "or", "not", "no", "so", "if", "then",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "they",
}

# Contradiction signal pairs (if both appear, might be contradictory)
_CONTRADICTION_PAIRS = [
    ({"买入", "看涨", "看好", "bullish", "buy", "加仓", "抄底"},
     {"卖出", "看跌", "看空", "bearish", "sell", "减仓", "清仓", "止损"}),
    ({"喜欢", "推荐", "好", "优秀", "赞", "棒"},
     {"不喜欢", "不推荐", "差", "烂", "失望", "坑"}),
    ({"坚持", "继续", "加油"},
     {"放弃", "停止", "算了"}),
    ({"增加", "提高", "上升", "涨"},
     {"减少", "降低", "下降", "跌"}),
]


class KnowledgeBase:
    """Stores and queries past notes for similarity and contradiction detection."""

    def __init__(self, data_path: Path | None = None):
        self.data_path = data_path or DEFAULT_DATA_PATH
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.db_file = self.data_path / KNOWLEDGE_BASE_FILE
        self.entries: list[KnowledgeEntry] = []
        self._load()

    def _load(self):
        """Load knowledge base from disk."""
        if self.db_file.exists():
            with open(self.db_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.entries = [KnowledgeEntry.from_dict(e) for e in data]
        else:
            self.entries = []

    def _save(self):
        """Persist knowledge base to disk."""
        with open(self.db_file, "w", encoding="utf-8") as f:
            json.dump(
                [e.to_dict() for e in self.entries],
                f,
                ensure_ascii=False,
                indent=2,
            )

    def add(self, note: Note):
        """Add a note to the knowledge base."""
        entry = KnowledgeEntry(
            note_id=note.id,
            category=note.category,
            title=note.title,
            key_points=note.key_points,
            tags=note.tags,
            created_at=note.created_at,
            content_summary=self._summarize(note.content),
            stock_symbol=note.stock_symbol,
            stock_action=note.stock_action,
        )
        self.entries.append(entry)
        self._save()

    def find_related(self, note: Note, top_k: int = 5) -> list[SimilarityResult]:
        """Find related notes (similar or contradictory)."""
        if not self.entries:
            return []

        results: list[SimilarityResult] = []
        note_keywords = self._extract_keywords(note)

        for entry in self.entries:
            # Don't compare with self
            if entry.note_id == note.id:
                continue

            entry_keywords = set()
            for text in [entry.title, entry.content_summary] + entry.key_points:
                entry_keywords.update(self._tokenize(text))
            entry_keywords -= _STOPWORDS

            # Calculate keyword overlap
            common = note_keywords & entry_keywords
            if not common:
                continue

            # Check for same-category relevance
            same_category = entry.category == note.category
            overlap_ratio = len(common) / min(len(note_keywords), len(entry_keywords)) if note_keywords and entry_keywords else 0

            # Check for stock-specific contradictions
            if (note.category == NoteCategory.STOCK
                    and entry.category == NoteCategory.STOCK
                    and note.stock_symbol
                    and note.stock_symbol == entry.stock_symbol):
                contradiction = self._check_stock_contradiction(note, entry)
                if contradiction:
                    results.append(contradiction)
                    continue
                # Same stock = always relevant
                if overlap_ratio < 0.15:
                    overlap_ratio = 0.15

            # Check for general contradictions
            combined_note_text = f"{note.title} {note.content} {' '.join(note.key_points)}"
            combined_entry_text = f"{entry.title} {entry.content_summary} {' '.join(entry.key_points)}"
            contradiction = self._check_contradiction(
                combined_note_text, combined_entry_text, entry, common
            )
            if contradiction:
                results.append(contradiction)
                continue

            # Similarity threshold
            threshold = 0.15 if same_category else 0.25
            if overlap_ratio >= threshold:
                results.append(SimilarityResult(
                    related_note_id=entry.note_id,
                    related_title=entry.title,
                    relation_type="similar",
                    reason=f"有 {len(common)} 个相关关键词",
                    related_date=entry.created_at,
                    matching_keywords=sorted(common)[:10],
                ))

        # Sort by number of matching keywords (desc) and return top_k
        results.sort(key=lambda r: len(r.matching_keywords), reverse=True)
        return results[:top_k]

    def get_entries_by_category(self, category: NoteCategory) -> list[KnowledgeEntry]:
        """Get all entries in a given category."""
        return [e for e in self.entries if e.category == category]

    def get_all_tags(self) -> dict[str, int]:
        """Get all tags with their frequency counts."""
        tag_counts: dict[str, int] = defaultdict(int)
        for entry in self.entries:
            for tag in entry.tags:
                tag_counts[tag] += 1
        return dict(sorted(tag_counts.items(), key=lambda x: -x[1]))

    def _extract_keywords(self, note: Note) -> set[str]:
        """Extract keywords from a note."""
        texts = [note.title, note.content] + note.key_points + note.tags
        if note.stock_reasoning:
            texts.append(note.stock_reasoning)
        keywords = set()
        for text in texts:
            keywords.update(self._tokenize(text))
        keywords -= _STOPWORDS
        return keywords

    def _tokenize(self, text: str) -> set[str]:
        """Simple tokenizer: split on whitespace/punctuation, extract Chinese bigrams."""
        if not text:
            return set()

        tokens = set()

        # English words
        english_words = re.findall(r"[a-zA-Z]+", text.lower())
        tokens.update(w for w in english_words if len(w) > 1)

        # Chinese characters - use bigrams for better matching
        chinese_chars = re.findall(r"[\u4e00-\u9fff]+", text)
        for segment in chinese_chars:
            # Single chars (for important terms)
            for char in segment:
                tokens.add(char)
            # Bigrams
            for i in range(len(segment) - 1):
                tokens.add(segment[i:i+2])
            # Trigrams for longer segments
            for i in range(len(segment) - 2):
                tokens.add(segment[i:i+3])

        # Numbers (stock prices, etc.)
        numbers = re.findall(r"\d+\.?\d*", text)
        tokens.update(numbers)

        return tokens

    def _summarize(self, content: str) -> str:
        """Create a short summary of content for storage."""
        # Take first 200 chars as summary
        clean = content.replace("\n", " ").strip()
        if len(clean) > 200:
            return clean[:200] + "..."
        return clean

    def _check_stock_contradiction(
        self, note: Note, entry: KnowledgeEntry
    ) -> SimilarityResult | None:
        """Check if stock notes contradict each other."""
        if not note.stock_action or not entry.stock_action:
            return None

        buy_actions = {"buy", "加仓", "抄底"}
        sell_actions = {"sell", "卖出", "减仓", "清仓", "止损"}

        note_is_buy = note.stock_action in buy_actions
        entry_is_buy = entry.stock_action in buy_actions
        note_is_sell = note.stock_action in sell_actions
        entry_is_sell = entry.stock_action in sell_actions

        if (note_is_buy and entry_is_sell) or (note_is_sell and entry_is_buy):
            prev_action = "买入" if entry_is_buy else "卖出"
            curr_action = "买入" if note_is_buy else "卖出"
            return SimilarityResult(
                related_note_id=entry.note_id,
                related_title=entry.title,
                relation_type="contradictory",
                reason=f"⚠️ 同一标的 {note.stock_symbol} 操作方向矛盾！"
                       f"之前是{prev_action}，现在是{curr_action}",
                related_date=entry.created_at,
                matching_keywords=[note.stock_symbol],
            )
        return None

    def _check_contradiction(
        self,
        note_text: str,
        entry_text: str,
        entry: KnowledgeEntry,
        common_keywords: set[str],
    ) -> SimilarityResult | None:
        """Check if two texts contain contradictory signals."""
        note_lower = note_text.lower()
        entry_lower = entry_text.lower()

        for positive_set, negative_set in _CONTRADICTION_PAIRS:
            note_has_positive = any(w in note_lower for w in positive_set)
            note_has_negative = any(w in note_lower for w in negative_set)
            entry_has_positive = any(w in entry_lower for w in positive_set)
            entry_has_negative = any(w in entry_lower for w in negative_set)

            if ((note_has_positive and entry_has_negative)
                    or (note_has_negative and entry_has_positive)):
                # Only flag if they share enough common ground
                if len(common_keywords) >= 3:
                    return SimilarityResult(
                        related_note_id=entry.note_id,
                        related_title=entry.title,
                        relation_type="contradictory",
                        reason=f"⚠️ 与之前的笔记观点可能矛盾，请留意前后想法的变化",
                        related_date=entry.created_at,
                        matching_keywords=sorted(common_keywords)[:10],
                    )
        return None
