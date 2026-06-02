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


def inferred_tiers(item):
    if item.get("tiers"):
        return set(item["tiers"])

    priority = item.get("priority", "")
    source_type = item.get("source_type", "")
    tiers = {"sector_expansion"}
    if priority == "high":
        tiers.add("core_daily")
    if priority == "low":
        tiers.add("topic_backfill")
    if any(marker in source_type for marker in ["global", "consulting", "thinktank", "research"]):
        tiers.add("global_reference")
    if "wechat" in source_type or "public_account" in source_type:
        tiers.add("wechat_related")
    return tiers


def route_fields(item):
    return set(item.get("fields") or item.get("sections") or [])


def main():
    parser = argparse.ArgumentParser(description="Generate feed_sources-compatible JSON from RSSHub route config.")
    parser.add_argument("routes_json")
    parser.add_argument("--instance", help="RSSHub instance base URL. Defaults to config default_instance.")
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--priority", action="append", help="Only include given priority. Can be repeated.")
    parser.add_argument("--tier", action="append", help="Only include routes tagged for a tier, e.g. core_daily or sector_expansion. Can be repeated.")
    parser.add_argument("--field", action="append", help="Only include routes matching a field/section, e.g. 医疗卫生 or technology_ai. Can be repeated.")
    parser.add_argument("--max-feeds", type=int, help="Limit output after filtering, preserving config order.")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    config = load_json(args.routes_json)
    instance = args.instance or config.get("default_instance") or "https://rsshub.app"
    priorities = set(args.priority or [])
    tiers = set(args.tier or [])
    fields = set(args.field or [])

    feeds = []
    for item in config.get("routes", []):
        if not args.include_disabled and not item.get("enabled", True):
            continue
        if priorities and item.get("priority") not in priorities:
            continue
        item_tiers = inferred_tiers(item)
        if tiers and not (tiers & item_tiers):
            continue
        item_fields = route_fields(item)
        if fields and not (fields & item_fields):
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
                "tiers": sorted(item_tiers),
                "fields": sorted(item_fields),
                "docs": item.get("docs", ""),
            }
        )
        if args.max_feeds and len(feeds) >= args.max_feeds:
            break

    output = {
        "notes": "Generated from RSSHub routes. Use for candidate discovery only; final brief should cite original source URLs where possible.",
        "instance": instance.rstrip("/"),
        "filters": {
            "priority": sorted(priorities),
            "tier": sorted(tiers),
            "field": sorted(fields),
            "max_feeds": args.max_feeds,
        },
        "feeds": feeds,
    }
    Path(args.out).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"feeds={len(feeds)}")
    print(args.out)


if __name__ == "__main__":
    main()
