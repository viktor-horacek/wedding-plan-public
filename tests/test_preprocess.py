import shutil
from datetime import date
from pathlib import Path

from preprocess import parse_day, iso_date, detect_phase, split_h1, derive_meta, render
from preprocess import main, phase_of_day


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
    assert "document_type" not in meta
    assert "scope" not in meta


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
    assert meta["document_type"] == "reference"
    assert meta["scope"] == "celý itinerář"


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
    assert "\n---\n" in out
    assert "> **Cesta:** Svatebni cesta 2026 > Cesta tam (Dny 1-11) > Den 5 / 5. 5. 2026 > Prosecco Hills" in out
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
    assert "Předchozí" not in out   # diacritic form must not appear
    assert "Predchozi" not in out   # ascii nav form must not appear for shared
    assert "Nasledujici" not in out  # ascii next form must not appear for shared
    assert "> **Cesta:** Svatebni cesta 2026 > Finance" in out  # shared file must still have a breadcrumb
    assert "Přehled." in out


def test_phase_of_day_interior_days():
    assert phase_of_day(5) == "1-cesta-tam"
    assert phase_of_day(15) == "2-lod"
    assert phase_of_day(25) == "3-cesta-zpet"


def test_phase_of_day_boundary_day_11_defaults_to_first_phase():
    assert phase_of_day(11) == "1-cesta-tam"


def test_phase_of_day_boundary_day_18_defaults_to_first_phase():
    assert phase_of_day(18) == "2-lod"


def test_phase_of_day_boundary_respects_current_phase_hint():
    assert phase_of_day(11, current_phase="2-lod") == "2-lod"
    assert phase_of_day(18, current_phase="3-cesta-zpet") == "3-cesta-zpet"
    assert phase_of_day(11, current_phase="1-cesta-tam") == "1-cesta-tam"


def test_phase_of_day_out_of_range():
    assert phase_of_day(0) is None
    assert phase_of_day(28) is None


def test_render_cross_phase_next_link_at_phase_1_end():
    meta = {
        "title": "Den 11 – Pondělí 11. 5.: Nalodění",
        "source_path": "1-cesta-tam/den-11/den-11.md",
        "phase": "1-cesta-tam",
        "phase_number": 1,
        "day_number": 11,
        "date": "2026-05-11",
        "day_of_week": "pondeli",
        "prev": "den-10",
        "next": "den-12",
    }
    out = render(meta, "body")
    assert "[den-10](../den-10/den-10.md)" in out
    assert "[den-12](../../2-lod/den-12/den-12.md)" in out


def test_render_cross_phase_prev_link_at_phase_2_start():
    meta = {
        "title": "Den 11 – Pondělí 11. 5.: Nalodění (lod)",
        "source_path": "2-lod/den-11/den-11.md",
        "phase": "2-lod",
        "phase_number": 2,
        "day_number": 11,
        "date": "2026-05-11",
        "day_of_week": "pondeli",
        "prev": "den-10",
        "next": "den-12",
    }
    out = render(meta, "body")
    assert "[den-10](../../1-cesta-tam/den-10/den-10.md)" in out
    assert "[den-12](../den-12/den-12.md)" in out


def test_render_cross_phase_links_at_phase_3_boundary():
    meta = {
        "title": "Den 18 – Pondělí 18. 5.: Vylodění",
        "source_path": "3-cesta-zpet/den-18/den-18.md",
        "phase": "3-cesta-zpet",
        "phase_number": 3,
        "day_number": 18,
        "date": "2026-05-18",
        "day_of_week": "pondeli",
        "prev": "den-17",
        "next": "den-19",
    }
    out = render(meta, "body")
    assert "[den-17](../../2-lod/den-17/den-17.md)" in out
    assert "[den-19](../den-19/den-19.md)" in out


def test_main_generates_individual_and_bundle(monkeypatch, tmp_path):
    fixtures = Path(__file__).parent / "fixtures"
    for src in fixtures.rglob("*.md"):
        dst = tmp_path / src.relative_to(fixtures)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src, dst)

    monkeypatch.setattr("preprocess.ROOT", tmp_path)
    monkeypatch.setattr("preprocess.DIST", tmp_path / "dist")
    monkeypatch.setattr("preprocess.INDIVIDUAL", tmp_path / "dist" / "individual")
    monkeypatch.setattr("preprocess.BUNDLE", tmp_path / "dist" / "bundle.md")

    main()

    individual_day = tmp_path / "dist" / "individual" / "1-cesta-tam" / "den-01" / "den-01.md"
    assert individual_day.exists()
    content = individual_day.read_text(encoding="utf-8")
    assert "day_number: 1" in content
    assert "> **Cesta:**" in content

    bundle = tmp_path / "dist" / "bundle.md"
    assert bundle.exists()
    bundle_content = bundle.read_text(encoding="utf-8")
    assert "=== FILE: 1-cesta-tam/den-01/den-01.md ===" in bundle_content
    assert "=== FILE: finance.md ===" in bundle_content
