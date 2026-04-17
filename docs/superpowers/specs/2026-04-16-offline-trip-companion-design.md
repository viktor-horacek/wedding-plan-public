# Offline & AI companion pro svatební cestu 2026 – design spec

**Datum:** 2026-04-16
**Autor:** Viktor Horáček (brainstorm s Claude)
**Stav:** draft pro schválení → implementation plan

---

## 1. Cíl a kontext

Repozitář `viktor-horacek/wedding-plan` (aktuálně private) obsahuje ~40 hierarchicky strukturovaných markdown souborů: 27denní itinerář honeymoon trip 1.–27. 5. 2026 (auto + MSC Grandiosa). Plán je detailní a finalizovaný – během cesty už se nebude měnit.

Během cesty **nebude internet** (internet balíček MSC nebudeme kupovat, v Alpách nestabilní data). Proto vše musí fungovat 100 % offline po jednorázové instalaci na telefony před odjezdem.

### Dva uživatelé, různé preference

- **Uživatel A (iPhone + VoiceOver)** – potřebuje maximálně accessible čtení md obsahu, žádné úpravy na cestě.
- **Uživatel B (Samsung Android)** – pohodlné prohlížení, klikatelné relativní odkazy mezi md soubory.

### Cíle spec dokumentu pokrývá

1. Offline čtení všech md souborů na obou telefonech.
2. Přístup pro Gemini LLM jako persistent knowledge (kombinace lookup + reasoning + web search) během online momentů.
3. Git repo vyčistit od citlivých PDF a případně publikovat jako public.

### Non-goals

- Dynamické updaty plánu během cesty (plán je finalizovaný).
- Spolupráce více lidí, review workflow, kolaborativní editace.
- Zachování commit history starého repa.
- Native iOS/Android app development.

---

## 2. Klíčová rozhodnutí z researche

Toto jsou ne-triviální závěry z paralelního researche (4 + 3 agenti na různá témata). Odůvodnění je tady, aby spec dával smysl při čtení za rok.

### Obsidian iOS nepoužít

- Dokumentované VoiceOver bugy od 10/2024 dodnes **bez opravy** (Obsidian forum thread bez odpovědi, changelog za 2025-2026 bez zmínky "accessibility/VoiceOver").
- Na AppleVis není ani v katalogu – komunita ho ignoruje.
- **Pro Android je Obsidian naopak winner** – od 2025 zdarma i komerčně, plná podpora relativních linků + reading mode.

### EPUB v Apple Books je pro iOS+VoiceOver primární kanál (ne md appka)

Rozhodující feature: **rotor** po nadpisech a linkcích. Swipe-down skáče jen po `Den X` nadpisech. TOC first-class citizen (Menu → TOC → kapitola). Nejvíc ověřený blind UX (AppleVis, AccessiblePublishing.ca, Apple aktivně testuje).

### Pro Gemini: dual strategie (NotebookLM + Roboti Gem)

- **NotebookLM** (zdarma, limit 50 zdrojů): **per-file upload 40 md** → inline klikatelné citace "den-15.md → sekce Časová osa". Nejsilnější grounding proti halucinacím.
- **Roboti Gem** (zdarma, limit 10 souborů): **bundle.md (merged)** → 2M context window v Gemini 3 Pro pojme celý plán najednou, žádný chunking, žádné hallucinations z špatného retrieval. Lepší na reasoning dotazy ("kolik celkem zaplatíme za parkování").

### Gemini Gems: Share button je grayed out, pokud má Gem GitHub URL jako knowledge

Takže GitHub connector do Gemu = použijeme jen pokud nepotřebujeme sdílet. Pro sdílitelný Gem musí být knowledge jako **uploaded file** nebo **Drive files**. Tohle omezení přímo určuje použití bundle přes upload.

### YAML frontmatter má měřitelný efekt +15-25 % retrieval accuracy

Gemini 3 Pro (duben 2026) parsuje YAML nativně. Klíče fungují jako attention magnety. Pro Gemini je navíc lepší **Markdown headers** než XML (Gemini byl trénován na webových datech).

