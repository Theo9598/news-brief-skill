import argparse
import json
from pathlib import Path
from urllib.parse import urljoin


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_instance(instance):
    return instance.rstrip("/") + "/"


def route_url(instance, route):
    route = route.lstrip("/")
    return urljoin(normalize_instance(instance), route)


def main():
    parser = argparse.ArgumentParser(description="Generate feed_sources-compatible JSON from RSSHub route config.")
    parser.add_argument("routes_json")
    parser.add_argument("--instance", help="RSSHub instance base URL. Defaults to config default_instance.")
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--priority", action="append", help="Only include given priority. Can be repeated.")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    config = load_json(args.routes_json)
    instance = args.instance or config.get("default_instance") or "https://rsshub.app"
    priorities = set(args.priority or [])

    feeds = []
    for item in config.get("routes", []):
        if not args.include_disabled and not item.get("enabled", True):
            continue
        if priorities and item.get("priority") not in priorities:
            continue
        feeds.append(
            {
                "name": item["name"],
                "url": route_url(instance, item["route"]),
                "sections": item.get("sections", []),
                "source_type": item.get("source_type", "rsshub_route"),
                "source_origin": "rsshub",
                "rsshub_route": item["route"],
                "rsshub_instance": instance.rstrip("/"),
                "priority": item.get("priority", ""),
                "docs": item.get("docs", ""),
            }
        )

    output = {
        "notes": "Generated from RSSHub routes. Use for candidate discovery only; final brief should cite original source URLs where possible.",
        "instance": instance.rstrip("/"),
        "feeds": feeds,
    }
    Path(args.out).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"feeds={len(feeds)}")
    print(args.out)


if __name__ == "__main__":
    main()
