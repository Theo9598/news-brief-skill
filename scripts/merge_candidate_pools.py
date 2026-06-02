import argparse
import json
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Merge candidate pools and de-duplicate by URL/title.")
    parser.add_argument("candidate_pools", nargs="+")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    pools = [load(path) for path in args.candidate_pools]
    base = pools[0]
    merged = {
        "brief_date": base["brief_date"],
        "title": base.get("title", "新闻项目简报"),
        "subtitle": base.get("subtitle", ""),
        "date_window": base["date_window"],
        "sections": base["sections"],
        "collection_methods": [],
        "candidates": [],
    }

    seen = set()
    counter = 1
    for pool in pools:
        merged["collection_methods"].extend(pool.get("collection_methods", []))
        for item in pool.get("candidates", []):
            key = item.get("url") or item.get("title")
            if key in seen:
                continue
            seen.add(key)
            copied = dict(item)
            copied["id"] = f"m{counter:03d}"
            counter += 1
            merged["candidates"].append(copied)

    Path(args.out).write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"merged_candidates={len(merged['candidates'])}")
    print(args.out)


if __name__ == "__main__":
    main()
