import argparse
import json
from pathlib import Path


DEFAULT_PATTERN_PATH = Path(__file__).resolve().parent.parent / "references" / "insight_title_patterns.json"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def title_has_insight(title, markers):
    return any(marker in title for marker in markers)


def title_is_weak_news(title, weak_words, markers):
    has_weak = any(word in title for word in weak_words)
    has_marker = title_has_insight(title, markers)
    return has_weak and not has_marker


def main():
    parser = argparse.ArgumentParser(description="Soft-check whether brief item titles carry policy insight rather than only news facts.")
    parser.add_argument("brief_json")
    parser.add_argument("--patterns", default=str(DEFAULT_PATTERN_PATH))
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when weak titles are found.")
    args = parser.parse_args()

    brief = load_json(args.brief_json)
    patterns = load_json(args.patterns)
    markers = patterns.get("insight_markers", [])
    weak_words = patterns.get("weak_news_words", [])

    warnings = []
    for idx, item in enumerate(brief.get("items", []), 1):
        title = item.get("title", "")
        if not title:
            warnings.append(f"item {idx} missing title")
            continue
        if len(title) < 12:
            warnings.append(f"item {idx} title may be too short for insight style: {title}")
        if not title_has_insight(title, markers):
            warnings.append(f"item {idx} title lacks insight marker: {title}")
        elif title_is_weak_news(title, weak_words, markers):
            warnings.append(f"item {idx} title may be event-only: {title}")

    print(f"items={len(brief.get('items', []))}")
    print(f"warnings={len(warnings)}")
    for warning in warnings:
        print("WARNING: " + warning)
    raise SystemExit(1 if args.strict and warnings else 0)


if __name__ == "__main__":
    main()
