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
import unicodedata
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
FLAT = DIST / "drive-flat"

PHASE_SHORT = {
    "1-cesta-tam":  "cesta-tam",
    "2-lod":        "lod",
    "3-cesta-zpet": "cesta-zpet",
}


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

PHASE_ORDER = ["1-cesta-tam", "2-lod", "3-cesta-zpet"]
PHASE_DAYS = {
    "1-cesta-tam":  set(range(1, 12)),    # 1-11 (boarding day 11 shared with 2-lod)
    "2-lod":        set(range(11, 19)),   # 11-18 (disembark day 18 shared with 3-cesta-zpet)
    "3-cesta-zpet": set(range(18, 28)),   # 18-27
}


def phase_of_day(day, current_phase=None):
    """Return the phase containing day N. On boundary days (11, 18) that belong
    to two phases, prefer current_phase if it contains the day."""
    if current_phase and day in PHASE_DAYS.get(current_phase, set()):
        return current_phase
    for phase in PHASE_ORDER:
        if day in PHASE_DAYS[phase]:
            return phase
    return None


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
    current_phase = meta.get("phase")

    def _link(day_ref):
        day_num = int(day_ref.split("-")[-1])
        target_phase = phase_of_day(day_num, current_phase)
        if target_phase == current_phase or target_phase is None:
            return f"../{day_ref}/{day_ref}.md"
        return f"../../{target_phase}/{day_ref}/{day_ref}.md"

    if meta.get("prev"):
        nav.append(f"**Predchozi:** [{meta['prev']}]({_link(meta['prev'])})")
    if meta.get("next"):
        nav.append(f"**Nasledujici:** [{meta['next']}]({_link(meta['next'])})")
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


def _slugify(text, max_len=45):
    """Convert Czech text to lowercase ASCII slug with hyphens, truncated."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:max_len].strip("-")


def _short_descriptor(title):
    """Extract the bit after the first colon from titles like 'Den N - weekday D.M.: Desc'."""
    if ":" in title:
        return title.split(":", 1)[-1].strip()
    return title


def flatten_for_drive():
    """Build dist/drive-flat/ — all enhanced md as a flat list with informative
    numeric prefixes. NotebookLM shows source names as plain filename (no folder
    hierarchy), so the prefix encodes phase, day number, and a short descriptor
    extracted from the H1 title. Sort order: phase days chronologically, then
    ship-shared files, then root reference docs."""
    if FLAT.exists():
        shutil.rmtree(FLAT)
    FLAT.mkdir(parents=True)

    ordered = []
    # Phase day files in chronological order; days 11 and 18 appear in two phases.
    for phase in PHASE_ORDER:
        for n in sorted(PHASE_DAYS[phase]):
            src = INDIVIDUAL / phase / f"den-{n:02d}" / f"den-{n:02d}.md"
            if src.exists():
                ordered.append((PHASE_SHORT[phase], f"den-{n:02d}", src))
    # Ship-shared files (non-day md directly under 2-lod/)
    for src in sorted((INDIVIDUAL / "2-lod").glob("*.md")):
        ordered.append(("lod", src.stem, src))
    # Root reference files
    for src in sorted(INDIVIDUAL.glob("*.md")):
        ordered.append(("root", src.stem, src))

    for i, (phase_short, stem, src) in enumerate(ordered, start=1):
        text = src.read_text(encoding="utf-8")
        title = frontmatter.loads(text).metadata.get("title", stem)
        descriptor = _slugify(_short_descriptor(title))
        parts = [f"{i:02d}"]
        if phase_short != "root":
            parts.append(phase_short)
        parts.append(stem)
        if descriptor and descriptor != stem:
            parts.append(descriptor)
        name = "-".join(parts) + ".md"
        (FLAT / name).write_text(text, encoding="utf-8")
    print(f"OK: drive-flat -> {FLAT} ({len(ordered)} files)")


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
    flatten_for_drive()


if __name__ == "__main__":
    main()
