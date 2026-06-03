import argparse
import json
from pathlib import Path


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(description="Generate feed_sources-compatible JSON from RSSHub health-check output.")
    parser.add_argument("health_json")
    parser.add_argument("--include-non-feed", action="store_true")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    health = load_json(args.health_json)
    feeds = []
    for item in health.get("routes", []):
        if item.get("status") != "ok" and not (args.include_non_feed and item.get("status") == "non_feed"):
            continue
        if not item.get("best_url"):
            continue
        feeds.append(
            {
                "name": item["name"],
                "url": item["best_url"],
                "sections": item.get("sections", []),
                "source_type": item.get("source_type", "rsshub_route"),
                "source_origin": "rsshub_live",
                "rsshub_route": item["route"],
                "rsshub_instance": item.get("best_instance", ""),
                "priority": item.get("priority", ""),
                "tiers": item.get("tiers", []),
                "fields": item.get("fields", []),
            }
        )

    output = {
        "notes": "Generated from RSSHub health-check output. Use for candidate discovery only; cite original source URLs in final briefs where possible.",
        "health_source": str(args.health_json),
        "feeds": feeds,
    }
    Path(args.out).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"feeds={len(feeds)}")
    print(args.out)


if __name__ == "__main__":
    main()
