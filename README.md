# News Brief Workflow Skill

This Codex skill produces reproducible Chinese news brief DOCX reports for technology innovation, healthcare, digital economy, services, consumption, employment, finance, investment, foreign investment, and trade.

The workflow combines:

- RSS/list/API discovery for broad candidate collection.
- RSSHub route expansion for sources that do not expose stable public feeds.
- AI-directed search for high-value reports, viewpoints, and original sources.
- WeChat/public-account leads with trace-back rules.
- Hard validation for date windows, required fields, source diversity, and final DOCX structure.

See `SKILL.md` for the full operating instructions.

Common RSSHub generation examples:

```powershell
python scripts/generate_rsshub_feeds.py references/rsshub_routes.json --tier core_daily --out rsshub_core_feeds.json
python scripts/generate_rsshub_feeds.py references/rsshub_routes.json --tier sector_expansion --field 医疗卫生 --out rsshub_health_feeds.json
python scripts/generate_rsshub_feeds.py references/rsshub_routes.json --tier topic_backfill --field technology_ai --out rsshub_ai_backfill_feeds.json
```