### Publikace repa: vytvořit nový public repo (nepokusit se vyčistit historii)

- `git-filter-repo` nebo BFG umí cleanup, ale PDF zůstávají v GitHub cache + PR referencích + forcích. Musí se kontaktovat support.
- Nový public repo = 10 minut, nula rizika, history plánu nemá archivní hodnotu.
- Starý privátní repo zůstává jako záloha (archivovat – read-only).

---

## 3. Architektura

```
┌─────────────────────────────────────────────────────────────────┐
│ git repo (nový: wedding-plan-public)                            │
│ ~40 md × YAML frontmatter + breadcrumb + jednotné H2 sekce     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
              preprocess.py  +  build.sh
                         │
           ┌─────────────┼──────────┐
           ▼             ▼          ▼
    dist/individual/  dist/bundle.md   dist/svatebni-cesta.epub
    /*.md                                dist/web/
                                         dist/web.zip
           │             │                 │
           ▼             ▼                 ▼
    Google Drive    Google Drive      distribuce na telefony
    (mirror)        (upload)          + GitHub Pages deploy
           │             │
           ▼             ▼
    NotebookLM      Roboti Gem
    (per-file)      (bundle)
```

### Kanály a konzumenti

| Konzument | Formát | Nástroj | Zdroj | Priority |
|-----------|--------|---------|-------|----------|
| Uživatel A offline | EPUB | Apple Books | `dist/*.epub` přes iCloud | **primární** |
| Uživatel A offline fallback | md | Notebooks (zdarma) | iCloud md složka | fallback |
| Uživatel A offline fallback 2 | HTML | Safari + web.zip v Files | extract | fallback |
| Uživatel B offline | md | Obsidian Android | git clone repa | **primární** |
| Uživatel B offline fallback | md | Markor (F-Droid) | stažený ZIP | fallback |
| Oba online Gemini lookup | 40 md | NotebookLM | Drive auto-sync | **primární** |
| Oba online Gemini konverzace | bundle.md | Roboti Gem | Drive upload | **primární** |
| Online preview/testing | HTML | GitHub Pages | auto-deploy | optional |
| PDF rezervace | PDF | Google Drive | soukromá složka | povinné |

---

## 4. Preprocessing (md → md+)

### YAML frontmatter schéma

Pro denní soubory:
```yaml
---
title: "Den 15 – Pátek 15. 5. 2026 – Palma de Mallorca"
source_path: 2-lod/den-15/den-15.md
phase: 2-lod
phase_number: 2
day_number: 15
date: 2026-05-15
day_of_week: patek
prev: den-14
next: den-16
tags: [cruise, palma, bellver]
---

> **Cesta:** Svatební cesta 2026 › Plavba MSC Grandiosa (Dny 11-18) › Den 15 / 15. 5. 2026 › Palma de Mallorca
> **Předchozí:** [den-14](../den-14/den-14.md) – **Následující:** [den-16](../den-16/den-16.md)
```

Pro shared soubory (`finance.md`, `ubytovani.md`, `checklist.md`, `baleni.md`, `lod-info.md` apod.):
```yaml
---
title: "Finance – přehled nákladů"
source_path: finance.md
document_type: reference
scope: celý itinerář
tags: [finance, rozpočet]
---
```

### Jednotné H2 sekce napříč denními soubory

Research potvrdil +ROI. Denní soubory sjednotit na:
- `## Časová osa` (chronologický harmonogram)
- `## Náklady` (tabulka)
- `## Checklist` (checkbox list)
- `## Zdroje` (ověření)

(Pokud sekce není relevantní, vynechat.)

### Skript `preprocess.py`

Projde `1-cesta-tam/`, `2-lod/`, `3-cesta-zpet/` + root `*.md`, odvodí metadata z cesty (day_number z `den-XX`, phase ze složky, date z TRIP_START + offset), vygeneruje `dist/individual/` (enhanced per-file) + `dist/bundle.md` (merged s `=== FILE: ... ===` separátory).

Závislosti: `pip install python-frontmatter pyyaml`. Plný kód v Appendixu A.

