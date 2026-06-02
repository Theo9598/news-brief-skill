import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Generate AI-directed search tasks from target-source config.")
    parser.add_argument("targets_json")
    parser.add_argument("--date-terms", required=True, help="Search date terms, e.g. '2026年6月1日 OR 2026年5月31日 OR 2026年5月30日'")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    config = json.loads(Path(args.targets_json).read_text(encoding="utf-8"))
    tasks = []
    for target in config.get("targets", []):
        domains = target.get("domains", [])
        templates = target.get("query_templates", [])
        for template in templates:
            if "{domain}" in template:
                for domain in domains:
                    tasks.append(
                        {
                            "target": target["name"],
                            "domain": domain,
                            "use_for": target.get("use_for", []),
                            "query": template.replace("{domain}", domain).replace("{date_terms}", args.date_terms),
                        }
                    )
            else:
                tasks.append(
                    {
                        "target": target["name"],
                        "domain": ",".join(domains),
                        "use_for": target.get("use_for", []),
                        "query": template.replace("{date_terms}", args.date_terms),
                    }
                )

    output = {
        "date_terms": args.date_terms,
        "task_count": len(tasks),
        "tasks": tasks,
    }
    Path(args.out).write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"tasks={len(tasks)}")
    print(args.out)


if __name__ == "__main__":
    main()
