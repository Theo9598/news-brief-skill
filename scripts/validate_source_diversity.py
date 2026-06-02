import argparse
import json
from collections import Counter
from pathlib import Path


OFFICIAL_HINTS = [
    "新华社",
    "人民日报",
    "央视",
    "人民网",
    "国务院",
    "国家统计局",
    "商务部",
    "央行",
    "国家医保局",
    "国家卫健委",
    "发改委",
    "工信部",
]


def source_label(item):
    return item.get("source", "").split("，")[0].strip() or "(missing source)"


def main():
    parser = argparse.ArgumentParser(description="Check source diversity for selected news brief items.")
    parser.add_argument("brief_items_json")
    parser.add_argument(
        "--max-source-share",
        type=float,
        default=0.20,
        help="Hard share ceiling for a single source label. Use 0.15 for high-diversity delivery.",
    )
    parser.add_argument(
        "--max-source-count",
        type=int,
        default=2,
        help="Hard count ceiling for a single source label. Default keeps repeated sources to at most two items.",
    )
    parser.add_argument("--max-official-share", type=float, default=0.25)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    data = json.loads(Path(args.brief_items_json).read_text(encoding="utf-8"))
    items = data.get("items", [])
    total = len(items)
    errors = []
    warnings = []

    sources = Counter()
    official_count = 0
    for item in items:
        source = source_label(item)
        sources[source] += 1
        if any(hint in item.get("source", "") for hint in OFFICIAL_HINTS):
            official_count += 1

    if total:
        for source, count in sources.items():
            share = count / total
            if count > args.max_source_count:
                message = f"source repeat count high: {source} {count}/{total}"
                if args.strict:
                    errors.append(message)
                else:
                    warnings.append(message)
            if share > args.max_source_share:
                message = f"source concentration high: {source} {count}/{total} ({share:.0%})"
                if args.strict:
                    errors.append(message)
                else:
                    warnings.append(message)

        official_share = official_count / total
        if official_share > args.max_official_share:
            message = f"official/authority source share high: {official_count}/{total} ({official_share:.0%})"
            if args.strict:
                errors.append(message)
            else:
                warnings.append(message)

    print(f"items={total}")
    print("sources=" + json.dumps(sources, ensure_ascii=False, sort_keys=True))
    print(f"official_like={official_count}")
    print(f"errors={len(errors)}")
    for error in errors:
        print("ERROR: " + error)
    print(f"warnings={len(warnings)}")
    for warning in warnings:
        print("WARNING: " + warning)
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