---

## 5. Build pipeline (lokální `build.sh`)

```bash
#!/usr/bin/env bash
set -euo pipefail
python preprocess.py  # → dist/individual + dist/bundle.md

# EPUB (přítelkyně, primární)
pandoc --toc --toc-depth=2 --split-level=1 \
  --metadata title="Svatební cesta 2026" \
  --metadata lang=cs \
  --epub-cover-image=cover.jpg \
  -o dist/svatebni-cesta.epub \
  dist/bundle.md

# MkDocs web (GitHub Pages + offline ZIP)
mkdocs build --clean --site-dir dist/web
(cd dist && zip -r web.zip web)

# Single-file HTML (univerzální backup)
pandoc --toc --toc-depth=3 --standalone --embed-resources \
  --metadata title="Svatební cesta 2026" \
  -o dist/svatebni-cesta.html \
  dist/bundle.md
```

### Závislosti

- Python 3.11+, `python-frontmatter`, `pyyaml`
- Pandoc 3.x (`choco install pandoc`)
- MkDocs + Material (`pip install mkdocs-material`)
- zip (v git bash)

### `mkdocs.yml`

Nav z README odvozená, Material theme s offline plugin, WCAG 2.1 AA. Detaily v Appendixu B.

**Poznámka k nav:** Appendix B ukazuje explicitní nav, ale MkDocs umí fallback na automatický nav z adresářové struktury, pokud `nav:` nedefinuješ. Pro rychlý start lze `nav:` úplně vynechat a MkDocs vygeneruje nav z hierarchie složek. Ruční nav dává přehlednější řazení, ale vyžaduje údržbu.

---

## 6. Migration flow

```
1. Audit md na citlivé údaje (grep na čísla karet, CVV, PIN, IBAN)
                    ↓
2. Extrakce z PDF → doplnit ubytovani.md co chybí
                    ↓
3. PDF → Google Drive (soukromá složka svatebni-cesta-PDF)
                    ↓
4. Install Python+deps, Pandoc, MkDocs Material
                    ↓
5. Napsat preprocess.py, build.sh, mkdocs.yml
                    ↓
6. První build lokálně → ověřit dist/ výstupy
                    ↓
7. Drive mirror md souborů (složka svatebni-cesta-md/)
                    ↓
8. Nový public repo wedding-plan-public
     - copy md (ne dist/, ne PDF)
     - push
     - GitHub Pages enable
                    ↓
9. Starý privátní repo → Archive (read-only)
                    ↓
10. Distribuce telefony:
    A) iPhone: EPUB → iCloud → Apple Books
    A) iPhone fallback: Notebooks + md složka
    B) Samsung: Obsidian Android + git clone
    B) Samsung fallback: web.zip → otevřít index.html
                    ↓
11. Gemini setup:
    - NotebookLM web: import 40 md z Drive → share link
    - Roboti Gem: upload bundle.md → share link
    - Oboje: system instructions (viz sekce 7)
                    ↓
12. Acceptance test 28.-29. 4. 2026 (2-3 dny před odjezdem)
    - Letadlový režim → test každé appky
    - VoiceOver demo s přítelkyní
    - 5 testovacích dotazů v NotebookLM + Gem
```

---

## 7. System instructions pro NotebookLM + Gem (identické)

