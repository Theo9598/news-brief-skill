import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


REQUIRED_ITEM_FIELDS = ["title", "field", "section", "source", "source_date", "url", "body"]
REQUIRED_DOMAINS = ["科技创新", "医疗卫生", "数字经济", "服务业", "消费", "就业", "货币金融", "投资", "外资外贸"]


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate(data):
    errors = []
    warnings = []
    date_window = set(data.get("date_window", []))
    sections = data.get("sections", [])
    items = data.get("items", [])

    if not data.get("brief_date"):
        errors.append("missing brief_date")
    if not date_window:
        errors.append("missing date_window")
    if not sections:
        errors.append("missing sections")
    if not items:
        errors.append("missing items")

    seen_urls = Counter()
    section_counts = Counter()
    domain_text = []

    for idx, item in enumerate(items, 1):
        for field in REQUIRED_ITEM_FIELDS:
            if not item.get(field):
                errors.append(f"item {idx} missing {field}")

        source_date = item.get("source_date")
        if source_date and source_date not in date_window:
            errors.append(f"item {idx} source_date outside window: {source_date}")

        source = item.get("source", "")
        source_dates = set(re.findall(r"20\d{2}-\d{2}-\d{2}", source))
        outside_source_dates = source_dates - date_window
        if outside_source_dates:
            errors.append(f"item {idx} source contains outside-window dates: {sorted(outside_source_dates)}")

        section = item.get("section")
        if section not in sections:
            errors.append(f"item {idx} section not in sections: {section}")
        section_counts[section] += 1

        seen_urls[item.get("url", "")] += 1
        domain_text.extend([item.get("field", ""), item.get("section", ""), item.get("title", ""), item.get("body", "")])

        body_len = len(item.get("body", ""))
        if body_len < 180:
            warnings.append(f"item {idx} body may be too short: {body_len} chars")
        if body_len > 520:
            warnings.append(f"item {idx} body may be too long: {body_len} chars")

    combined = "\n".join(domain_text)
    missing_domains = [domain for domain in REQUIRED_DOMAINS if domain not in combined]
    if missing_domains:
        errors.append(f"missing required domains: {missing_domains}")

    thin_sections = [section for section in sections if section_counts[section] < 1]
    if thin_sections:
        errors.append(f"sections with no items: {thin_sections}")

    duplicate_urls = {url: count for url, count in seen_urls.items() if url and count > 1}
    if duplicate_urls:
        warnings.append(f"duplicate urls: {duplicate_urls}")

    viewpoint_count = sum(1 for item in items if item.get("viewpoint_person") or item.get("viewpoint_org") or item.get("viewpoint"))
    if items and viewpoint_count < max(1, int(len(items) * 0.6)):
        warnings.append(f"low viewpoint coverage: {viewpoint_count}/{len(items)} items")

    return errors, warnings, section_counts


def main():
    parser = argparse.ArgumentParser(description="Validate structured news brief data.")
    parser.add_argument("input_json")
    args = parser.parse_args()

    data = load_json(args.input_json)
    errors, warnings, section_counts = validate(data)

    print(f"items={len(data.get('items', []))}")
    print(f"date_window={','.join(data.get('date_window', []))}")
    print("section_counts=" + json.dumps(section_counts, ensure_ascii=False, sort_keys=True))
    print(f"errors={len(errors)}")
    for error in errors:
        print("ERROR: " + error)
    print(f"warnings={len(warnings)}")
    for warning in warnings:
        print("WARNING: " + warning)
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
