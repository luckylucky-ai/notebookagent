"""Configuration and category definitions for the Obsidian note organizer."""

from enum import Enum
from pathlib import Path


class NoteCategory(str, Enum):
    """Note categories for organizing thoughts."""

    INSPIRATION = "inspiration"       # 灵感
    BOOK = "book"                     # 读书笔记/感悟
    MOOD = "mood"                     # 心情日记
    STOCK = "stock"                   # 股票操作
    VIDEO = "video"                   # 视频链接/推荐
    SCHEDULE = "schedule"             # 行程安排
    FITNESS = "fitness"               # 健身记录
    LEARNING = "learning"             # 学习笔记
    GENERAL = "general"               # 其他碎碎念


# Each category's folder, icon, and default tags
CATEGORY_CONFIG = {
    NoteCategory.INSPIRATION: {
        "folder": "02-inspirations",
        "icon": "💡",
        "default_tags": ["灵感", "idea"],
        "template": "inspiration",
    },
    NoteCategory.BOOK: {
        "folder": "03-books",
        "icon": "📚",
        "default_tags": ["读书", "book"],
        "template": "book",
    },
    NoteCategory.MOOD: {
        "folder": "04-mood",
        "icon": "🌊",
        "default_tags": ["心情", "mood"],
        "template": "mood",
    },
    NoteCategory.STOCK: {
        "folder": "05-stocks",
        "icon": "📈",
        "default_tags": ["股票", "investment"],
        "template": "stock",
    },
    NoteCategory.VIDEO: {
        "folder": "06-videos",
        "icon": "🎬",
        "default_tags": ["视频", "video"],
        "template": "video",
    },
    NoteCategory.SCHEDULE: {
        "folder": "07-schedule",
        "icon": "📅",
        "default_tags": ["行程", "schedule"],
        "template": "schedule",
    },
    NoteCategory.FITNESS: {
        "folder": "08-fitness",
        "icon": "💪",
        "default_tags": ["健身", "fitness"],
        "template": "fitness",
    },
    NoteCategory.LEARNING: {
        "folder": "03-books",
        "icon": "📝",
        "default_tags": ["学习", "learning"],
        "template": "learning",
    },
    NoteCategory.GENERAL: {
        "folder": "00-inbox",
        "icon": "📌",
        "default_tags": ["碎碎念"],
        "template": "general",
    },
}

# Default vault path
DEFAULT_VAULT_PATH = Path(__file__).parent.parent / "vault"
DEFAULT_DATA_PATH = Path(__file__).parent.parent / "data"
KNOWLEDGE_BASE_FILE = "knowledge_base.json"
