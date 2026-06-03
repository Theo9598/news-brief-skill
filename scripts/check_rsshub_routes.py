import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin


UA = "Mozilla/5.0 (compatible; CodexNewsBrief RSSHubHealth/1.0)"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def normalize_instance(instance):
    return instance.rstrip("/") + "/"


def route_url(instance, route):
    return urljoin(normalize_instance(instance), route.lstrip("/"))


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


def should_include(item, args):
    if not args.include_disabled and not item.get("enabled", True):
        return False
    if args.priority and item.get("priority") not in set(args.priority):
        return False
    if args.tier and not (set(args.tier) & inferred_tiers(item)):
        return False
    if args.field and not (set(args.field) & route_fields(item)):
        return False
    return True


def classify_error(exc):
    if isinstance(exc, urllib.error.HTTPError):
        return f"http_{exc.code}"
    if isinstance(exc, urllib.error.URLError):
        return "url_error"
    if isinstance(exc, TimeoutError):
        return "timeout"
    return exc.__class__.__name__


def probe(url, timeout):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
        },
    )
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(512)
            elapsed_ms = int((time.time() - started) * 1000)
            body_lower = body.lower()
            looks_like_feed = b"<rss" in body_lower or b"<feed" in body_lower or b"<rdf" in body_lower
            return {
                "status": "ok" if looks_like_feed else "non_feed",
                "http_status": getattr(resp, "status", ""),
                "elapsed_ms": elapsed_ms,
                "sample": body[:120].decode("utf-8", errors="replace"),
            }
    except Exception as exc:
        elapsed_ms = int((time.time() - started) * 1000)
        return {
            "status": classify_error(exc),
            "elapsed_ms": elapsed_ms,
            "error": repr(exc),
        }


def build_instances(config, args):
    instances = []
    if args.instance:
        instances.extend(args.instance)
    else:
        if config.get("default_instance"):
            instances.append(config["default_instance"])
        instances.extend(config.get("fallback_instances", []))
    seen = set()
    out = []
    for instance in instances:
        clean = instance.rstrip("/")
        if clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def main():
    parser = argparse.ArgumentParser(description="Probe RSSHub routes across public/self-hosted instances.")
    parser.add_argument("routes_json")
    parser.add_argument("--instance", action="append", help="RSSHub instance base URL. Can be repeated.")
    parser.add_argument("--include-disabled", action="store_true")
    parser.add_argument("--priority", action="append")
    parser.add_argument("--tier", action="append")
    parser.add_argument("--field", action="append")
    parser.add_argument("--max-routes", type=int)
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    config = load_json(args.routes_json)
    instances = build_instances(config, args)
    routes = [item for item in config.get("routes", []) if should_include(item, args)]
    if args.max_routes:
        routes = routes[: args.max_routes]

    results = []
    for item in routes:
        attempts = []
        best_url = ""
        best_instance = ""
        best_status = "failed"
        for instance in instances:
            url = route_url(instance, item["route"])
            result = probe(url, args.timeout)
            result["instance"] = instance
            result["url"] = url
            attempts.append(result)
            if result["status"] == "ok":
                best_url = url
                best_instance = instance
                best_status = "ok"
                break
            if result["status"] == "non_feed" and best_status == "failed":
                best_status = "non_feed"
                best_url = url
                best_instance = instance
        results.append(
            {
                "name": item["name"],
                "route": item["route"],
                "sections": item.get("sections", []),
                "fields": sorted(route_fields(item)),
                "tiers": sorted(inferred_tiers(item)),
                "priority": item.get("priority", ""),
                "source_type": item.get("source_type", ""),
                "status": best_status,
                "best_instance": best_instance,
                "best_url": best_url,
                "attempts": attempts,
            }
        )

    output = {
        "notes": "RSSHub route health check. Use ok routes as candidate discovery feeds only.",
        "instances": instances,
        "route_count": len(results),
        "ok_count": sum(1 for item in results if item["status"] == "ok"),
        "routes": results,
    }
    Path(args.out).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"routes={len(results)}")
    print(f"ok={output['ok_count']}")
    print(args.out)


if __name__ == "__main__":
    main()
