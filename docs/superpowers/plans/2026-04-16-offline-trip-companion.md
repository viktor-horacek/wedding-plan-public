# Offline & AI Companion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vygenerovat offline-first + Gemini-friendly konzumaci 27denního cestovního plánu ze ~40 markdown souborů, distribuovat na iPhone (Apple Books EPUB) a Samsung (Obsidian Android), napojit na Gemini NotebookLM + Roboti Gem, publikovat v novém public GitHub repu + GitHub Pages.

**Architecture:** Python preprocessing vygeneruje enhanced md s YAML frontmatter + breadcrumbs + bundle. Pandoc vygeneruje EPUB. MkDocs Material vygeneruje web (offline + GitHub Pages). Starý privátní repo se nahradí novým public repem bez PDF. PDF jde na Google Drive.

**Tech Stack:** Python 3.11+ (`python-frontmatter`, `pyyaml`, `pytest`), Pandoc 3.x, MkDocs Material, bash (git bash na Windows), GitHub Actions, Google Drive, NotebookLM, Gemini Gems.

**Spec:** `docs/superpowers/specs/2026-04-16-offline-trip-companion-design.md`

---

## Fáze execution v bite-sized taskách

```
Fáze 1: Tooling + Python TDD (Task 1-8)
  └─ Vyvinout preprocess.py unit-by-unit
       ↓
Fáze 2: Build pipeline (Task 9-11)
  └─ build.sh + mkdocs.yml + end-to-end test
       ↓
Fáze 3: Git migration (Task 12-17)
  └─ Audit, PDF → Drive, nový public repo, GH Pages
       ↓
Fáze 4: iPhone distribuce (Task 18-20)
  └─ EPUB, Notebooks fallback, web.zip fallback
       ↓
Fáze 5: Android distribuce (Task 21-22)
  └─ Obsidian + Markor fallback
       ↓
Fáze 6: Gemini setup (Task 23-26)
  └─ Privacy, Drive, NotebookLM, Roboti Gem
       ↓
Fáze 7: Acceptance test (Task 27-30)
  └─ Airplane mode oba telefony + Gemini online + docs
```

---

## File Structure

### Nové soubory (budou vytvořeny tímto plánem)

| Soubor | Odpovědnost |
|--------|-------------|
| `preprocess.py` | Čte md z repa, přidá YAML frontmatter + breadcrumbs, vygeneruje `dist/individual/` a `dist/bundle.md` |
| `tests/test_preprocess.py` | Pytest unit testy preprocess funkcí |
| `tests/fixtures/` | Ukázková md pro testy (den, shared soubor) |
| `build.sh` | Orchestruje preprocess + pandoc (EPUB) + mkdocs (web) + zip |
| `mkdocs.yml` | MkDocs Material config s offline plugin |
| `cover.jpg` | EPUB cover image (uživatel poskytne) |
| `.github/workflows/pages.yml` | Auto-deploy MkDocs → GitHub Pages |
| `.gitignore` | Ignorovat `dist/`, `*.pdf`, `__pycache__/`, `.pytest_cache/` |

### Modifikované soubory

| Soubor | Úprava |
|--------|--------|
| `ubytovani.md` | Doplnit chybějící rezervační údaje z PDF (Task 13) |

---

## Task 1: Instalace toolchainu

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Ověřit Python 3.11+**

Run:
```bash
python --version
```
Expected: `Python 3.11.x` nebo vyšší. Pokud ne → instalovat z python.org.

- [ ] **Step 2: Vytvořit `requirements.txt`**

```txt
python-frontmatter>=1.1.0
pyyaml>=6.0
pytest>=8.0
```

- [ ] **Step 3: Instalovat Python deps**

Run:
```bash
pip install -r requirements.txt
```
Expected: úspěšná instalace, žádné chyby.

- [ ] **Step 4: Instalovat Pandoc 3.x**

Run (PowerShell jako admin):
```powershell
choco install pandoc
```
Nebo stáhnout installer z https://pandoc.org/installing.html

Ověření:
```bash
pandoc --version
```
Expected: `pandoc 3.x.y` nebo vyšší.

- [ ] **Step 5: Instalovat MkDocs Material**

Run:
```bash
pip install mkdocs-material
```
Ověření:
```bash
mkdocs --version
```
Expected: `mkdocs, version 1.x`.

- [ ] **Step 6: Commit toolchain manifest**

```bash
git add requirements.txt
git commit -m "Add Python deps manifest for preprocessing toolchain"
```

---

## Task 2: Test infrastructure + `parse_day` + `iso_date`

**Files:**
- Create: `tests/__init__.py` (prázdný)
- Create: `tests/test_preprocess.py`
- Create: `preprocess.py`

- [ ] **Step 1: Vytvořit prázdný `tests/__init__.py`**

```python
```

- [ ] **Step 2: Napsat failing testy pro `parse_day` a `iso_date`**

`tests/test_preprocess.py`:
```python
from datetime import date
from pathlib import Path

from preprocess import parse_day, iso_date


def test_parse_day_extracts_number_from_nested_path():
    assert parse_day(Path("1-cesta-tam/den-05/den-05.md")) == 5


def test_parse_day_extracts_two_digit_day():
    assert parse_day(Path("3-cesta-zpet/den-27/den-27.md")) == 27


def test_parse_day_returns_none_for_non_day_file():
    assert parse_day(Path("ubytovani.md")) is None
    assert parse_day(Path("2-lod/lod-info.md")) is None


def test_iso_date_day_1_is_trip_start():
    assert iso_date(1) == date(2026, 5, 1)


def test_iso_date_day_15_is_palma():
    assert iso_date(15) == date(2026, 5, 15)


def test_iso_date_day_27_is_last():
    assert iso_date(27) == date(2026, 5, 27)
```

- [ ] **Step 3: Spustit testy → FAIL**

Run:
```bash
pytest tests/test_preprocess.py -v
```
Expected: `ModuleNotFoundError: No module named 'preprocess'`.

- [ ] **Step 4: Minimální implementace v `preprocess.py`**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from datetime import date, timedelta
from pathlib import Path

TRIP_START = date(2026, 5, 1)
DAY_RE = re.compile(r"den-(\d{2})")


def parse_day(p):
    m = DAY_RE.search(str(p))
    return int(m.group(1)) if m else None


def iso_date(n):
    return TRIP_START + timedelta(days=n - 1)
```

- [ ] **Step 5: Testy PASS**

Run:
```bash
pytest tests/test_preprocess.py -v
```
Expected: 6 passed.

- [ ] **Step 6: Commit**

```bash
git add tests/__init__.py tests/test_preprocess.py preprocess.py
git commit -m "Add parse_day and iso_date with unit tests"
```

---

## Task 3: `detect_phase`

**Files:**
- Modify: `tests/test_preprocess.py` (add tests)
- Modify: `preprocess.py` (add function)

- [ ] **Step 1: Failing testy pro `detect_phase`**

Přidat do `tests/test_preprocess.py`:
```python
from preprocess import detect_phase


