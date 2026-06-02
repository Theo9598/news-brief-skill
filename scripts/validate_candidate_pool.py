import argparse
import json
from collections import Counter
from pathlib import Path


REQUIRED_CANDIDATE_FIELDS = ["id", "status", "discovery_method", "section", "field", "title", "source", "source_date", "url", "screening_reason"]
VALID_STATUS = {"selected", "rejected"}
VALID_DISCOVERY = {"rss", "ai_search", "official_page", "manual_verified", "crawler", "api", "wechat_lead"}
VALID_SOURCE_LEVEL = {"原创", "采访", "转载", "观点", "广告", ""}
VALID_USE_METHOD = {"事实线索", "观点来源", "案例来源", "不用", ""}
VALID_TRACE_STATUS = {"已追到原始来源", "只找到一层转述", "无法追源", ""}
VALID_TRACE_ROUTE = {"canonical_site", "mp_weixin", "sogou_weixin", "repost_pages", "original_source_trace", "none", ""}
VALID_RISK = {"软文", "样本口径不清", "观点偏置", "时效过旧", ""}


def main():
    parser = argparse.ArgumentParser(description="Validate candidate pool before AI screening output is promoted.")
    parser.add_argument("candidate_pool_json")
    args = parser.parse_args()

    pool = json.loads(Path(args.candidate_pool_json).read_text(encoding="utf-8"))
    date_window = set(pool.get("date_window", []))
    sections = set(pool.get("sections", []))
    candidates = pool.get("candidates", [])
    errors = []
    warnings = []

    if not pool.get("collection_methods"):
        errors.append("missing collection_methods")
    if not date_window:
        errors.append("missing date_window")
    if not sections:
        errors.append("missing sections")
    if not candidates:
        errors.append("missing candidates")

    ids = Counter()
    selected_counts = Counter()
    for idx, item in enumerate(candidates, 1):
        for field in REQUIRED_CANDIDATE_FIELDS:
            if not item.get(field):
                errors.append(f"candidate {idx} missing {field}")
        ids[item.get("id", "")] += 1
        if item.get("status") not in VALID_STATUS:
            errors.append(f"candidate {idx} invalid status: {item.get('status')}")
        if item.get("discovery_method") not in VALID_DISCOVERY:
            errors.append(f"candidate {idx} invalid discovery_method: {item.get('discovery_method')}")
        if item.get("source_level", "") not in VALID_SOURCE_LEVEL:
            errors.append(f"candidate {idx} invalid source_level: {item.get('source_level')}")
        if item.get("use_method", "") not in VALID_USE_METHOD:
            errors.append(f"candidate {idx} invalid use_method: {item.get('use_method')}")
        if item.get("trace_status", "") not in VALID_TRACE_STATUS:
            errors.append(f"candidate {idx} invalid trace_status: {item.get('trace_status')}")
        if item.get("trace_route", "") not in VALID_TRACE_ROUTE:
            errors.append(f"candidate {idx} invalid trace_route: {item.get('trace_route')}")
        if item.get("risk", "") and item.get("risk") not in VALID_RISK:
            errors.append(f"candidate {idx} invalid risk: {item.get('risk')}")

        if item.get("discovery_method") == "wechat_lead":
            if not item.get("wechat_account"):
                warnings.append(f"candidate {idx} wechat_lead missing wechat_account")
            if item.get("status") == "selected" and item.get("trace_status") == "无法追源":
                errors.append(f"candidate {idx} selected wechat_lead cannot be traced to an original source")
            if item.get("status") == "selected" and item.get("trace_route", "") in {"", "none"}:
                warnings.append(f"candidate {idx} selected wechat_lead missing trace_route")
            if item.get("status") == "selected" and item.get("source_level") == "广告":
                errors.append(f"candidate {idx} selected wechat_lead is marked as advertising")
            if item.get("status") == "selected" and item.get("use_method") == "不用":
                errors.append(f"candidate {idx} selected wechat_lead use_method is 不用")
        if item.get("source_date") not in date_window:
            if item.get("status") == "selected":
                errors.append(f"candidate {idx} selected source_date outside window: {item.get('source_date')}")
            else:
                warnings.append(f"candidate {idx} rejected outside date window: {item.get('source_date')}")
        if item.get("section") not in sections:
            errors.append(f"candidate {idx} unknown section: {item.get('section')}")
        if item.get("status") == "selected":
            selected_counts[item.get("section")] += 1
            if not item.get("body"):
                errors.append(f"candidate {idx} selected but missing body")

    duplicate_ids = [id_ for id_, count in ids.items() if id_ and count > 1]
    if duplicate_ids:
        errors.append(f"duplicate ids: {duplicate_ids}")

    thin_sections = [section for section in sections if selected_counts[section] < 1]
    if thin_sections:
        warnings.append(f"selected sections with no items: {thin_sections}")

    selected_items = [item for item in candidates if item.get("status") == "selected"]
    viewpoint_count = sum(
        1 for item in selected_items
        if item.get("viewpoint_person") or item.get("viewpoint_org") or item.get("viewpoint")
    )
    if selected_items and viewpoint_count < max(1, int(len(selected_items) * 0.6)):
        warnings.append(f"low viewpoint coverage: {viewpoint_count}/{len(selected_items)} selected items")

    print(f"candidates={len(candidates)}")
    print(f"selected={sum(selected_counts.values())}")
    print("selected_counts=" + json.dumps(selected_counts, ensure_ascii=False, sort_keys=True))
    print(f"errors={len(errors)}")
    for error in errors:
        print("ERROR: " + error)
    print(f"warnings={len(warnings)}")
    for warning in warnings:
        print("WARNING: " + warning)
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
