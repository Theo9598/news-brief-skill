---
name: news-brief-workflow
description: Produce reproducible Chinese news brief DOCX reports with strict date-window rules, source quality checks, field coverage, viewpoint-oriented writing, and validation for policy/economic/technology/health news projects.
metadata:
  short-description: Reproducible Chinese news brief workflow
---

# News Brief Workflow

Use this skill when the user asks to create, update, or systematize a Chinese news brief/news project covering technology innovation, healthcare, digital economy, services, consumption, employment, finance, investment, foreign investment, or trade.

## Workflow

1. **Set the date window**
   - If the brief date is Monday: use Saturday, Sunday, and Monday.
   - If Tuesday through Friday: use the current day and previous day.
   - If weekend delivery is requested, ask for the intended brief date unless it is obvious.

2. **Build a candidate pool first**
   - Use JSON shaped like `references/candidate_pool_schema.json`.
   - Collection may use search interfaces, RSS/list pages, RSSHub routes, official public pages/APIs, or a safe crawler when explicitly useful.
   - For RSS, use `scripts/collect_rss_candidates.py FEEDS.json --brief-date YYYY-MM-DD --window ... --out RAW.json`.
   - To expand RSS coverage with RSSHub, generate feed JSON first:
     `scripts/generate_rsshub_feeds.py references/rsshub_routes.json --out RSSHUB_FEEDS.json`.
     For the normal daily run, prefer `--tier core_daily`; for thin sections, add `--tier sector_expansion --field 医疗卫生` or another relevant field; for narrow backfills, use `--tier topic_backfill --field technology_ai`.
     RSSHub routes are discovery aids only; final briefs should cite original article/report URLs where possible.
   - If project-local `.python-packages` contains `feedparser`, the script uses it for RSS/Atom parsing; otherwise it falls back to Python stdlib XML parsing.
   - Add `--extract-text --max-extract N` to fetch candidate pages and extract article text with `trafilatura` when installed.
   - Do not run third-party crawler code unless it has passed source, dependency, permission, install-script, and license review.
   - Candidate records must include `selected` or `rejected` plus a screening reason.

3. **Use four discovery channels**
   - RSS/list/API channel: broad, reproducible rolling-news discovery.
   - RSSHub route channel: expands RSS/list coverage for sources without stable public feeds, especially business media, finance data, healthcare industry media, AI company/research updates, consulting/thinking pieces, and public-account-adjacent sources.
   - RSSHub routes are grouped into tiers: `core_daily`, `sector_expansion`, `topic_backfill`, `wechat_related`, and `global_reference`. Use all routes only when recall matters more than speed/noise.
   - AI-directed channel: targeted search for reports, rankings, topic pages, official deep releases, think tanks, universities, international institutions, brokerage views, and named/institutional viewpoints.
   - WeChat/public-account lead channel: use `references/wechat_public_accounts.json` as a non-official lead pool for timely articles, industry cases, and viewpoints. These are leads, not final authorities by default.
   - If the project has an `ai_target_sources.json`, use it to guide targeted searches. Replace `{date_terms}` with the active date window.
   - For WeChat/public-account leads, generate routed search tasks with `scripts/generate_wechat_search_tasks.py references/wechat_public_accounts.json --routes-json references/wechat_source_routes.json --date-terms "..." --levels A,B --out WECHAT_TASKS.json`.
   - If a complete public `mp.weixin.qq.com` URL is available, fetch and extract it with `scripts/fetch_wechat_article.py URL --out ARTICLE.json`.
   - WeChat original-resolution order: canonical account/site domain first, then `mp.weixin.qq.com`, then Sogou Weixin, then stable repost pages, then trace any named data/report/policy back to the original source.
   - Aggregators such as NewsNow may be used only as discovery aids. Do not cite the aggregator as the final source when the original outlet or a stable republished page is available.
   - RSSHub instances can fail, rate-limit, or lag. Treat failed RSSHub routes as non-blocking and rerun AI-directed search for important missing sections.
   - When RSS output is dominated by a small number of rolling feeds, keep RSS items as clues and rerun AI-directed searches against finance/securities media, industry media, foreign media, think tanks, universities, associations, and international institutions.

