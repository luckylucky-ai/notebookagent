#!/usr/bin/env python3
"""CLI entry point for the Obsidian Note Organizer.

Usage examples:

  # Quick note (general)
  python main.py --category general --title "随想" --content "今天天气真好"

  # Inspiration
  python main.py --category inspiration --title "App idea" \
      --content "做一个可以识别花的App" --tags "创业,AI" \
      --key-points "用图像识别" "结合植物百科"

  # Stock
  python main.py --category stock --title "腾讯操作" \
      --content "技术面突破，成交量放大" \
      --stock-symbol "0700.HK" --stock-action buy --stock-price 380.5

  # Fitness
  python main.py --category fitness --title "胸肌日" \
      --content "今天做了卧推和飞鸟" \
      --exercise-type "力量训练" --duration 60 --intensity high

  # List notes
  python main.py --list
  python main.py --list --category stock

  # Show stats
  python main.py --stats
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

from organizer import NoteOrganizer, NoteCategory


def main():
    parser = argparse.ArgumentParser(
        description="Obsidian Note Organizer - 碎碎念整理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Mode
    parser.add_argument("--list", action="store_true", help="列出已有笔记")
    parser.add_argument("--stats", action="store_true", help="显示统计信息")

    # Note fields
    parser.add_argument("-c", "--category", type=str,
                        choices=[c.value for c in NoteCategory],
                        help="笔记分类")
    parser.add_argument("-t", "--title", type=str, help="笔记标题")
    parser.add_argument("--content", type=str, help="笔记内容")
    parser.add_argument("--tags", type=str, help="标签 (逗号分隔)")
    parser.add_argument("--key-points", nargs="+", help="要点列表")
    parser.add_argument("--source", type=str, help="来源 (URL、书名等)")

    # Mood
    parser.add_argument("--mood-score", type=int, choices=range(1, 11),
                        metavar="1-10", help="心情指数 (1-10)")

    # Stock
    parser.add_argument("--stock-symbol", type=str, help="股票代码")
    parser.add_argument("--stock-action", type=str,
                        choices=["buy", "sell", "watch"], help="操作类型")
    parser.add_argument("--stock-price", type=float, help="操作价格")
    parser.add_argument("--stock-reasoning", type=str, help="操作逻辑")

    # Fitness
    parser.add_argument("--exercise-type", type=str, help="运动类型")
    parser.add_argument("--duration", type=int, help="时长(分钟)")
    parser.add_argument("--intensity", type=str,
                        choices=["low", "medium", "high"], help="强度")

    # Vault path
    parser.add_argument("--vault", type=str, help="Obsidian vault 路径")

    args = parser.parse_args()

    vault_path = Path(args.vault) if args.vault else None
    organizer = NoteOrganizer(vault_path=vault_path)

    # List mode
    if args.list:
        cat = NoteCategory(args.category) if args.category else None
        notes = organizer.list_notes(cat)
        if not notes:
            print("暂无笔记")
        else:
            for n in notes:
                print(f"  {n.stem}")
        return

    # Stats mode
    if args.stats:
        stats = organizer.get_stats()
        print(f"📊 笔记统计")
        print(f"   总计: {stats['total_notes']} 条")
        if stats["categories"]:
            print(f"   分类:")
            for cat, count in stats["categories"].items():
                print(f"     {cat}: {count}")
        if stats["top_tags"]:
            print(f"   热门标签:")
            for tag, count in list(stats["top_tags"].items())[:10]:
                print(f"     #{tag}: {count}")
        return

    # Create note mode
    if not args.category or not args.title or not args.content:
        parser.error("创建笔记需要: --category, --title, --content")

    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []

    result = organizer.organize(
        category=args.category,
        title=args.title,
        content=args.content,
        tags=tags,
        key_points=args.key_points,
        source=args.source,
        mood_score=args.mood_score,
        stock_symbol=args.stock_symbol,
        stock_action=args.stock_action,
        stock_price=args.stock_price,
        stock_reasoning=args.stock_reasoning,
        exercise_type=args.exercise_type,
        duration_minutes=args.duration,
        intensity=args.intensity,
    )

    print(result.summary())


if __name__ == "__main__":
    main()