```
Jsi asistent pro svatební cestu 1.–27. 5. 2026 (2 osoby, auto + MSC Grandiosa).
Odpovídej česky.

PRAVIDLA GROUNDING:
1. Odpovídej POUZE z poskytnutých zdrojů. Nevymýšlej ceny, časy, adresy, telefony.
2. Pokud info není v zdrojích: "V itineráři to není uvedeno, doporučuji ověřit."
3. Postup: (a) identifikuj den/datum v dotazu, (b) najdi den-XX.md, (c) cituj sekci, (d) shrň.
4. Vždy uveď zdroj: "(den-15.md → Časová osa 10:00)".
5. Pro finanční dotazy čti finance.md; balení baleni.md; ubytování ubytovani.md; checklist checklist.md.
6. Pro loď čti 2-lod/lod-info.md, bary.md, stravovani.md, zabava-aktivity.md, hidden-gems.md, prakticke-tipy.md, pristavy-logistika.md, napojove-balicky.md, zdroje.md.
7. Pokud používáš bundle soubor, jednotlivé dny najdeš podle separátoru `=== FILE: cesta/k/souboru.md ===`.

KONTEXT DAT:
- Fáze 1 (1-cesta-tam/): dny 1–11, 1.–11. 5. 2026, auto Rakousko→Itálie
- Fáze 2 (2-lod/): dny 11–18, 11.–18. 5. 2026, MSC Grandiosa (Janov → La Spezia → Civitavecchia → sea day → Palma → Barcelona → Cannes → Janov)
- Fáze 3 (3-cesta-zpet/): dny 18–27, 18.–27. 5. 2026, auto Švýcarsko→ČR

PRO WEB SEARCH (pouze pokud dotaz výslovně vyžaduje aktuální data):
- Kombinuj knowledge s aktuálními daty (počasí, zavírací doby, jízdní řády)
- Vždy rozliš "z plánu" vs "z webu".

STYL:
- Stručně, prakticky. Bez zbytečných úvodů.
- U časů uvádět přesné intervaly.
- U cen uvádět měnu explicitně (EUR/CHF/CZK).
```

---

## 8. EXTENSIVE CHECKLIST – 6 fází

### Fáze A: Audit & příprava (před jakoukoli změnou)

- [ ] A1. Zkontrolovat git status – žádné nedokončené změny v working tree
- [ ] A2. Vytvořit backup aktuálního stavu: `git clone --mirror` do `D:\sources\wedding-plan-backup.git`
- [ ] A3. Zkopírovat PDF zálohu mimo git: `D:\sources\wedding-plan-pdf-backup/` (pro jistotu před smazáním)
- [ ] A4. Grep všech md na čísla karet: `grep -rE '\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b' *.md */**/*.md`
- [ ] A5. Grep na `CVV|PIN|IBAN|SWIFT|SSN`: `grep -irE '(CVV|PIN|IBAN|SWIFT|SSN)' *.md */**/*.md`
- [ ] A6. Ruční přečtení `ubytovani.md`, `finance.md` na citlivé údaje
- [ ] A7. Pokud něco nalezeno → sanitize (nahradit placeholdery, commitnout)
- [ ] A8. Extrakce klíčových údajů z 22 PDF → doplnit do `ubytovani.md` (rezervační čísla, check-in časy, kontakty)
- [ ] A9. Ověřit, že po extrakci ubytovani.md obsahuje vše potřebné během cesty
- [ ] A10. Vytvořit Google Drive složku `svatebni-cesta-PDF/` (soukromá)
- [ ] A11. Upload 22 PDF do Drive složky
- [ ] A12. Ověřit Drive přístup z iPhone i Samsung (offline cache pokud potřeba)
- [ ] A13. Smazat PDF z pracovní kopie repa (nekomitovat ještě)

### Fáze B: Tooling & build setup

- [ ] B1. Install Python 3.11+ (pokud není)
- [ ] B2. `pip install python-frontmatter pyyaml`
- [ ] B3. Install Pandoc: `choco install pandoc` (nebo přímo z pandoc.org)
- [ ] B4. Install MkDocs Material: `pip install mkdocs-material`
- [ ] B5. Ověřit `pandoc --version`, `mkdocs --version`
- [ ] B6. Napsat `preprocess.py` podle Appendixu A
- [ ] B7. Napsat `build.sh` podle sekce 5
- [ ] B8. Napsat `mkdocs.yml` podle Appendixu B
- [ ] B9. Připravit `cover.jpg` pro EPUB (1600×2400 px)
- [ ] B10. Přidat `.gitignore` s `dist/`, `*.pdf`, `.env`, `__pycache__/`
- [ ] B11. První dry-run: `python preprocess.py` → zkontrolovat `dist/individual/` + `dist/bundle.md`
- [ ] B12. Vizuálně projít 2-3 enhanced soubory (frontmatter OK, breadcrumbs OK, obsah zachován)
- [ ] B13. Ověřit jednotné H2 sekce napříč denními soubory (pokud neunifikováno, doplnit do preprocess.py nebo ručně)
- [ ] B14. `bash build.sh` → ověřit `dist/svatebni-cesta.epub`, `dist/web/index.html`, `dist/svatebni-cesta.html`, `dist/web.zip`
- [ ] B15. Otevřít EPUB v Calibre nebo macOS Books → strukturální test (TOC, kapitoly)
- [ ] B16. Otevřít `dist/web/index.html` v Chrome → ověřit nav, search, relativní odkazy
- [ ] B17. Otevřít `dist/svatebni-cesta.html` samostatně → ověřit fungování
- [ ] B18. Commit tooling: `preprocess.py`, `build.sh`, `mkdocs.yml`, `.gitignore`, `cover.jpg` (do starého private repa i nového public repa)

