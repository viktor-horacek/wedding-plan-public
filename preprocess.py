#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Preprocess markdown files for LLM knowledge base (NotebookLM / Gemini Gem / Claude).

Scans 1-cesta-tam/, 2-lod/, 3-cesta-zpet/ + root *.md in the repo root.
Produces dist/individual/*.md (enhanced per-file with YAML frontmatter and
breadcrumb) and dist/bundle.md (all files concatenated with path separators).

Install:  pip install -r requirements.txt
Run:      python preprocess.py
"""
from __future__ import annotations
import re
import shutil
import yaml
import frontmatter
from datetime import date, timedelta
from pathlib import Path

TRIP_START = date(2026, 5, 1)
DAY_RE = re.compile(r"den-(\d{2})")

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
INDIVIDUAL = DIST / "individual"
BUNDLE = DIST / "bundle.md"


def parse_day(p):
    m = DAY_RE.search(str(p))
    return int(m.group(1)) if m else None


def iso_date(n):
    return TRIP_START + timedelta(days=n - 1)


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


def split_h1(text):
    lines = text.splitlines()
    for i, l in enumerate(lines):
        s = l.strip()
        if s.startswith("# ") and not s.startswith("## "):
            return s[2:].strip(), "\n".join(lines[:i] + lines[i + 1:]).lstrip("\n")
    return None, text


DAYS_CZ = ["pondeli", "utery", "streda", "ctvrtek", "patek", "sobota", "nedele"]


def derive_meta(rel, raw):
    h1, body = split_h1(raw)
    phase = detect_phase(rel)
    n = parse_day(rel)
    meta = {
        "title": h1 or rel.stem,
        "source_path": rel.as_posix(),
    }
    if not phase and parse_day(rel) is None:
        meta["document_type"] = "reference"
        meta["scope"] = "celý itinerář"
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
        if kw in low:
            tags.append(tag)
    if tags:
        meta["tags"] = tags
    return meta, body  # body stripped downstream by render()


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
        path_norm = rel.as_posix()
        bundle.append(f"\n\n=== FILE: {path_norm} ===\n\n{enhanced}")
    BUNDLE.write_text("\n".join(bundle), encoding="utf-8")
    print(f"OK: {len(list(INDIVIDUAL.rglob('*.md')))} files -> {INDIVIDUAL}")
    print(f"OK: bundle -> {BUNDLE}")


if __name__ == "__main__":
    main()