def test_detect_phase_cesta_tam():
    result = detect_phase(Path("1-cesta-tam/den-05/den-05.md"))
    assert result == {"key": "1-cesta-tam", "number": 1, "label": "Cesta tam (Dny 1-11)"}


def test_detect_phase_lod():
    result = detect_phase(Path("2-lod/lod-info.md"))
    assert result == {"key": "2-lod", "number": 2, "label": "Plavba MSC Grandiosa (Dny 11-18)"}


def test_detect_phase_cesta_zpet():
    result = detect_phase(Path("3-cesta-zpet/den-20/den-20.md"))
    assert result["key"] == "3-cesta-zpet"
    assert result["number"] == 3


def test_detect_phase_shared_file_returns_none():
    assert detect_phase(Path("finance.md")) is None
    assert detect_phase(Path("ubytovani.md")) is None
```

- [ ] **Step 2: Spustit → 4 nové FAIL**

Run: `pytest tests/test_preprocess.py -v`
Expected: 4 new failures (`detect_phase` not defined).

- [ ] **Step 3: Implementace v `preprocess.py`**

Přidat po `iso_date`:
```python
PHASES = {
    "1-cesta-tam":  {"number": 1, "label": "Cesta tam (Dny 1-11)"},
    "2-lod":        {"number": 2, "label": "Plavba MSC Grandiosa (Dny 11-18)"},
    "3-cesta-zpet": {"number": 3, "label": "Cesta zpet (Dny 18-27)"},
}


def detect_phase(rel):
    parts = rel.parts
    if parts and parts[0] in PHASES:
        return {"key": parts[0], **PHASES[parts[0]]}
    return None
```

- [ ] **Step 4: Testy PASS**

Run: `pytest tests/test_preprocess.py -v`
Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/test_preprocess.py preprocess.py
git commit -m "Add detect_phase for 3-phase trip structure"
```

---

## Task 4: `split_h1`

**Files:**
- Modify: `tests/test_preprocess.py`
- Modify: `preprocess.py`

- [ ] **Step 1: Failing testy**

Přidat:
```python
from preprocess import split_h1


def test_split_h1_extracts_title_and_body():
    text = "# Den 5 – Úterý\n\nText\n\n## Sekce"
    title, body = split_h1(text)
    assert title == "Den 5 – Úterý"
    assert body == "Text\n\n## Sekce"


def test_split_h1_ignores_h2():
    text = "## Only subheading\n\nText"
    title, body = split_h1(text)
    assert title is None
    assert body == text


def test_split_h1_strips_leading_blank_lines():
    text = "\n\n# Title\n\nbody"
    title, body = split_h1(text)
    assert title == "Title"
    assert body == "body"
```

- [ ] **Step 2: Spustit → 3 FAIL**

Run: `pytest tests/test_preprocess.py -v`

- [ ] **Step 3: Implementace**

Přidat do `preprocess.py`:
```python
def split_h1(text):
    lines = text.splitlines()
    for i, l in enumerate(lines):
        s = l.strip()
        if s.startswith("# ") and not s.startswith("## "):
            return s[2:].strip(), "\n".join(lines[:i] + lines[i + 1:]).lstrip("\n")
    return None, text
```

- [ ] **Step 4: Testy PASS**

Run: `pytest tests/test_preprocess.py -v`
Expected: 13 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/test_preprocess.py preprocess.py
git commit -m "Add split_h1 for title extraction"
```

---

## Task 5: `derive_meta` (klíčová funkce)

**Files:**
- Modify: `tests/test_preprocess.py`
- Modify: `preprocess.py`

- [ ] **Step 1: Failing testy pro day file metadata**

Přidat:
```python
from preprocess import derive_meta


def test_derive_meta_day_file_extracts_metadata():
    rel = Path("1-cesta-tam/den-05/den-05.md")
    raw = "# Den 5 – Úterý 5. 5.: Prosecco Hills\n\nText body."
    meta, body = derive_meta(rel, raw)

    assert meta["title"] == "Den 5 – Úterý 5. 5.: Prosecco Hills"
    assert meta["source_path"] == "1-cesta-tam/den-05/den-05.md"
    assert meta["phase"] == "1-cesta-tam"
    assert meta["phase_number"] == 1
    assert meta["day_number"] == 5
    assert meta["date"] == "2026-05-05"
    assert meta["day_of_week"] == "utery"
    assert meta["prev"] == "den-04"
    assert meta["next"] == "den-06"
    assert body == "Text body."


def test_derive_meta_day_1_has_no_prev():
    rel = Path("1-cesta-tam/den-01/den-01.md")
    raw = "# Den 1\n\nbody"
    meta, _ = derive_meta(rel, raw)
    assert "prev" not in meta
    assert meta["next"] == "den-02"


def test_derive_meta_day_27_has_no_next():
    rel = Path("3-cesta-zpet/den-27/den-27.md")
    raw = "# Den 27\n\nbody"
    meta, _ = derive_meta(rel, raw)
    assert meta["prev"] == "den-26"
    assert "next" not in meta


def test_derive_meta_shared_file_no_day_keys():
    rel = Path("finance.md")
    raw = "# Finance\n\nPřehled."
    meta, body = derive_meta(rel, raw)
    assert meta["title"] == "Finance"
    assert meta["source_path"] == "finance.md"
    assert "day_number" not in meta
    assert "phase" not in meta
    assert body == "Přehled."


def test_derive_meta_tags_extracted_from_content():
    rel = Path("1-cesta-tam/den-05/den-05.md")
    raw = "# Den 5\n\nProsecco Hills, Michelin restaurace, lanovka CastelBrando."
    meta, _ = derive_meta(rel, raw)
    assert "prosecco" in meta["tags"]
    assert "michelin" in meta["tags"]
    assert "lanovka" in meta["tags"]


def test_derive_meta_fallback_title_from_filename():
    rel = Path("2-lod/bary.md")
    raw = "Žádný H1.\n\nText bez nadpisu."
    meta, _ = derive_meta(rel, raw)
    assert meta["title"] == "bary"
```

- [ ] **Step 2: Spustit → 6 FAIL**

Run: `pytest tests/test_preprocess.py -v`

- [ ] **Step 3: Implementace**

Přidat do `preprocess.py`:
```python
DAYS_CZ = ["pondeli", "utery", "streda", "ctvrtek", "patek", "sobota", "nedele"]


