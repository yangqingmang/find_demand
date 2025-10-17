# Find Demand – Market Demand Analysis Toolkit

Find Demand is a full-stack toolkit for discovering, validating, and executing on market demand with a single command line workflow. It automates keyword collection, scoring, intent analysis, demand validation, and even scaffolds landing pages so that product and content teams can move from idea to deployment quickly.

## Highlights
- **Integrated demand mining pipeline** – from seed collection to opportunity scoring, trend monitoring, and volume validation in one pass.
- **Multi-source discovery** – fetches ideas from Google Suggest, Reddit, Product Hunt, Hacker News, YouTube, and more (via `SuggestionCollector` and `DiscoveryManager`).
- **Intelligent scoring & insights** – combines intent detection, SERP/market signals, commercial value, and new-word detection to prioritize ideas.
- **Volume guardrails** – recent enhancements reuse Google Trends thresholds to label each keyword as `sufficient`, `needs_review`, or `insufficient`, with summaries surfaced in CLI output.
- **One-click website scaffolding** – generate intent-driven site structures, Tailwind templates, and deployment artifacts under `generated_websites/`.
- **Crawler support** – `run_lummstudio_spider.py` mirrors external insight feeds for recurring research.

## Project Structure
| Path | Purpose |
| ---- | ------- |
| `src/collectors/` | Suggestion & trend collectors, including Google Suggest, Reddit, and Product Hunt integrations. |
| `src/demand_mining/` | Core demand mining logic (managers, analyzers, new word detector, multi-platform validation). |
| `src/pipeline/` | Cleaning, transformation, and orchestration helpers used by the CLI workflow. |
| `src/website_builder/` | Intent-aware site generator, SEO helpers, deployment adapters. |
| `config/` | Runtime configuration (`integrated_workflow_config.json`, encrypted secrets, proxy settings). |
| `data/` | Sample inputs and cached artifacts; safe location for keyword CSVs. |
| `docs/` | Playbooks, to-do lists, API guides, and demand mining SOP references. |
| `output/` | Generated CSV/JSON reports (analysis, discovery, new word detection summaries). |
| `generated_websites/` | Output of website builder workflows. |

## Core Workflows
### 1. Integrated Demand Mining
1. **Seed ingestion** – read CSV/JSON keywords or discover seeds from multi-platform sources.
2. **Cleaning & normalization** – standardize tokens, deduplicate, and filter brands.
3. **Intent & market analysis** – `KeywordManager` pipes data through intent, market, SERP, and competitive scorers.
4. **New word detection** – Google Trends-based detector grades breakout/rising terms and boosts opportunity scores when warranted.
5. **Volume validation** – each keyword receives a `volume_validation` block (recent & baseline averages vs configured thresholds) plus a `volume_validation_summary` across the batch.
6. **Reporting** – CSV/JSON outputs under `output/reports/` with per-keyword metrics, summaries, and optional trend cache exports.

Run directly through the CLI:
```bash
python main.py --input data/keywords.csv               # Analyze a prepared keyword list
python main.py --discover "AI tool" "AI generator"      # Seed discovery + analysis pipeline
python main.py --help                                   # Full CLI reference
```

### 2. Multi-Platform Discovery
`DiscoveryManager` aligns multiple sources (Reddit, Hacker News, YouTube, Google Suggestions, Twitter/X*, Product Hunt*). Results feed the demand mining pipeline or can be stored separately.

### 3. Website Generation
Once high-priority intents are chosen, `src/website_builder` can craft:
- Intent-driven navigation and page blueprints.
- Tailwind/Turbo HTML templates.
- SEO metadata and structured data stubs.
- Deployment descriptors for Vercel/Cloudflare (when tokens are configured).

Invoke via the builder CLI:
```bash
python -m src.website_builder.cli --intent "AI essay checker" --output generated_websites/essay
```

### 4. LummStudio Spider
For continuous inspiration from curated sources:
```bash
python run_lummstudio_spider.py
```
Outputs live under `src/spider/` (HTML + Markdown) and can be piped back to discovery pipelines.

## Installation
```bash
python -m venv .venv
.venv\Scripts\activate          # On Windows
# source .venv/bin/activate      # On macOS/Linux
pip install -r requirements.txt
# Playwright-based collectors require a one-time browser download
playwright install chromium
```

## Configuration
1. **Environment / secrets** – populate `config/.env` or run the encryption helper to store secrets in `config/.env.encrypted`.
2. **Google APIs** – obtain Custom Search & Ads keys (see `docs/API配置待办事项.md` for step-by-step instructions).
3. **Additional integrations** – Product Hunt, SERP API, Vercel, Cloudflare, and proxy configuration live in `config/` and can be toggled per workflow.
4. **Workflow tuning** – adjust `config/integrated_workflow_config.json` to override seed profiles, filters, scoring weights, and detector thresholds.
5. **Google Trends 指纹** – 默认为 Playwright 浏览器流量，可通过 `FIND_DEMAND_TRENDS_BACKEND` 调整 (`playwright`/`httpx`/`requests`)；若使用 Playwright，请确保运行 `playwright install chromium` 并按需配置代理/语言。

## Output & Reporting
- `output/reports/*.json` – master run metadata, per-keyword metrics, intent & market summaries.
- `output/reports/*.csv` – detailed keyword tables for spreadsheets or BI tools.
- `output/discovery/` – (optional) raw discovery exports by platform and timestamp.
- `output/reports/new_word_*` – Google Trends snapshots with detector annotations.
- `generated_websites/` – static site scaffolds, ready for deployment.

Each keyword in the JSON output now includes:
```json
{
  "keyword": "ai essay checker",
  "opportunity_score": 87.4,
  "volume_validation": {
    "status": "needs_review",
    "avg_7d": 4.2,
    "avg_30d": 8.7,
    "recent_threshold": 5.0,
    "notes": "below_volume_baseline"
  }
}
```
Use ` volume_validation_summary` to quickly triage which ideas require manual volume checks before investing further.

## Development & Testing
```bash
pytest                              # Run unit tests
pytest --maxfail=1 --disable-warnings
pytest --cov=src                    # Coverage run
```

Before pushing changes, ensure:
- New dependencies are captured in `requirements.txt`.
- Relevant docs in `docs/` are updated (API guides, SOPs, enhancement plans).
- CLI commands still succeed on the sample dataset (`data/keywords.csv`).

## Further Reading
- `docs/需求挖掘整理版.md` – end-to-end qualitative demand mining SOP.
- `docs/需求挖掘阶段增强待办.md` – roadmap for volume validation, Reddit structuring, and verification loops.
- `docs/google_trends_enhancement_plan.md` – plans for expanding seed pools and trend watchlists.
- `docs/API配置待办事项.md` – API setup & encryption reference.

*Items marked with an asterisk require API tokens or additional configuration before use.