### Fáze C: Cleanup repa + publikace

- [ ] C1. Založit nový GitHub repo `wedding-plan-public` jako **public** (přes `gh repo create` nebo web UI)
- [ ] C2. Lokálně: `mkdir D:\sources\wedding-plan-public && cd wedding-plan-public`
- [ ] C3. `git init -b main`
- [ ] C4. Copy pouze md + tooling: `cp ../svatební-cesta/*.md .`, `cp -r ../svatební-cesta/1-cesta-tam .` (bez PDF!), `cp -r 2-lod`, `cp -r 3-cesta-zpet`, `cp preprocess.py build.sh mkdocs.yml cover.jpg .gitignore`
- [ ] C5. Ověřit absenci PDF: `find . -name '*.pdf'` → empty
- [ ] C6. `git add .` → `git status` → ověřit že se nic PDF nepridalo
- [ ] C7. `git commit -m "Initial public release of wedding trip plan"`
- [ ] C8. `git remote add origin git@github.com:viktor-horacek/wedding-plan-public.git`
- [ ] C9. `git push -u origin main`
- [ ] C10. GitHub UI: Settings → Pages → Source: GitHub Actions (nebo docs/ nebo gh-pages branch)
- [ ] C11. GitHub Action workflow `.github/workflows/pages.yml` pro auto-deploy MkDocs (viz Appendix C)
- [ ] C12. Push Action → ověřit že buildnul a deployed
- [ ] C13. Ověřit GitHub Pages URL: `https://viktor-horacek.github.io/wedding-plan-public/` v browseru
- [ ] C14. Starý private repo `wedding-plan` → Settings → Archive this repository (read-only)
- [ ] C15. Dokumentace kde jsou PDF (Drive) – poznámka v README nového repa

### Fáze D: Distribuce na telefony

#### Uživatel A – iPhone (primární: EPUB + Apple Books)

- [ ] D1. Na PC: build dist/svatebni-cesta.epub
- [ ] D2. Upload EPUB do iCloud Drive (složka `Knihy/`)
- [ ] D3. Počkat na sync do iPhone (ověřit v Files app → iCloud Drive)
- [ ] D4. V Files app: tap na EPUB → Share → Open in Books
- [ ] D5. V Apple Books ověřit: kniha se objevila v Library
- [ ] D6. Zapnout VoiceOver → test rotor navigace (nastavení → Zpřístupnění → VoiceOver)
- [ ] D7. Test rotor headings: "skoč na Den 15"
- [ ] D8. Test TOC: Menu → Table of Contents → procházet kapitolami
- [ ] D9. Test vyhledávání: "Palma" → skok na relevantní pasáž
- [ ] D10. Test cross-reference: tap na link v Den 15 → otevře cíl
- [ ] D11. Test letadlový režim → ověřit že EPUB jede offline

#### Uživatel A – iPhone (fallback: Notebooks zdarma)

