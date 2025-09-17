# Repository Guidelines

## Project Structure & Module Organization
Core code lives in `src/`, which is split by responsibility: `collectors/` for data ingestion, `demand_mining/` for scoring and insight engines, `pipeline/` for orchestration, `utils/` for shared helpers, and `website_builder/` for static output generation. `main.py` is the unified CLI entry point, while `run_lummstudio_spider.py` drives the standalone crawler. Configuration assets reside in `config/` (JSON, YAML, and encryption helpers), input samples in `data/`, documentation in `docs/`, and generated artifacts in `output/` or `generated_websites/`.

## Build, Test, and Development Commands
Set up dependencies with `pip install -r requirements.txt` inside an activated virtual env (`python -m venv .venv && .venv\Scripts\activate`). Run the integrated workflow through `python main.py --help` to explore options, or `python main.py --input data/keywords.csv` for a typical batch. Use `python run_lummstudio_spider.py` when iterating on the LummStudio spider. Before submitting work, execute `pytest` (or `pytest --maxfail=1 --disable-warnings`) and optionally `pytest --cov=src` for coverage insights.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation, descriptive snake_case for functions and variables, and PascalCase for classes. New modules should use type hints, docstrings, and explicit imports, mirroring existing managers such as `IntegratedDemandMiningManager`. Reuse the structured logging utilities in `src/utils/logger.py`, keep CLI messaging concise, and prefer UTF-8 source files.

## Testing Guidelines
Adopt pytest for all new code: colocate unit tests under `tests/` (create the directory if missing) or alongside the module in a `test_*\.py` file. Name tests after the behavior under scrutiny (`test_analyze_keywords_handles_empty_input`). Aim for meaningful fixture data in `data/` and keep coverage above 80% for core logic. Include regression tests when updating collectors or pipelines to guard against API drift.

## Commit & Pull Request Guidelines
Commits in this repository are brief, action-oriented statements (see `git log`), often in Chinese imperative mood. Follow that tone, start with a verb, and scope changes narrowly. Pull requests should explain the problem, summarize the solution, list relevant commands (`pytest`, `python main.py`), and attach sample output paths when behavior changes. Link to tracking issues where applicable and highlight configuration updates users must make locally.

## Configuration & Security Tips
Never commit real API keys or encrypted payloads; keep secrets in `.env` files ignored by Git. When editing configs in `config/`, document default placeholders and use `reencrypt_config.py` if you touch encrypted entries. Validate any crawler changes against proxy settings in `config/proxy_config.yaml`, and confirm generated reports land in the expected `output/reports` directory.