4. **Source and selection standards**
   - Prefer first-party sources: ministries, regulators, official releases, statistical agencies, associations, international institutions, universities, high-end think tanks.
   - Use authority media and market sources when they add facts or named viewpoints.
   - Include viewpoints where useful: named officials, researchers, chief economists, industry leaders, international institution representatives.
   - Keep a problem-oriented stance: each item should contain a new fact, new problem, new explanation, or actionable policy/market implication.
   - Do not use person names as the primary discovery filter. Discover by event/topic/date first, then enrich selected items with viewpoints.
   - If a named person is unavailable, use institution-level interpretation or clearly label the item as a factual item; do not invent a speaker.
   - Diversify final selections: official media and single RSS-heavy sources should not dominate the final brief.
   - High-diversity delivery rule: aim for one item per source label; allow at most two items from the same source label unless the user explicitly asks for a narrower source set.
   - Default hard gate: no single final source should exceed 20% of selected items, and no source should exceed two items. For high-diversity delivery, run `validate_source_diversity.py --strict --max-source-share 0.15`.
   - If a source exceeds the gate, do not merely relabel it. Replace weaker items through targeted AI search and keep official sources mainly for fact verification.
   - Treat Xinhua, People's Daily, CCTV, and similar official/authority outlets as verification and key-fact sources, not the main discovery pool.
   - Prefer supplementing final selections with securities media, industry associations, industry media, think tanks, universities, international institutions, foreign media, and brokerage/research views.
   - Good China-market source mix includes, when available: 第一财经、21世纪经济报道、证券时报、中国证券报、上海证券报、财新、界面、经济观察报、每日经济新闻、财联社、行业媒体/协会、Reuters/AP/FT/Bloomberg/WSJ, and international institutions. Avoid letting 中新网, 36氪 rolling feeds, 新华社, 人民日报, or CCTV become the main body.
   - WeChat/public-account lead pool:
     - A-level daily scan: 机器之心、量子位、晚点 LatePost、财新、第一财经、21世纪经济报道、健康界、动脉网、医药魔方、财联社.
     - B/C-level scan by keyword or every 1-2 days, especially for industry cases, service consumption, platform economy, healthcare, and AI.
     - Classify every WeChat-origin candidate with: `source_level` (原创/采访/转载/观点/广告), `use_method` (事实线索/观点来源/案例来源/不用), `trace_status` (已追到原始来源/只找到一层转述/无法追源), `trace_route` (canonical_site/mp_weixin/sogou_weixin/repost_pages/original_source_trace/none), and `risk` (软文/样本口径不清/观点偏置/时效过旧).
     - Do not include a WeChat-origin item in the final brief unless it provides at least one of: new data, new policy signal, a representative case, a clear problem, or a credible expert/institutional viewpoint.
     - If `trace_status` is `无法追源`, use it only to trigger further search or as a rejected candidate; do not select it for the final brief.
     - If the WeChat original cannot be indexed, do not stop. Record which route succeeded: account official site, `mp.weixin.qq.com`, Sogou Weixin, repost page, or original source. Use the best stable URL as the candidate URL.
     - `mp.weixin.qq.com` fetches require complete, current article URLs. Incomplete or stale URLs often redirect to `wappoc_appmsgcaptcha`; treat those as blocked and continue through the route list instead of trying to bypass verification.

5. **Promote selected candidates**
   - Validate the candidate pool with `scripts/validate_candidate_pool.py CANDIDATES.json`.
   - If RSS, AI-directed search, and WeChat/public-account leads were collected separately, merge them with `scripts/merge_candidate_pools.py POOL1.json POOL2.json ... --out MERGED.json` before final screening.
   - Promote selected items with `scripts/build_brief_from_candidates.py CANDIDATES.json --out ITEMS.json`.
   - Validate final item data with `scripts/validate_brief_data.py ITEMS.json`.
   - Keep every selected `source_date` inside the date window. Rejected candidates may be outside the window if their rejection reason says so.

6. **Generate the DOCX**
   - Use `scripts/generate_news_brief.py ITEMS.json --out OUTPUT.docx`.
   - Use the bundled Python/runtime available in the current environment; do not install packages unless necessary.
   - Do not append a separate source list unless the user asks for it. Keep source and link under each item.

7. **Validate before delivery**
   - Confirm candidate pool QA, final item QA, date window, required fields, section coverage, duplicate URLs, and minimum item counts.
   - Run source diversity QA:
     `scripts/validate_source_diversity.py ITEMS.json --strict --max-source-share 0.15`
   - Viewpoint coverage is a quality signal, not a hard gate: missing viewpoints should trigger targeted follow-up search, not deletion of otherwise important facts.
   - Word delivery uses structural checks only: generated file exists, expected item count is present, source links are embedded, no separate source list exists unless requested, and document colors follow the project style.

## Default Sections

Use these sections unless the user requests another taxonomy:

- 科技创新
- 医疗卫生
- 数字经济
- 服务业/消费
- 就业
- 货币金融/投资
- 外资外贸

Target 2-3 items per section when enough fresh information exists. It is acceptable to have fewer in a low-news section if forcing items would weaken quality or violate the date window.