def derive_meta(rel, raw):
    h1, body = split_h1(raw)
    phase = detect_phase(rel)
    n = parse_day(rel)
    meta = {
        "title": h1 or rel.stem,
        "source_path": str(rel).replace("\\", "/"),
    }
    if phase:
        meta["phase"] = phase["key"]
        meta["phase_number"] = phase["number"]
    if n is not None:
        d = iso_date(n)
        meta["date"] = d.isoformat()
        meta["day_number"] = n
        meta["day_of_week"] = DAYS_CZ[d.weekday()]
        if n > 1:
            meta["prev"] = f"den-{n - 1:02d}"
        if n < 27:
            meta["next"] = f"den-{n + 1:02d}"
    low = raw.lower()
    tags = []
    for kw, tag in [
        ("prosecco", "prosecco"),
        ("msc grandiosa", "cruise"),
        ("lanovk", "lanovka"),
        ("sentiero", "hiking"),
        ("michelin", "michelin"),
        ("walk-in", "walk-in"),
    ]:
        if kw in low and tag not in tags:
            tags.append(tag)
    if tags:
        meta["tags"] = tags
    return meta, body
```

- [ ] **Step 4: Testy PASS**

Run: `pytest tests/test_preprocess.py -v`
Expected: 19 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/test_preprocess.py preprocess.py
git commit -m "Add derive_meta for per-file YAML frontmatter generation"
```

---

## Task 6: `render` (výstupní formát)

**Files:**
- Modify: `tests/test_preprocess.py`
- Modify: `preprocess.py`

- [ ] **Step 1: Failing testy pro render**

Přidat:
```python
from preprocess import render


def test_render_day_file_has_frontmatter_and_breadcrumbs():
    meta = {
        "title": "Den 5 – Úterý 5. 5.: Prosecco Hills",
        "source_path": "1-cesta-tam/den-05/den-05.md",
        "phase": "1-cesta-tam",
        "phase_number": 1,
        "day_number": 5,
        "date": "2026-05-05",
        "day_of_week": "utery",
        "prev": "den-04",
        "next": "den-06",
    }
    body = "Text body."
    out = render(meta, body)

    assert out.startswith("---\n")
    assert "title:" in out
    assert "day_number: 5" in out
    assert "\n---\n" in out  # frontmatter delimiter
    assert "> **Cesta:** Svatebni cesta 2026 > Cesta tam (Dny 1-11) > Den 5" in out
    assert "Predchozi:" in out
    assert "Nasledujici:" in out
    assert "# Den 5 – Úterý 5. 5.: Prosecco Hills" in out
    assert "Text body." in out


def test_render_shared_file_no_breadcrumb_nav():
    meta = {
        "title": "Finance",
        "source_path": "finance.md",
    }
    body = "Přehled."
    out = render(meta, body)
    assert "---\n" in out
    assert "# Finance" in out
    assert "Předchozí" not in out
    assert "Předchozí" not in out  # no nav for shared
    assert "Přehled." in out
```

- [ ] **Step 2: FAIL**

Run: `pytest tests/test_preprocess.py -v`

- [ ] **Step 3: Implementace**

Přidat `import yaml` na začátek `preprocess.py`, pak funkci:
```python
import yaml  # přidat mezi imports


def render(meta, body):
    phase = PHASES.get(meta.get("phase", ""))
    crumbs = ["Svatebni cesta 2026"]
    if phase:
        crumbs.append(phase["label"])
    if "day_number" in meta:
        d = iso_date(meta["day_number"])
        crumbs.append(f"Den {meta['day_number']} / {d.day}. {d.month}. {d.year}")
    short = meta["title"].split(":", 1)[-1].strip() if ":" in meta["title"] else meta["title"]
    crumbs.append(short)
    nav = []
    if meta.get("prev"):
        nav.append(f"**Predchozi:** [{meta['prev']}](../{meta['prev']}/{meta['prev']}.md)")
    if meta.get("next"):
        nav.append(f"**Nasledujici:** [{meta['next']}](../{meta['next']}/{meta['next']}.md)")
    fm = yaml.safe_dump(meta, allow_unicode=True, sort_keys=False).strip()
    out = [
        f"---\n{fm}\n---",
        "",
        f"> **Cesta:** {' > '.join(crumbs)}",
    ]
    if nav:
        out.append(f"> {' - '.join(nav)}")
    out += ["", f"# {meta['title']}", "", body.strip(), ""]
    return "\n".join(out)
```

- [ ] **Step 4: PASS**

Run: `pytest tests/test_preprocess.py -v`
Expected: 21 passed.

- [ ] **Step 5: Commit**

```bash
git add tests/test_preprocess.py preprocess.py
git commit -m "Add render function for enhanced md output"
```

---

## Task 7: `main()` integrace + bundle

**Files:**
- Modify: `tests/test_preprocess.py`
- Modify: `preprocess.py`
- Create: `tests/fixtures/1-cesta-tam/den-01/den-01.md`
- Create: `tests/fixtures/finance.md`

- [ ] **Step 1: Testovací fixture soubory**

`tests/fixtures/1-cesta-tam/den-01/den-01.md`:
```markdown
# Den 1 – Pátek 1. 5.: Test Day

Body of day 1.
```

`tests/fixtures/finance.md`:
```markdown
# Finance – test

Test přehled.
```

- [ ] **Step 2: Failing integration test**

Přidat:
```python
import tempfile
import shutil
from preprocess import main


def test_main_generates_individual_and_bundle(monkeypatch, tmp_path):
    # Copy fixtures to temp dir
    fixtures = Path("tests/fixtures")
    for src in fixtures.rglob("*.md"):
        dst = tmp_path / src.relative_to(fixtures)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)

    monkeypatch.setattr("preprocess.ROOT", tmp_path)
    monkeypatch.setattr("preprocess.DIST", tmp_path / "dist")
    monkeypatch.setattr("preprocess.INDIVIDUAL", tmp_path / "dist" / "individual")
    monkeypatch.setattr("preprocess.BUNDLE", tmp_path / "dist" / "bundle.md")

    main()

    # Verify individual output
    individual_day = tmp_path / "dist" / "individual" / "1-cesta-tam" / "den-01" / "den-01.md"
    assert individual_day.exists()
    content = individual_day.read_text(encoding="utf-8")
    assert "day_number: 1" in content
    assert "> **Cesta:**" in content

    # Verify bundle
    bundle = tmp_path / "dist" / "bundle.md"
    assert bundle.exists()
    bundle_content = bundle.read_text(encoding="utf-8")
    assert "=== FILE: 1-cesta-tam/den-01/den-01.md ===" in bundle_content
    assert "=== FILE: finance.md ===" in bundle_content
```

- [ ] **Step 3: FAIL**

Run: `pytest tests/test_preprocess.py::test_main_generates_individual_and_bundle -v`

- [ ] **Step 4: Implementace `main()`**