- [ ] D12. App Store: Notebooks (notebooksapp.com) → Install
- [ ] D13. V iCloud Drive vytvořit složku `svatebni-cesta-md/` a upload všech enhanced md (z `dist/individual/`)
- [ ] D14. Notebooks: Settings → iCloud → Enable, otevřít složku
- [ ] D15. Test otevření 2-3 denních souborů, klikatelné linky
- [ ] D16. Známý limit: preview mode má VoiceOver bugy s nadpisy → ptát se přítelkyně, zda ji to vadí; pokud ano, fallback 2

#### Uživatel A – iPhone (fallback 2: web.zip v Safari)

- [ ] D17. Upload `dist/web.zip` do iCloud Drive
- [ ] D18. V Files app: tap na zip → extrakce do `web/` složky
- [ ] D19. Tap na `web/index.html` → otevře v Safari (file://)
- [ ] D20. Ověřit navigaci, klikatelné linky
- [ ] D21. Přidat do Reading List jednotlivé stránky (pro offline cache)

#### Uživatel B – Samsung (primární: Obsidian Android + git)

- [ ] D22. Play Store: Obsidian → Install
- [ ] D23. Obsidian: Create vault → "svatebni-cesta" lokální
- [ ] D24. Install Obsidian Git plugin (Community Plugins → Git → Enable)
- [ ] D25. Git plugin nastavit: remote URL wedding-plan-public, branch main
- [ ] D26. Pull → vault se naplní md soubory
- [ ] D27. Settings: Default view for new tabs → **Reading view**
- [ ] D28. Test: otevřít README → kliknout na link na den-01 → otevře se
- [ ] D29. Test letadlový režim → ověřit offline

#### Uživatel B – Samsung (fallback: Markor)

- [ ] D30. F-Droid: Markor → Install
- [ ] D31. Stáhnout `web.zip` do `/Download/`
- [ ] D32. Rozbalit do `/Download/svatebni-cesta-web/`
- [ ] D33. Markor otevřít `/Download/svatebni-cesta-md/` nebo soubory v tom
- [ ] D34. Alternativně: `git clone` přes Termux + Markor čte soubory

### Fáze E: Gemini / Roboti Gem setup

- [ ] E1. Zapnout privacy: myaccount.google.com → Data & Privacy → Gemini Apps Activity → OFF
- [ ] E2. Ověřit "Personal Intelligence" (2026 rebrand cross-app flow) – zapnout/vypnout dle preference
- [ ] E3. Upload `dist/individual/*.md` na Google Drive → složka `svatebni-cesta-md-enhanced/` (40 souborů). Pro NotebookLM je vhodné před uploadem souborům dát numerické prefixy pro řazení v flat seznamu, např. `01-den-01.md`, ..., `11-den-11.md`, `12-lod-info.md`, `13-bary.md`, ..., `20-den-11-lod.md`, ..., `50-ubytovani.md`, `51-finance.md`, `52-checklist.md`, `53-baleni.md`. Prefixy přidej buď ručně, nebo krátkým PowerShell skriptem.
- [ ] E4. Upload `dist/bundle.md` na Google Drive → `svatebni-cesta-bundle/bundle.md`
- [ ] E5. NotebookLM: notebooklm.google.com → Create Notebook "Svatební cesta 2026"
- [ ] E6. Add sources → Drive → select 40 enhanced md souborů (sort podle prefix)
- [ ] E7. Custom instructions (prompt): paste z sekce 7 tohoto dokumentu
- [ ] E8. Test 5 dotazů z Acceptance test (sekce 9)
- [ ] E9. Share → "Anyone with a link" → "Viewer" → zkopírovat link
- [ ] E10. Poslat link přítelkyni (SMS/iMessage) + popis jak otevřít v iOS NotebookLM appce
- [ ] E11. Install iOS NotebookLM app pro oba (App Store)
- [ ] E12. Roboti Gem: gemini.google.com → Gems → Create Gem "Svatební cesta"
- [ ] E13. Instructions field: paste z sekce 7
- [ ] E14. Knowledge → Upload `bundle.md` z PC (nebo přes Drive pokud podporováno)
- [ ] E15. Test: "Co máme 15. den odpoledne?" → ověřit že cituje bundle
- [ ] E16. Share → copy link → poslat přítelkyni
- [ ] E17. Ověřit Gem funguje v iOS Gemini appce pro oba

### Fáze F: Acceptance test + rollout

- [ ] F1. Naplánovat test 28. nebo 29. 4. 2026 (2-3 dny před 1. 5.)
- [ ] F2. Letadlový režim na obou telefonech
- [ ] F3. Uživatel A test scénáře:
  - [ ] F3a. "Přečti mi plán den 5 ráno" – Apple Books rotor
  - [ ] F3b. "Skoč na den 20" – TOC navigation
  - [ ] F3c. "Najdi mi info o ubytování v Rapallo" – search
  - [ ] F3d. "Co dělat, když lanovka nejede?" – cross-reference
  - [ ] F3e. Fallback: stejné scénáře v Notebooks (pokud Apple Books selže)
- [ ] F4. Uživatel B test scénáře:
  - [ ] F4a. Otevři README → proklikej se na den 10
  - [ ] F4b. Fulltext search "Prosecco" → vrátí relevantní dny
  - [ ] F4c. Klikni na link v den-05.md → otevře den-05
  - [ ] F4d. Back tlačítko vrátí na předchozí dokument
- [ ] F5. Vypnout letadlový režim → online Gemini test:
  - [ ] F5a. "Kolik stojí vstup do CastelBrando v den 5?" (lookup, grounded)
  - [ ] F5b. "Kolik celkově utratíme za parkování za 27 dní?" (syntéza, multiple sources)
  - [ ] F5c. "Co vzít do batohu na den 8 na Monte Baldo?" (cross-reference baleni + den 8)
  - [ ] F5d. "Jaké počasí očekáváme v Palmě 15. května?" (web search + grounded)
  - [ ] F5e. "Co je plán B, když Monte Baldo lanovka nejede?" (alt plány)
- [ ] F6. Pokud nějaký test selže → identifikovat root cause, opravit před odjezdem
- [ ] F7. Napsat cheat-sheet (1 stránka, A4) s klíčovými URL a hesly, vzít sebou vytištěné
- [ ] F8. Dokumentace pro přítelkyni: jak otevřít EPUB, jak spustit rotor, jak otevřít NotebookLM notebook (audio nebo text)
- [ ] F9. Dokumentace pro Viktora: jak `git pull` v Obsidianu kdyby se něco změnilo, kde jsou backup ZIPy
- [ ] F10. 1. 5. 2026 před odjezdem: poslední `git pull` na Samsungu, ověřit všechno jede

---

## 9. Rollback / co dělat, když něco selže

| Problém | Fallback |
|---------|----------|
| Apple Books neotevře EPUB | Notebooks s md soubory z iCloud |
| Notebooks nefunguje s VoiceOverem | web.zip → rozbalit → Safari otevřít file:// |
| Obsidian Android se nenaplní | Markor + stažený web.zip nebo md složka |
| NotebookLM vypadne | Roboti Gem s bundle.md |
| Gem halucinuje | Follow-up: "cituj doslovně větu ze zdroje" – pokud neumí, přiznal halucinaci |
| Gemini appka padá | Web gemini.google.com v Safari/Chrome |
| Vypadne internet dřív než čekáme | Všechno kritické je už offline na obou telefonech |
| Něco kritického není v md, jen v PDF | Google Drive PDF složka (offline-cached) |

---

## 10. Otevřené otázky / future work

- **PWA na GitHub Pages** – iOS Safari podporuje omezeně (service worker offline cache nespolehlivý). Přidat později, není blocker.
- **Automatizace build na GitHub Actions** – zatím ručně `bash build.sh`. Pokud změny během posledního týdne, ruční rebuild je OK.
- **Dual-language (anglická verze)** – není v scope.
- **TTS audio export** z md (pro poslech během řízení) – mimo scope, ale zajímavé budoucí rozšíření.

---

## Appendix A: `preprocess.py`

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Preprocess markdown files for LLM knowledge base (NotebookLM / Gemini Gem / Claude).
Scans 1-cesta-tam/, 2-lod/, 3-cesta-zpet/ + root *.md.
Produces dist/individual/*.md (enhanced per-file) + dist/bundle.md.

Install:  pip install python-frontmatter pyyaml
Run:      python preprocess.py
"""
from __future__ import annotations
import re
import shutil
from datetime import date, timedelta
from pathlib import Path

import frontmatter
import yaml

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
INDIVIDUAL = DIST / "individual"
BUNDLE = DIST / "bundle.md"

PHASES = {
    "1-cesta-tam":  {"number": 1, "label": "Cesta tam (Dny 1-11)"},
    "2-lod":        {"number": 2, "label": "Plavba MSC Grandiosa (Dny 11-18)"},
    "3-cesta-zpet": {"number": 3, "label": "Cesta zpet (Dny 18-27)"},
}
TRIP_START = date(2026, 5, 1)
DAYS_CZ = ["pondeli", "utery", "streda", "ctvrtek", "patek", "sobota", "nedele"]
DAY_RE = re.compile(r"den-(\d{2})")


def parse_day(p):
    m = DAY_RE.search(str(p))
    return int(m.group(1)) if m else None


def iso_date(n):
    return TRIP_START + timedelta(days=n - 1)


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
        path_norm = str(rel).replace("\\", "/")
        bundle.append(f"\n\n=== FILE: {path_norm} ===\n\n{enhanced}")
    BUNDLE.write_text("\n".join(bundle), encoding="utf-8")
    print(f"OK: {len(list(INDIVIDUAL.rglob('*.md')))} files -> {INDIVIDUAL}")
    print(f"OK: bundle -> {BUNDLE}")


if __name__ == "__main__":
    main()
```

---

## Appendix B: `mkdocs.yml`

```yaml
site_name: Svatební cesta 2026
site_description: 27denní itinerář honeymoon trip (auto + MSC Grandiosa)
site_author: Viktor Horáček
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
  - offline  # critical pro file:// otevření

nav:
  - Přehled: README.md
  - Cesta tam:
      - Den 1: 1-cesta-tam/den-01/den-01.md
      - Den 2: 1-cesta-tam/den-02/den-02.md
      # ...atd.
  - Plavba:
      - Přehled lodi: 2-lod/lod-info.md
      - Den 11: 2-lod/den-11/den-11.md
      # ...atd.
  - Cesta zpět:
      # ...atd.
  - Reference:
      - Ubytování: ubytovani.md
      - Finance: finance.md
      - Checklist: checklist.md
      - Balení: baleni.md

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

---

## Appendix C: GitHub Actions pro auto-deploy

`.github/workflows/pages.yml`:

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

---

## Reference

Citované zdroje z researche (duben 2026):

- [Apple Books + VoiceOver rotor navigation — AccessiblePublishing.ca](https://www.accessiblepublishing.ca/voiceover-and-apple-books-on-ios/)
- [1Writer accessibility review — AppleVis](https://www.applevis.com/apps/ios/productivity/1writer-markdown-text-editor)
- [Notebooks iOS — cross-references and internal links](https://www.notebooksapp.com/cross-references-and-internal-links/)
- [Obsidian VoiceOver bug reports — Obsidian Forum](https://forum.obsidian.md/t/several-accessibility-issues-with-voiceover-for-obsidian-on-ios/89681)
- [NotebookLM Docs](https://support.google.com/notebooklm/answer/16215270)
- [Gemini Gems sharing](https://support.google.com/gemini/answer/16504957)
- [Notebooks in Gemini launch 8. 4. 2026 — Google Blog](https://blog.google/innovation-and-ai/products/gemini-app/notebooks-gemini-notebooklm/)
- [MkDocs Material offline plugin](https://squidfunk.github.io/mkdocs-material/plugins/offline/)
- [MkDocs Material accessibility audit WCAG 2.1 AA](https://albrittonanalytics.com/brand/design-system/accessibility-audit-report/)
- [Pandoc EPUB guide](https://pandoc.org/epub.html)
- [git-filter-repo](https://github.com/newren/git-filter-repo)
- [GitHub: Removing sensitive data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
