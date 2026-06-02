import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Promote selected candidates into brief item JSON.")
    parser.add_argument("candidate_pool_json")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    pool = json.loads(Path(args.candidate_pool_json).read_text(encoding="utf-8"))
    selected = [item for item in pool.get("candidates", []) if item.get("status") == "selected"]
    brief = {
        "brief_date": pool["brief_date"],
        "title": pool.get("title", "新闻项目简报"),
        "subtitle": pool.get("subtitle", ""),
        "date_window": pool["date_window"],
        "sections": pool["sections"],
        "items": [
            {
                "title": item["title"],
                "field": item["field"],
                "section": item["section"],
                "source": item["source"],
                "source_date": item["source_date"],
                "url": item["url"],
                "viewpoint_person": item.get("viewpoint_person", ""),
                "viewpoint_org": item.get("viewpoint_org", ""),
                "viewpoint": item.get("viewpoint", ""),
                "body": item["body"],
            }
            for item in selected
        ],
    }
    Path(args.out).write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"selected={len(selected)}")
    print(args.out)


if __name__ == "__main__":
    main()