Přidat `import shutil` a `import frontmatter` a konstanty na začátek `preprocess.py`:
```python
import shutil
import frontmatter

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
INDIVIDUAL = DIST / "individual"
BUNDLE = DIST / "bundle.md"
```

Přidat `main()`:
```python
def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    INDIVIDUAL.mkdir(parents=True)
    files = []
    for ph in PHASES:
        p = ROOT / ph
        if p.is_dir():
            files += sorted(p.rglob("*.md"))
    files += sorted(ROOT.glob("*.md"))
    bundle = [f"# Svatebni cesta 2026 - Bundle\n\nGenerated: {date.today().isoformat()}\n"]
    for src in files:
        rel = src.relative_to(ROOT)
        raw = frontmatter.loads(src.read_text(encoding="utf-8")).content
        meta, body = derive_meta(rel, raw)
        enhanced = render(meta, body)
        out = INDIVIDUAL / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(enhanced, encoding="utf-8")
        path_norm = str(rel).replace("\\", "/")
        bundle.append(f"\n\n=== FILE: {path_norm} ===\n\n{enhanced}")
    BUNDLE.write_text("\n".join(bundle), encoding="utf-8")
    print(f"OK: {len(list(INDIVIDUAL.rglob('*.md')))} files -> {INDIVIDUAL}")
    print(f"OK: bundle -> {BUNDLE}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: PASS**

Run: `pytest tests/test_preprocess.py -v`
Expected: 22 passed.

- [ ] **Step 6: Commit**

```bash
git add tests/fixtures tests/test_preprocess.py preprocess.py
git commit -m "Add main() orchestrator + bundle generation"
```

---

## Task 8: Reálný dry-run na existujících md

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Vytvořit/doplnit `.gitignore`**

```
dist/
*.pdf
__pycache__/
.pytest_cache/
*.pyc
.venv/
```

- [ ] **Step 2: Spustit preprocess na reálném repu**

Run:
```bash
python preprocess.py
```
Expected output:
```
OK: 40+ files -> .../dist/individual
OK: bundle -> .../dist/bundle.md
```

- [ ] **Step 3: Ověřit namátkově 3 soubory**

Run:
```bash
head -30 dist/individual/README.md
head -30 dist/individual/1-cesta-tam/den-05/den-05.md
head -30 dist/individual/finance.md
```

Každý by měl mít:
- YAML frontmatter `---`
- `> **Cesta:**` breadcrumb
- Přesný nadpis a obsah původního souboru

- [ ] **Step 4: Velikost bundle**

Run:
```bash
wc -c dist/bundle.md
wc -l dist/bundle.md
```
Expected: ~300-700 kB, ~10k-20k řádků.

- [ ] **Step 5: Ověřit že `=== FILE:` separátory fungují**

Run:
```bash
grep -c "=== FILE:" dist/bundle.md
```
Expected: počet md souborů v repu (cca 40+).

- [ ] **Step 6: Commit**

```bash
git add .gitignore
git commit -m "Add .gitignore for build artifacts and Python cache"
```

---

## Task 9: `build.sh`

**Files:**
- Create: `build.sh`
- Create: `cover.jpg` (uživatel poskytne, nebo generujeme placeholder)
- Create: `styles.css`

- [ ] **Step 1: Vytvořit minimální `cover.jpg`**

Pokud uživatel nemá cover:
```bash
# Fallback: jednoduché barevné JPG 1600×2400
# (použít online generátor, Canva, nebo pass --without-cover-image v build.sh)
```

Nebo v `build.sh` vynechat `--epub-cover-image` pokud `cover.jpg` neexistuje.

- [ ] **Step 2: Vytvořit `styles.css` pro HTML výstup**

```css
body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    max-width: 780px;
    margin: 2rem auto;
    padding: 0 1rem;
    line-height: 1.6;
    color: #222;
}
h1, h2, h3 { color: #1a3e6f; }
table { border-collapse: collapse; margin: 1rem 0; }
th, td { border: 1px solid #ccc; padding: 0.4rem 0.8rem; text-align: left; }
th { background: #f0f4f8; }
blockquote {
    border-left: 3px solid #8ab4d6;
    padding-left: 1rem;
    margin-left: 0;
    color: #555;
}
```

- [ ] **Step 3: Vytvořit `build.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail

echo "==> Preprocessing markdown"
python preprocess.py

echo "==> Generating EPUB"
EPUB_ARGS="--toc --toc-depth=2 --split-level=1 --metadata title=Svatební cesta 2026 --metadata lang=cs"
if [ -f cover.jpg ]; then
  EPUB_ARGS="$EPUB_ARGS --epub-cover-image=cover.jpg"
fi
pandoc $EPUB_ARGS -o dist/svatebni-cesta.epub dist/bundle.md

echo "==> Generating MkDocs web"
mkdocs build --clean --site-dir dist/web

echo "==> Zipping web for offline"
(cd dist && zip -rq web.zip web)

echo "==> Generating single-file HTML"
pandoc --toc --toc-depth=3 --standalone --embed-resources \
  --metadata title="Svatební cesta 2026" \
  --css styles.css \
  -o dist/svatebni-cesta.html \
  dist/bundle.md

echo ""
echo "==> Výstupy v dist/:"
ls -lh dist/*.epub dist/*.html dist/web.zip
echo ""
echo "  - dist/svatebni-cesta.epub     → Apple Books (iPhone)"
echo "  - dist/svatebni-cesta.html     → single-file HTML fallback"
echo "  - dist/web.zip                 → offline web ZIP"
echo "  - dist/web/                    → MkDocs výstup (pro GH Pages)"
echo "  - dist/bundle.md               → single-file md (pro Roboti Gem)"
echo "  - dist/individual/*.md         → 40 md pro NotebookLM (nahrát do Drive)"
```

- [ ] **Step 4: Commit**

```bash
git add build.sh styles.css
git commit -m "Add build.sh pipeline (preprocess + EPUB + MkDocs + zip + HTML)"
```

---

## Task 10: `mkdocs.yml`

**Files:**
- Create: `mkdocs.yml`

- [ ] **Step 1: Vytvořit `mkdocs.yml`**

Minimální varianta s auto-nav (MkDocs vygeneruje nav ze struktury):
```yaml
site_name: Svatební cesta 2026
site_description: 27denní itinerář honeymoon trip (auto + MSC Grandiosa)
docs_dir: .
site_dir: dist/web
use_directory_urls: true

theme:
  name: material
  language: cs
  features:
    - navigation.instant
    - navigation.tracking
    - navigation.tabs
    - navigation.sections
    - navigation.indexes
    - toc.integrate
    - search.suggest
    - search.highlight
    - content.code.copy
  palette:
    - scheme: default
      primary: blue
      accent: teal

plugins:
  - search
  - offline

markdown_extensions:
  - toc:
      permalink: true
  - admonition
  - tables
  - pymdownx.highlight
  - pymdownx.superfences
  - attr_list
  - md_in_html
```

- [ ] **Step 2: Exclude `dist/`, `docs/superpowers/`, `tests/` z docs**

Přidat do `mkdocs.yml`:
```yaml
exclude_docs: |
  dist/
  docs/
  tests/
  preprocess.py
  build.sh
  mkdocs.yml
  requirements.txt
  node_modules/
  .github/
```

- [ ] **Step 3: Test build**

Run:
```bash
mkdocs build --clean --site-dir dist/web
```
Expected: `INFO - The following pages exist in the docs directory, but are not included in the "nav" configuration:` (to je OK), `INFO - Documentation built in X seconds`.

- [ ] **Step 4: Otevřít lokálně pro ověření**

Run:
```bash
mkdocs serve
```
V browseru: http://127.0.0.1:8000/

Test:
- Navigace mezi dny funguje
- Search najde slovo "Prosecco"
- Relativní odkazy mezi md klikatelné

Ukončit: Ctrl+C.

- [ ] **Step 5: Commit**

```bash
git add mkdocs.yml
git commit -m "Add mkdocs.yml with Material theme and offline plugin"
```

---

## Task 11: End-to-end build test

**Files:** (žádné nové, jen ověření)

- [ ] **Step 1: Full build**

Run:
```bash
bash build.sh
```
Expected: 4 výstupy v `dist/` bez chyb.

- [ ] **Step 2: Ověřit EPUB**

Run:
```bash
ls -lh dist/svatebni-cesta.epub
```
Expected: soubor existuje, ~200-500 kB.

Otevřít v Calibre, Apple Books, nebo online EPUB vieweru (https://epubreader.online). Ověřit:
- TOC má 27 dní + shared soubory
- Nadpisy jsou čitelné
- Obsah jednotlivých dnů odpovídá md

- [ ] **Step 3: Ověřit single-file HTML**

Run:
```bash
start dist/svatebni-cesta.html  # Windows
```
Expected: otevře se v browseru, TOC nahoře, všechny dny, klikatelné kotvy.

- [ ] **Step 4: Ověřit web.zip**

```bash
mkdir /tmp/web-test
cd /tmp/web-test
unzip -q D:/sources/svatební-cesta/dist/web.zip
start web/index.html
```
Expected: MkDocs web se otevře lokálně, search funguje offline (klíč `offline plugin`).

- [ ] **Step 5: Ověřit bundle.md velikost**

Run:
```bash
wc -l dist/bundle.md
grep -c "=== FILE:" dist/bundle.md
```
Expected: 10-20k řádků, ~40+ FILE separátorů.

- [ ] **Step 6: Commit testovací checkpoint (dokumentace v README)**

Pokud chceš – ale jen pokud se něco přidalo. Jinak přeskočit.

---

## Task 12: Audit md na citlivé údaje

**Files:** (žádné nové, jen čtení)

- [ ] **Step 1: Grep na čísla karet**

Run:
```bash
grep -rnE '\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b' *.md */**/*.md
```
Expected: žádný hit. Pokud ano → ručně sanitize.

- [ ] **Step 2: Grep na klíčová slova**

Run:
```bash
grep -rinE '(CVV|CVC|PIN|IBAN|SWIFT|password|heslo)' *.md */**/*.md
```
Expected: žádný hit (nebo jen kontextové zmínky typu "PIN bezkontaktně" v obsahu, ne reálné hodnoty).

- [ ] **Step 3: Ruční review citlivých souborů**

Přečíst:
- `ubytovani.md`
- `finance.md`
- `checklist.md`

Hledat: jména hostů (OK, neuložené jako lekované), čísla účtů, platební detaily, osobní identifikační údaje.

- [ ] **Step 4: Pokud něco nalezeno → sanitize commit**

```bash
# Po ruční úpravě:
git add ubytovani.md finance.md
git commit -m "Sanitize sensitive details from reservation docs"
```

- [ ] **Step 5: Pokud nic nalezeno → zaznamenat ve spec**

Poznámka: "Audit proveden YYYY-MM-DD, žádné citlivé údaje nalezené v md souborech."

---

## Task 13: Extrakce rezervačních údajů z PDF do `ubytovani.md`

**Files:**
- Modify: `ubytovani.md`

- [ ] **Step 1: Projít 22 PDF v `1-cesta-tam/den-*/*.pdf` a `3-cesta-zpet/den-*/*.pdf`**

Otevřít každý PDF a zaznamenat:
- Jméno ubytování (už asi v ubytovani.md je)
- **Rezervační číslo / booking reference**
- **Check-in čas**
- **Check-out čas**
- **Adresa** (pokud chybí)
- **Kontakt na majitele** (email, ne telefon – viz memory rule)
- **Částka zaplaceno** (pokud relevantní pro finance.md)

- [ ] **Step 2: Doplnit do `ubytovani.md`**

Pro každou rezervaci přidat/ověřit sekci:
```markdown
### Den N – Název ubytování

- **Adresa:** ...
- **Rezervační č.:** ...
- **Check-in:** 15:00 (po předchozím kontaktu emailem)
- **Check-out:** 10:00
- **Kontakt:** email@example.com
- **Zaplaceno:** X EUR (Y. Y. 202Y přes Booking / přímý převod)
```

- [ ] **Step 3: Commit**

```bash
git add ubytovani.md
git commit -m "Extract reservation details from PDFs into ubytovani.md"
```

---

## Task 14: PDF → Google Drive

**Files:** (externí, Drive)

- [ ] **Step 1: Vytvořit Drive složku**

V Google Drive (drive.google.com):
- New → Folder → název `svatebni-cesta-PDF`
- (Optional) Share → Anyone with link NE, radši ponechat private

- [ ] **Step 2: Upload 22 PDF**

Upload všech PDF z:
- `1-cesta-tam/den-01/*.pdf` (2)
- `1-cesta-tam/den-02/*.pdf` (2)
- `1-cesta-tam/den-03/*.pdf` (2)
- `1-cesta-tam/den-06/*.pdf` (2)
- `1-cesta-tam/den-07/*.pdf` (2)
- `1-cesta-tam/den-09/*.pdf` (2)
- `3-cesta-zpet/den-18/*.pdf` (2)
- `3-cesta-zpet/den-20/*.pdf` (2)
- `3-cesta-zpet/den-24/*.pdf` (2)
- `3-cesta-zpet/den-25/*.pdf` (2)
- `3-cesta-zpet/den-26/*.pdf` (2)

- [ ] **Step 3: Ověřit přístup přes Drive app na iPhone i Samsungu**

Oba telefony: otevřít Google Drive app, najít `svatebni-cesta-PDF/`, tap na libovolný PDF → ověřit že se stáhne/otevře.

Na iPhone: po otevření PDF → Share → Save to Files (pro offline cache).
Na Samsungu: Drive má "Make available offline" per file.

- [ ] **Step 4: Smazat PDF z pracovní kopie repa**

Run:
```bash
find 1-cesta-tam 3-cesta-zpet -name '*.pdf' -delete
```

Nebo ručně:
```bash
rm 1-cesta-tam/den-*/*.pdf
rm 3-cesta-zpet/den-*/*.pdf
```

Ověřit:
```bash
find . -name '*.pdf'
```
Expected: empty.

**DŮLEŽITÉ: NEKOMITOVAT zatím do privátního repa.** PDF zůstanou v git history. Cleanup commit uděláme v novém public repu (Task 15).

---

## Task 15: Nový public repo

**Files:** (jiný adresář)

- [ ] **Step 1: Vytvořit prázdný GitHub repo**

Webově na https://github.com/new:
- Name: `wedding-plan-public`
- Description: "Svatební cesta 2026 – 27denní itinerář"
- Visibility: **Public**
- Nezaškrtávat README / .gitignore / license (uděláme lokálně)
- Create repository

Nebo CLI:
```bash
gh repo create wedding-plan-public --public --description "Svatební cesta 2026 – 27denní itinerář"
```

- [ ] **Step 2: Vytvořit lokální pracovní adresář**

Run:
```bash
cd /d/sources
cp -r svatební-cesta wedding-plan-public
cd wedding-plan-public
```

- [ ] **Step 3: Odstranit git metadata a PDF**

Run:
```bash
rm -rf .git
find . -name '*.pdf' -delete
# Ověřit:
find . -name '*.pdf'
```
Expected: empty.

- [ ] **Step 4: Init nový git repo**

Run:
```bash
git init -b main
git add .
git status
```
Ověřit že se nic PDF nepřipojilo.

- [ ] **Step 5: Initial commit**

Run:
```bash
git commit -m "Initial public release of wedding trip plan"
```

- [ ] **Step 6: Push na GitHub**

Run:
```bash
git remote add origin git@github.com:viktor-horacek/wedding-plan-public.git
git push -u origin main
```

- [ ] **Step 7: Ověřit na GitHub webu**

https://github.com/viktor-horacek/wedding-plan-public – měl by být vidět README, struktura složek, žádné PDF.

---

## Task 16: GitHub Actions + Pages

**Files:**
- Create: `.github/workflows/pages.yml`

- [ ] **Step 1: Vytvořit Actions workflow**

V `wedding-plan-public/.github/workflows/pages.yml`:
```yaml
name: Deploy MkDocs to GitHub Pages
on:
  push:
    branches: [main]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install mkdocs-material
      - run: mkdocs build --clean --site-dir _site
      - uses: actions/upload-pages-artifact@v3
        with:
          path: _site
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Commit + push**

Run:
```bash
git add .github/workflows/pages.yml
git commit -m "Add GitHub Actions for MkDocs Pages deploy"
git push
```

- [ ] **Step 3: Zapnout GitHub Pages**

Web: https://github.com/viktor-horacek/wedding-plan-public/settings/pages
- Source: GitHub Actions
- Save.

- [ ] **Step 4: Sledovat Action build**

Web: https://github.com/viktor-horacek/wedding-plan-public/actions
- První run by měl projít ~1-2 min.
- Pokud fail → číst log, opravit, push znovu.

- [ ] **Step 5: Ověřit nasazený web**

URL: `https://viktor-horacek.github.io/wedding-plan-public/`

Test:
- Načte se MkDocs Material s "Svatební cesta 2026"
- Navigace mezi dny funguje
- Search najde "Prosecco"

---

## Task 17: Archive starý privátní repo

- [ ] **Step 1: GitHub UI**

https://github.com/viktor-horacek/wedding-plan/settings

- Scroll úplně dolů → "Danger Zone" → "Archive this repository"
- Potvrdit.

- [ ] **Step 2: Ověřit archivovaný stav**

Repo page by měla mít žlutý banner "This repository has been archived..."

**Memo:** PDF zůstávají v git history archivovaného privátního repa. Přístup má jen vlastník (ty). Žádná akce dál není potřeba.

---

## Task 18: iPhone – EPUB v Apple Books (primární)

- [ ] **Step 1: Rebuild, ujisti se že EPUB je čerstvý**

Run:
```bash
cd /d/sources/svatební-cesta  # nebo wedding-plan-public
bash build.sh
```

- [ ] **Step 2: Upload EPUB do iCloud Drive**

Buď:
- Přes Finder / File Explorer: zkopírovat `dist/svatebni-cesta.epub` do složky iCloud Drive na PC (`C:\Users\zarco\iCloud Drive\`)
- Nebo upload přes iCloud.com

- [ ] **Step 3: Počkat na sync na iPhone**

iPhone Files app → iCloud Drive → ověřit že `svatebni-cesta.epub` je vidět.

- [ ] **Step 4: Otevřít v Apple Books**

Files app → tap na EPUB → Share → Open in Books.

V Books Library by se měla objevit kniha.

- [ ] **Step 5: VoiceOver test – rotor navigace**

iPhone → Settings → Accessibility → VoiceOver → ON (nebo triple-click Home/Side)

V Books otevřít knihu:
- Otočit 2 prsty (rotor) → přepnout na "Headings"
- Swipe down → skáče po H1 (Den 1, Den 2, ...)
- Swipe right → čte obsah

- [ ] **Step 6: TOC test**

V Books:
- Tap na Menu (vlevo nahoře) → Table of Contents
- Swipe VoiceOverem mezi kapitolami
- Double-tap "Den 15" → skočí tam

- [ ] **Step 7: Letadlový režim test**

Zapnout letadlový režim → otevřít Books → EPUB funguje 100% offline.

---

## Task 19: iPhone fallback – Notebooks

- [ ] **Step 1: Install Notebooks**

iPhone → App Store → "Notebooks – Write and Organize" (by Alfons Schmid) → Install (free).

- [ ] **Step 2: Upload enhanced md do iCloud**

Na PC: zkopírovat `dist/individual/` do `iCloud Drive/svatebni-cesta-md/`.

Struktura by měla být:
```
svatebni-cesta-md/
├── README.md
├── 1-cesta-tam/den-01/den-01.md
├── 2-lod/lod-info.md
└── ...
```

- [ ] **Step 3: Otevřít v Notebooks**

iPhone → Notebooks → Settings (gear) → iCloud → Enable → vybrat `svatebni-cesta-md` složku.

- [ ] **Step 4: Test klikatelných linků**

V Notebooks otevřít README.md → tap na link "den-05" → ověřit že se otevře cílový soubor.

- [ ] **Step 5: VoiceOver test v Notebooks**

Zapnout VoiceOver → otevřít den-05 v Preview mode → swipe right → čte obsah.

**Pokud preview mode má VoiceOver bugy s nadpisy** (viz spec) → přepnout na Editor mode, nebo použít fallback 3 (web.zip + Safari).

---

## Task 20: iPhone fallback 2 – `web.zip` v Safari

- [ ] **Step 1: Upload `dist/web.zip` do iCloud Drive**

Z PC: kopírovat `dist/web.zip` do `iCloud Drive/`.

- [ ] **Step 2: Extrahovat na iPhone**

iPhone Files app → iCloud Drive → `web.zip` → tap → extract.
Vznikne složka `web/`.

- [ ] **Step 3: Otevřít v Safari**

Files → web/ → tap na `index.html` → "Open in..." → Safari.

Safari otevře MkDocs web z `file://` URL.

- [ ] **Step 4: Ověřit navigaci a klikatelné linky**

Nav funguje, search fallback pro offline je přes offline plugin.

- [ ] **Step 5: Přidat hlavní stránku do Reading List**

Safari → Share → Add to Reading List (pro offline cache).

---

## Task 21: Samsung – Obsidian Android + git sync (primární)

- [ ] **Step 1: Install Obsidian Android**

Google Play → "Obsidian" → Install (free).

- [ ] **Step 2: Vytvořit vault**

Obsidian Android: Create new vault → name `svatebni-cesta`, lokální storage.

- [ ] **Step 3: Enable Community Plugins**

Settings → Community plugins → Turn on community plugins → Browse → hledat "Obsidian Git" → Install → Enable.

- [ ] **Step 4: Konfigurovat Git plugin**

Obsidian Git settings:
- Remote URL: `https://github.com/viktor-horacek/wedding-plan-public.git`
- Branch: `main`
- Author name: `Viktor Horáček`

- [ ] **Step 5: Clone repo do vaultu**

V Obsidian Git: Pull (nebo první setup vyžaduje "Clone").

Po dokončení: vault se naplní md soubory z repa.

- [ ] **Step 6: Nastavit Reading view jako default**

Settings → Editor → Default view for new tabs: **Reading view**.

- [ ] **Step 7: Test**

- Otevřít README.md → tap na link "den-01" → ověřit že se otevře
- Back gesture (swipe zleva) → vrátí na README
- Command palette: `Ctrl+P` ekvivalent (tap na menu) → Fulltext search "Prosecco"

- [ ] **Step 8: Letadlový režim test**

Airplane mode ON → Obsidian stále funguje (vault je lokální).

---

## Task 22: Samsung fallback – Markor

- [ ] **Step 1: Install Markor**

F-Droid: https://f-droid.org/packages/net.gsantner.markor/ → Install.
Nebo Google Play: Markor → Install.

- [ ] **Step 2: Stáhnout `dist/web.zip`**

Přes USB kabel z PC kopírovat `dist/web.zip` do `/Download/` na Samsungu.

- [ ] **Step 3: Extrahovat**

V Samsung Files app: tap na `web.zip` → Extract → vytvoří se `/Download/web/`.

- [ ] **Step 4: Otevřít v Markor**

Markor → Open folder → `/Download/web/` → tap na `index.html`.

(Alternativně: otevřít přímo md soubory z `/Download/svatebni-cesta-md/` pokud je tam)

- [ ] **Step 5: Test**

Otevřít 2-3 md soubory, ověřit čitelnost.

---

## Task 23: Gemini privacy settings

- [ ] **Step 1: Vypnout tréning dat**

Web: https://myaccount.google.com/activitycontrols
- Gemini Apps Activity → **OFF**
- Personal Intelligence (pokud je v regionu) → dle preference.

- [ ] **Step 2: Ověřit na iPhone Gemini appce**

Gemini iOS app → profile → Privacy → ověřit že "Activity" je OFF.

---

## Task 24: Google Drive upload md + bundle

- [ ] **Step 1: Vytvořit Drive složky**

- `svatebni-cesta-md-enhanced/` (pro NotebookLM)
- `svatebni-cesta-bundle/` (pro Roboti Gem)

- [ ] **Step 2: Přejmenovat individual soubory s prefixy**

Vytvořit PowerShell skript `prefix.ps1` v `dist/`:
```powershell
$prefix = 1
Get-ChildItem -Recurse -Filter *.md dist/individual/1-cesta-tam |
  Sort-Object FullName |
  ForEach-Object {
    $new = "dist/drive-ready/{0:D2}-{1}" -f $prefix, $_.Name
    New-Item -ItemType Directory -Path (Split-Path $new) -Force | Out-Null
    Copy-Item $_.FullName $new
    $prefix++
  }
# Opakovat pro 2-lod a 3-cesta-zpet a root soubory
```

Nebo prostě ručně – u 40 souborů to zabere 10 minut.

Cílová jmenná konvence:
```
01-den-01.md
02-den-02.md
...
11-den-11.md
12-lod-info.md
13-bary.md
14-stravovani.md
...
40-ubytovani.md
41-finance.md
42-checklist.md
43-baleni.md
```

- [ ] **Step 3: Upload všech 40 prefixovaných md do `svatebni-cesta-md-enhanced/`**

Drive web UI: drag & drop.

- [ ] **Step 4: Upload `dist/bundle.md` do `svatebni-cesta-bundle/`**

Drag & drop jednoho souboru.

---

## Task 25: NotebookLM notebook + share

- [ ] **Step 1: Create Notebook**

Web: https://notebooklm.google.com → **Create new notebook** → název `Svatební cesta 2026`.

- [ ] **Step 2: Add sources z Drive**

- Add source → Google Drive → vybrat všech 40 md z `svatebni-cesta-md-enhanced/`
- Počkat na indexaci (~1-2 min).

- [ ] **Step 3: Ověřit že všechny zdroje načteny**

V seznamu sources by mělo být 40 souborů s prefixy v pořadí.

- [ ] **Step 4: Vložit custom instructions**

Settings (gear) → Custom instructions → paste prompt ze sekce 7 spec dokumentu:
```
Jsi asistent pro svatební cestu 1.–27. 5. 2026 ...
(celý prompt ze spec sekce 7)
```

- [ ] **Step 5: Test 5 dotazy (acceptance)**

Viz Task 29.

- [ ] **Step 6: Share**

Share button (vpravo nahoře) → "Anyone with link" → Viewer role → Copy link.

- [ ] **Step 7: Poslat link partnerce**

iMessage / SMS / email.

- [ ] **Step 8: iOS NotebookLM app**

Oba telefony: App Store → NotebookLM → Install.
Otevřít link z iMessage → otevře se v app.

---

## Task 26: Roboti Gem + share

- [ ] **Step 1: Create Gem**

Web: https://gemini.google.com → klik na Gems → **Create Gem** → název `Svatební cesta 2026`.

- [ ] **Step 2: Instructions**

Paste prompt ze sekce 7 spec dokumentu.

- [ ] **Step 3: Knowledge**

Knowledge section → Upload file → vybrat `dist/bundle.md` z PC.

(Alternativně: `Add file` → Drive → vybrat bundle z `svatebni-cesta-bundle/`)

- [ ] **Step 4: Save Gem**

- [ ] **Step 5: Test dotaz**

"Co máme 15. den odpoledne?" → Gem by měl odpovědět z bundle s citací na Den 15.

- [ ] **Step 6: Share Gem**

Share → Copy link → poslat partnerce.

- [ ] **Step 7: Test v iOS Gemini app**

Oba telefony: otevřít Gemini app → My Gems → otevřít "Svatební cesta" → ptát se.

---

## Task 27: Airplane mode test – iPhone

**Datum: 28. nebo 29. 4. 2026 (2-3 dny před odjezdem)**

- [ ] **Step 1: Letadlový režim ON**

Pull down Control Center → Airplane mode.

- [ ] **Step 2: Apple Books scénáře**

- [ ] Najdi Den 5 přes TOC
- [ ] Čti "Časová osa" s VoiceOver rotor (Headings)
- [ ] Najdi "Palma" ve fulltext search (pokud Books má) nebo ve VoiceOver rotor (Links)
- [ ] Cross-reference: najdi odkaz v Den 5 na jiný den a pokus se skočit

- [ ] **Step 3: Notebooks fallback scénáře (pokud Books selže)**

- [ ] Otevři README → kliknutí na link na Den 10
- [ ] Otevři finance.md → čti tabulku

- [ ] **Step 4: Web.zip fallback scénáře (pokud Notebooks selže)**

- [ ] Files → web/index.html → Safari
- [ ] Naviguj na Den 20

- [ ] **Step 5: Pokud všechno selže, eskalace**

Přítelkyně musí mít alespoň jednu cestu, jak se dostat k plánu offline. Pokud žádná nefunguje, řešení:
- Jedno řešení je 100% jisté = tištěný itinerář (A4 print z `dist/svatebni-cesta.html`), vzít jako "ultimate backup"
- Nebo naplánovat workaround přes partnera (který má Obsidian Android)

---

## Task 28: Airplane mode test – Samsung

- [ ] **Step 1: Letadlový režim ON**

- [ ] **Step 2: Obsidian scénáře**

- [ ] Otevři README.md → klik na Den 10 → Den 10 se otevře
- [ ] Back button → vrátí na README
- [ ] Search → "Prosecco" → list výsledků
- [ ] Otevři finance.md → tabulka se renderuje

- [ ] **Step 3: Markor fallback scénáře**

- [ ] Markor → /Download/svatebni-cesta-md/1-cesta-tam/den-05/den-05.md → otevřít preview

---

## Task 29: Gemini online test (5 testovacích dotazů)

- [ ] **Step 1: Letadlový režim OFF, iPhone Gemini app**

- [ ] **Step 2: Test NotebookLM**

Otevřít sdílený notebook → zadat 5 dotazů postupně:

- [ ] **Dotaz 1 (lookup):** "Kolik stojí vstup do CastelBrando v Den 5?"
  Expected: odpověď s citací na den-05.md → sekce Časová osa.
- [ ] **Dotaz 2 (syntéza):** "Kolik celkem utratíme za parkování za 27 dní?"
  Expected: součet napříč zdroji (může být méně přesné než Claude).
- [ ] **Dotaz 3 (cross-reference):** "Co vzít do batohu na Den 8 na Monte Baldo?"
  Expected: kombinace z `baleni.md` a `den-08.md`.
- [ ] **Dotaz 4 (web search):** "Jaké počasí bude v Palmě 15. května 2026?"
  Expected: NotebookLM nemá web search → přepnout na Roboti Gem v Gemini appce.
- [ ] **Dotaz 5 (fallback plán):** "Co je plán B, když Monte Baldo lanovka nejede?"
  Expected: z den-08.md "Záložní plán".

- [ ] **Step 3: Test Roboti Gem**

Gemini app → My Gems → "Svatební cesta" → stejné dotazy.

Bonus: "Naplánuj nám Den 15 odpoledne včetně aktuálního počasí v Palmě" → kombinace knowledge + web search.

- [ ] **Step 4: Opravy**

Pokud Gemini halucinuje → follow-up: "Cituj doslovně větu ze zdroje." Pokud neumí, potvrzeno halucinace → zaznamenat a zvážit přidání Claude Pro jako fallback.

---

## Task 30: Finální dokumentace + odjezd

- [ ] **Step 1: Napsat 1 stránkový cheat-sheet**

`CHEATSHEET.md` (nebo poznámka v Apple Notes):
```markdown
# Svatební cesta 2026 – Cheatsheet

## Offline (v autě / na lodi)
- iPhone: Books → "Svatební cesta 2026" (EPUB)
  - Rotor: Headings → swipe = skok po dnech
  - TOC: Menu → Obsah
- Samsung: Obsidian → vault "svatebni-cesta" → Reading view

## Online (hotely s wifi)
- NotebookLM iOS: notebook "Svatební cesta 2026"
- Gemini iOS: Gems → "Svatební cesta"

## Fallbacks
- iPhone: Notebooks app → iCloud/svatebni-cesta-md/
- iPhone: Files → web/index.html → Safari
- Samsung: Markor → /Download/svatebni-cesta-md/

## Důležité
- PDF rezervací: Google Drive → svatebni-cesta-PDF/
- Ubytovací kontakty: ubytovani.md v plánu

## Nouzové
- Tištěný itinerář v autě (svatebni-cesta.html → A4 print)
```

- [ ] **Step 2: Vytisknout cheat-sheet**

Print `CHEATSHEET.md` → A4 → vzít do auta.

- [ ] **Step 3: Poslední `git pull` na Samsungu**

1. 5. 2026 ráno: Obsidian Git → Pull.

- [ ] **Step 4: Poslední rebuild EPUB pokud změny**

Pokud byly commity po Task 18: rebuild EPUB + upload do iCloud Drive znovu.

- [ ] **Step 5: Ověřit všechny telefony + Gemini jdou**

Finální smoke test: každá appka otevřít, ptát se Gemini "Co máme na Den 1".

- [ ] **Step 6: Vyrazit na cestu**

🎉

---

## Ověření completeness

Po dokončení všech 30 Tasků, projít spec checklist (sekce 8, fáze A-F, ~110 položek) a potvrdit že každá položka má odpovídající Task/Step. Pokud něco chybí → přidat Task.

## Commit hygiene

- Každý Task končí commitem
- Commit messages v angličtině, krátké, imperative mood
- Po Task 17 všechny commity do **nového public repa** `wedding-plan-public`
- Privátní repo zůstává archivovaný bez dalších commitů
