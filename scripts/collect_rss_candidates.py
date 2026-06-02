import argparse
import email.utils
import html
import json
import re
import site
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


UA = "Mozilla/5.0 (compatible; CodexNewsBrief/1.0; +https://openai.com)"


WORKSPACE_PACKAGES = Path.cwd() / ".python-packages"
if WORKSPACE_PACKAGES.exists():
    site.addsitedir(str(WORKSPACE_PACKAGES))

try:
    import feedparser  # type: ignore
except Exception:
    feedparser = None

try:
    import trafilatura  # type: ignore
except Exception:
    trafilatura = None


def text_of(element, names):
    for name in names:
        found = element.find(name)
        if found is not None and found.text:
            return html.unescape(found.text.strip())
    return ""


def strip_tags(value):
    return re.sub(r"<[^>]+>", "", value or "").strip()


def parse_date(value):
    value = (value or "").strip()
    if not value:
        return ""
    try:
        parsed = email.utils.parsedate_to_datetime(value)
        if parsed:
            if parsed.tzinfo:
                parsed = parsed.astimezone(timezone.utc)
            return parsed.strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        pass
    match = re.search(r"(20\d{2})[-/年](\d{1,2})[-/月](\d{1,2})", value)
    if match:
        y, m, d = match.groups()
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
    return ""


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read()


def parse_feed(raw):
    if feedparser is not None:
        parsed = feedparser.parse(raw)
        for entry in parsed.entries:
            links = getattr(entry, "links", []) or []
            url = getattr(entry, "link", "")
            if not url and links:
                url = links[0].get("href", "")
            yield {
                "title": getattr(entry, "title", ""),
                "url": url,
                "published_raw": getattr(entry, "published", "") or getattr(entry, "updated", ""),
                "summary": strip_tags(getattr(entry, "summary", "")),
            }
        return

    root = ET.fromstring(raw)
    items = root.findall(".//item")
    if items:
        for item in items:
            yield {
                "title": text_of(item, ["title"]),
                "url": text_of(item, ["link"]),
                "published_raw": text_of(item, ["pubDate", "date", "{http://purl.org/dc/elements/1.1/}date"]),
                "summary": strip_tags(text_of(item, ["description", "summary"])),
            }
        return

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall(".//atom:entry", ns):
        link = ""
        link_el = entry.find("atom:link", ns)
        if link_el is not None:
            link = link_el.attrib.get("href", "")
        yield {
            "title": text_of(entry, ["{http://www.w3.org/2005/Atom}title"]),
            "url": link,
            "published_raw": text_of(entry, ["{http://www.w3.org/2005/Atom}published", "{http://www.w3.org/2005/Atom}updated"]),
            "summary": strip_tags(text_of(entry, ["{http://www.w3.org/2005/Atom}summary", "{http://www.w3.org/2005/Atom}content"])),
        }


def main():
    parser = argparse.ArgumentParser(description="Collect raw RSS candidates using only Python stdlib.")
    parser.add_argument("feeds_json")
    parser.add_argument("--brief-date", required=True)
    parser.add_argument("--window", nargs="+", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--extract-text", action="store_true", help="Fetch candidate pages and extract text with trafilatura when installed.")
    parser.add_argument("--max-extract", type=int, default=30)
    args = parser.parse_args()

    config = json.loads(Path(args.feeds_json).read_text(encoding="utf-8"))
    window = set(args.window)
    candidates = []
    errors = []

    for feed in config.get("feeds", []):
        try:
            raw = fetch(feed["url"])
            for entry in parse_feed(raw):
                source_date = parse_date(entry.get("published_raw", ""))
                if source_date and source_date not in window:
                    continue
                extracted_text = ""
                if args.extract_text and trafilatura is not None and entry.get("url") and len(candidates) < args.max_extract:
                    try:
                        downloaded = trafilatura.fetch_url(entry["url"])
                        if downloaded:
                            extracted_text = trafilatura.extract(downloaded, include_comments=False, include_tables=False) or ""
                            extracted_text = extracted_text.strip()[:3000]
                    except Exception:
                        extracted_text = ""
                candidates.append(
                    {
                        "id": f"raw{len(candidates) + 1:04d}",
                        "status": "raw",
                        "title": entry.get("title", ""),
                        "source": feed["name"],
                        "source_date": source_date,
                        "url": entry.get("url", ""),
                        "summary": entry.get("summary", ""),
                        "extracted_text": extracted_text,
                        "candidate_sections": feed.get("sections", []),
                        "collection_method": "rss",
                        "feed_url": feed["url"],
                        "source_type": feed.get("source_type", ""),
                    }
                )
        except Exception as exc:
            errors.append({"feed": feed.get("name"), "url": feed.get("url"), "error": repr(exc)})

    output = {
        "brief_date": args.brief_date,
        "date_window": args.window,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "parser": "feedparser" if feedparser is not None else "stdlib_xml",
        "text_extractor": "trafilatura" if trafilatura is not None else "none",
        "feeds": config.get("feeds", []),
        "raw_candidates": candidates,
        "fetch_errors": errors,
    }
    Path(args.out).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"raw_candidates={len(candidates)}")
    print(f"fetch_errors={len(errors)}")
    print(args.out)
    if errors:
        for error in errors[:10]:
            print("FETCH_ERROR: " + json.dumps(error, ensure_ascii=False))


if __name__ == "__main__":
    main()
