# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Czech-language honeymoon-trip itinerary (1.–27. 5. 2026, 2 people, car + MSC Grandiosa cruise). The source material is handwritten Markdown organized by day; the tooling transforms it into several distribution formats (EPUB, MkDocs web, single-file HTML, NotebookLM-friendly flat files, and a Gemini-friendly single bundle).

**`dist/` is entirely generated — never edit files there, never commit it.** It is recreated by `preprocess.py` + `build.sh`.

## Commands

```bash
# Python deps (one-time)
pip install -r requirements.txt

# Regenerate enhanced markdown only (dist/individual, dist/bundle.md, dist/drive-flat)
python preprocess.py

# Full build pipeline (requires pandoc on PATH)
bash build.sh

# Tests (pytest)
pytest
pytest tests/test_preprocess.py::test_parse_day_extracts_number_from_nested_path  # single test

# Local MkDocs preview — preprocess must have run at least once
python -m mkdocs serve
```

`build.sh` runs `preprocess.py` first, then generates EPUB (pandoc), MkDocs site (`dist/web/`), offline zip (`dist/web.zip`), and single-file HTML (pandoc). `preprocess.py` deliberately cleans only `dist/individual/` and `dist/bundle.md` so EPUB/HTML/web artifacts from a previous `build.sh` run survive re-preprocessing.

## Content layout

Three phase directories + shared reference files at repo root:

| Path | Content |
|------|---------|
| `1-cesta-tam/den-NN/den-NN.md` | Days 1–11, outbound drive CZ→IT |
| `2-lod/den-NN/den-NN.md` + `2-lod/*.md` | Days 11–18 on MSC Grandiosa + shared ship docs (`lod-info.md`, `bary.md`, `stravovani.md`, `pristavy-logistika.md`, etc.) |
| `3-cesta-zpet/den-NN/den-NN.md` | Days 18–27, return drive CH→CZ |
| `README.md`, `baleni.md`, `checklist.md`, `finance.md`, `ubytovani.md` | Root reference docs (scope = whole trip) |

**Boundary days 11 and 18 exist twice** — day 11 appears in both `1-cesta-tam/` (final drive day, boarding) and `2-lod/` (first ship day); day 18 appears in both `2-lod/` (disembarkation) and `3-cesta-zpet/` (onward drive). `PHASE_DAYS` sets in `preprocess.py` encode this overlap, and `phase_of_day(day, current_phase)` prefers the caller's phase when a day belongs to two. Cross-phase `prev`/`next` nav links use `../../other-phase/den-NN/...` and are covered by the `test_render_cross_phase_*` tests — touching the nav logic without updating those tests will silently break the day 11 and day 18 transitions.

## preprocess.py — the main pipeline

Reads every `*.md` under the three phase dirs + root, then produces three outputs in `dist/`:

1. **`dist/individual/<phase>/den-NN/den-NN.md`** — same hierarchy as source, each file gains YAML frontmatter (title, source_path, phase, phase_number, date, day_number, day_of_week, prev, next, tags) and a breadcrumb blockquote with prev/next nav links. This is the `docs_dir` MkDocs reads from (`mkdocs.yml` → `docs_dir: dist/individual`).
2. **`dist/bundle.md`** — every enhanced file concatenated with `=== FILE: <relative/path> ===` separators. Consumed by Gemini Gems; the separator is load-bearing for the custom instructions in `docs/deploy-instructions.md`.
3. **`dist/drive-flat/NN-<phase_short>-<stem>-<descriptor>.md`** — flat list (no subdirs) with numeric prefixes encoding chronological order. Needed because NotebookLM shows source names as plain filenames with no folder context. Day-11 and day-18 files appear twice here (once per phase) because of the phase overlap.

Key functions (all in `preprocess.py`):
- `parse_day(path)` — extracts the `NN` from `den-NN` anywhere in a path
- `detect_phase(rel)` — returns phase metadata if the relative path starts with a phase dir
- `derive_meta(rel, raw)` — splits H1 from body, builds the frontmatter dict, adds heuristic tags
- `render(meta, body)` — emits the final enhanced file with frontmatter + breadcrumb + body
- `flatten_for_drive()` — walks `dist/individual/` in chronological-phase order to build `dist/drive-flat/`

Trip start date `2026-05-01` is hardcoded as `TRIP_START`; ISO dates are derived from `day_number`.

## Tests

`tests/test_preprocess.py` covers day/phase parsing, metadata derivation, render output shape (frontmatter + breadcrumb + nav), cross-phase link construction at day 11/18, and a full end-to-end run against `tests/fixtures/`. When changing preprocess behavior, run pytest — the tests are fast (<1s) and catch the non-obvious boundary-day bugs.

## Deployment

- **GitHub Pages** — `.github/workflows/pages.yml` runs `pip install -r requirements.txt`, then `python preprocess.py`, then `mkdocs build --site-dir _site`, and publishes `_site/`. Triggered on push to `main`/`master`. This is the only automated deploy; EPUB/HTML/drive-flat/bundle outputs are distributed manually per `docs/deploy-instructions.md` (Apple Books, NotebookLM, Gemini Gem, Obsidian).
- Local `build.sh` uses `dist/web` as MkDocs output (different from CI's `_site`) so everything lands under `dist/`.
