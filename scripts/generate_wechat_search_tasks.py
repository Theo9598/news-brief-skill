import argparse
import json
from pathlib import Path


FIELD_KEYWORDS = {
    "technology_ai": ["AI", "人工智能", "机器人", "大模型", "算力", "科技创新"],
    "healthcare": ["医疗", "医药", "医保", "创新药", "公共卫生", "健康"],
    "macro_finance_trade": ["宏观", "金融", "投资", "外资", "外贸", "就业", "消费"],
    "consumption_services": ["消费", "服务业", "平台经济", "即时零售", "餐饮", "文旅"],
}


def unique(seq):
    seen = set()
    out = []
    for item in seq:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def build_route_queries(account, date_terms, keywords, domains):
    keyword_expr = " OR ".join(keywords[:8])
    route_queries = {
        "canonical_site": [
            f'site:{domain} ({date_terms}) {keyword_expr}'
            for domain in domains
        ],
        "mp_weixin": [
            f'site:mp.weixin.qq.com "{account}" ({date_terms}) {keyword_expr}',
            f'site:mp.weixin.qq.com ({date_terms}) "{account}"',
        ],
        "sogou_weixin": [
            f'site:weixin.sogou.com "{account}" ({date_terms}) {keyword_expr}',
            f'搜狗微信 "{account}" ({date_terms}) {keyword_expr}',
        ],
        "repost_pages": [
            f'"{account}" ({date_terms}) {keyword_expr} -site:mp.weixin.qq.com',
            f'"{account}" "{keywords[0] if keywords else ""}" ({date_terms}) 转载 原文',
        ],
        "original_source_trace": [
            f'({date_terms}) {keyword_expr} 原始来源 报告 公告 数据',
            f'({date_terms}) {keyword_expr} 专家 表示 认为 机构 报告',
        ],
    }
    return route_queries


def main():
    parser = argparse.ArgumentParser(description="Generate AI/search tasks from a WeChat public-account lead whitelist.")
    parser.add_argument("wechat_sources_json")
    parser.add_argument("--date-terms", required=True)
    parser.add_argument("--levels", default="A,B", help="Comma-separated levels to include, e.g. A,B,C,optional_expansion")
    parser.add_argument("--routes-json", help="Optional account-to-domain resolution route config.")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    config = json.loads(Path(args.wechat_sources_json).read_text(encoding="utf-8"))
    routes = {}
    if args.routes_json:
        routes = json.loads(Path(args.routes_json).read_text(encoding="utf-8"))
    route_accounts = routes.get("accounts", {})
    resolution_order = routes.get(
        "default_resolution_order",
        ["canonical_site", "mp_weixin", "sogou_weixin", "repost_pages", "original_source_trace"],
    )
    selected_levels = [level.strip() for level in args.levels.split(",") if level.strip()]

    accounts = []
    for level in selected_levels:
        level_data = config.get("levels", {}).get(level, {})
        accounts.extend(level_data.get("accounts", []))
    accounts = unique(accounts)

    account_to_fields = {account: [] for account in accounts}
    for field, field_accounts in config.get("use_rules", {}).items():
        for account in field_accounts:
            if account in account_to_fields:
                account_to_fields[account].append(field)

    tasks = []
    for account in accounts:
        fields = account_to_fields.get(account) or ["macro_finance_trade"]
        keywords = unique(keyword for field in fields for keyword in FIELD_KEYWORDS.get(field, []))
        domains = route_accounts.get(account, {}).get("canonical_domains", [])
        query = f'"{account}" ({args.date_terms}) ' + " OR ".join(keywords[:8])
        tasks.append(
            {
                "account": account,
                "fields": fields,
                "query": query,
                "canonical_domains": domains,
                "resolution_order": resolution_order,
                "route_queries": build_route_queries(account, args.date_terms, keywords, domains),
                "use": "WeChat/public-account lead only; trace to original source before final use.",
                "trace_rule": "Prefer canonical web domains; if unavailable, try mp.weixin.qq.com, Sogou Weixin, stable repost pages, then trace named data/report/policy back to the original source.",
                "classification_required": ["source_level", "use_method", "trace_status", "risk"],
            }
        )

    payload = {
        "date_terms": args.date_terms,
        "levels": selected_levels,
        "resolution_order": resolution_order,
        "tasks": tasks,
    }
    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"tasks={len(tasks)}")
    print(args.out)


if __name__ == "__main__":
    main()
