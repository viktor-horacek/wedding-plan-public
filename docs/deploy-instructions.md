# Deploy & distribuce – krok za krokem

Tento dokument provádí tebe (Viktora) manuálními kroky, které Claude už nemohl udělat sám. Postupuj v pořadí. Každý krok říká **kde** (web/terminal), **co** (přesný příkaz / UI akce) a **jak** ověříš, že to sedí.

---

## Task 14 – PDF na Google Drive

**Kde:** [drive.google.com](https://drive.google.com) (web) + File Explorer na PC
**Co:**

1. V Drive webu: `New → Folder → svatebni-cesta-PDF`
2. Otevři složku, klikni `New → File upload` (nebo drag & drop)
3. Upload všech **22 PDF** z těchto umístění na lokálním disku:
   - `D:\sources\svatební-cesta\1-cesta-tam\den-01\*.pdf` (2 soubory: Altstadt Bed&Bike)
   - `D:\sources\svatební-cesta\1-cesta-tam\den-02\*.pdf` (2: Pension Clara)
   - `D:\sources\svatební-cesta\1-cesta-tam\den-03\*.pdf` (2: el Zhìgol B&B)
   - `D:\sources\svatební-cesta\1-cesta-tam\den-06\*.pdf` (2: Verona)
   - `D:\sources\svatební-cesta\1-cesta-tam\den-07\*.pdf` (2: Aria Life Hotel)
   - `D:\sources\svatební-cesta\1-cesta-tam\den-09\*.pdf` (2: Casa nel Golfo)
   - `D:\sources\svatební-cesta\3-cesta-zpet\den-18\*.pdf` (2: Pandora Stresa)
   - `D:\sources\svatební-cesta\3-cesta-zpet\den-20\*.pdf` (2: Alpenblick)
   - `D:\sources\svatební-cesta\3-cesta-zpet\den-24\*.pdf` (2: WHLIVING Konstanz)
   - `D:\sources\svatební-cesta\3-cesta-zpet\den-25\*.pdf` (2: BNB Claudia)
   - `D:\sources\svatební-cesta\3-cesta-zpet\den-26\*.pdf` (2: Goldbach Regensburg)

   Rychlý způsob: v File Exploreru zadej do adresního řádku `D:\sources\svatební-cesta`, pak search `*.pdf` – vrátí všech 22. Ctrl+A → drag do Drive.

4. **Udělej Drive složku dostupnou offline na telefonech:**
   - **iPhone:** Drive app → složka `svatebni-cesta-PDF` → `⋯ → Make available offline` (každý soubor; nebo celou složku).
   - **Samsung:** Drive app → složka → dlouhý stisk souboru → `Make available offline`.

**Ověření:** V Drive vidíš všech 22 PDF. Na telefonu zapni letadlový režim, otevři Drive app, zkus otevřít libovolný PDF — otevře se bez internetu.

**Po ověření** mi napiš "PDF na Drive", já je pak smažu z lokálního repa + committnu.

---

## Task 15 – Nový public GitHub repo

**Kde:** [github.com/new](https://github.com/new) (web) + terminál
**Co (varianta A – přes web UI):**

1. Web: **New repository**
   - Owner: `viktor-horacek`
   - Name: `wedding-plan-public`
   - Description: `Svatební cesta 2026 – 27denní itinerář (auto + MSC Grandiosa)`
   - **Public**
   - NE-zaškrtávej "Add a README", "Add .gitignore", "Choose a license" – provedeme lokálně
   - `Create repository`
2. Vlastní okno s `Quick setup` ignoruj.

**Co (varianta B – přes gh CLI, rychlejší):**

```bash
gh repo create wedding-plan-public --public \
  --description "Svatební cesta 2026 – 27denní itinerář (auto + MSC Grandiosa)"
```

**Pak lokálně:**

```bash
# Vytvoř nový pracovní adresář VEDLE stávajícího (aby stávající zůstal nedotčený)
cd /d/sources
cp -r svatební-cesta wedding-plan-public
cd wedding-plan-public

# Smaž git historii (private historie má PDF a revertovaný mkdocs hack)
rm -rf .git

# Smaž PDF, dist/, local tooling (ale ne .github, ne tests, ne tooling soubory)
find . -name '*.pdf' -delete
rm -rf dist/
rm -rf .idea/
rm -rf .claude/
rm -rf .pytest_cache/
rm -rf __pycache__/ tests/__pycache__/

# Ověř že není nic citlivého
find . -name '*.pdf'   # → empty
grep -rE 'PIN: [0-9]' *.md 3-cesta-zpet/*/*.md  # → empty

# Inicializuj fresh git
git init -b main
git add .
git status   # projdi — uvidíš jen md, preprocess.py, tests/, build.sh, mkdocs.yml, .github/, styles.css, requirements.txt, docs/

# Commit
git commit -m "Initial public release of wedding trip plan"

# Připoj remote a push
git remote add origin git@github.com:viktor-horacek/wedding-plan-public.git
git push -u origin main
```

**Ověření:** [github.com/viktor-horacek/wedding-plan-public](https://github.com/viktor-horacek/wedding-plan-public) ukazuje soubory, žádný PDF, žádná citlivá data.

---

## Task 16 – Zapnout GitHub Pages

**Kde:** `github.com/viktor-horacek/wedding-plan-public/settings/pages`

1. **Build and deployment** → **Source**: `GitHub Actions` (ne `Deploy from a branch`)
2. Klikni `Save` (pokud je tlačítko)
3. Přejdi na tab **Actions** (`/actions`) – měl by se sám spustit workflow `Deploy MkDocs to GitHub Pages` (ze souboru `.github/workflows/pages.yml`, který už v repu je).
4. Počkej ~1–2 min, dokud nezobrazí zelený fajfka.
5. Pokud FAIL, klikni na run → uvidíš log. Nejčastější problém: `docs_dir: dist/individual` neexistuje v CI – workflow ho sám vygeneruje přes `python preprocess.py`, takže by to mělo projít.

**Ověření:** Otevři `https://viktor-horacek.github.io/wedding-plan-public/` – uvidíš MkDocs Material web s názvem "Svatební cesta 2026", hlavní menu (Cesta tam / Plavba / Cesta zpět / Reference), fungující search.

---

## Task 17 – Archive starý private repo

**Kde:** `github.com/viktor-horacek/wedding-plan/settings`

1. Scroll úplně dolů → **Danger Zone**
2. Klikni `Archive this repository`
3. Potvrď napsáním názvu `viktor-horacek/wedding-plan`
4. Repo změní banner na "This repository has been archived and is now read-only"

**PDF zůstávají v historii starého private repa — nevadí, jen ty k němu máš přístup.**

---

## Fáze 3 – Distribuce na telefony

### iPhone (přítelkyně) – primární EPUB

1. Na PC spusť `bash build.sh` – vygeneruje `dist/svatebni-cesta.epub`.
2. Zkopíruj `dist/svatebni-cesta.epub` do složky **iCloud Drive** na PC (např. `C:\Users\zarco\iCloudDrive\`). Počkej na sync (pár sekund).
3. Na iPhone → `Files` app → `iCloud Drive` → najdi `svatebni-cesta.epub`.
4. Tap na soubor → `Share` → `Open in Books`. Kniha se objeví v Books Library.
5. **Test s přítelkyní (důležité):** pošli jí krátký návod:
   - `Books` app → knihovna → "Svatební cesta 2026"
   - Uvnitř: **rotor** (otočení 2 prstů) → `Headings` → swipe down přeskakuje po nadpisech dnů
   - **TOC:** menu ikona (vlevo nahoře) → `Table of Contents` → vybrat kapitolu "Den X"
   - **Search:** menu → `Search` → zadat "Palma" atd.

### iPhone – fallback 1 (Notebooks app)

1. App Store → instalovat `Notebooks – Write and Organize` (zdarma, vývojář Alfons Schmid).
2. Na PC: zkopíruj **celou složku** `dist/individual/` do iCloud Drive (tj. `iCloud Drive/svatebni-cesta-md/`).
3. V Notebooks app: Settings (ozubené kolečko) → iCloud → Enable → vybrat `svatebni-cesta-md/`.
4. Test: otevři `README.md` → tap na odkaz → cílový soubor se otevře.

### iPhone – fallback 2 (offline web v Safari)

1. Z PC: zkopíruj `dist/web.zip` do iCloud Drive.
2. Na iPhone: `Files` → `iCloud Drive` → tap `web.zip` → extract (vznikne složka `web/`).
3. V `web/` tap `index.html` → "Open in…" → Safari. Funguje offline.

### Samsung (Viktor) – primární Obsidian + Git

1. Google Play → instalovat **Obsidian** (free).
2. Otevři → **Create new vault** → jméno `svatebni-cesta`, interní úložiště.
3. Settings → **Community plugins** → Turn ON → Browse → hledej **Obsidian Git** → Install → Enable.
4. Obsidian Git settings → zadej:
   - Remote URL: `https://github.com/viktor-horacek/wedding-plan-public.git`
   - Branch: `main`
   - Author name: `Viktor Horáček`
5. Pull (nebo první setup vyžaduje Clone). Vault se naplní md soubory.
6. Settings → **Editor** → **Default view for new tabs**: `Reading view`.
7. Test: otevři `README.md` → tap odkaz na Den 1 → otevře se. Zpět: swipe zleva.
8. Test letadlový režim: zapni airplane mode → vše funguje z lokálního vaultu.

### Samsung – fallback Markor

1. F-Droid: install [Markor](https://f-droid.org/packages/net.gsantner.markor/) nebo Google Play.
2. Přes USB kabel z PC → kopíruj `dist/web.zip` do `/Download/`.
3. V Samsung Files: tap `web.zip` → Extract → vznikne `/Download/web/`.
4. V Markoru otevři `/Download/web/index.html`.

---

## Fáze 4 – Gemini context

### NotebookLM (primární – přesné citace, grounded)

1. [notebooklm.google.com](https://notebooklm.google.com) → **Create new notebook**
2. Název: `Svatební cesta 2026`
3. **Add sources** → `Google Drive` → Sign-in, pak vybrat 40 souborů z `svatebni-cesta-md-enhanced/` (upload je nejdřív na Drive přes `Drive → New → File upload` a drag celé složky `dist/individual/`).
4. Custom instructions (klikni na settings / gear ikonu):
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
5. **Share** (vpravo nahoře) → `Anyone with a link` → `Viewer` → zkopíruj link → pošli přítelkyni (iMessage, WhatsApp).
6. Stáhnout iOS NotebookLM app z App Store na oba telefony.

**Testovací dotazy po setupu:**
- "Kolik stojí vstup do CastelBrando v Den 5?" (lookup)
- "Kolik celkem utratíme za parkování za 27 dní?" (syntéza)
- "Co vzít do batohu na Den 8 na Monte Baldo?" (cross-reference)
- "Jaké počasí bude v Palmě 15. května 2026?" (web search)
- "Co je plán B, když Monte Baldo lanovka nejede?" (fallback plán)

### Roboti Gem (sekundární – konverzačnější)

1. [gemini.google.com](https://gemini.google.com) → `Gems` (levý panel) → `Create Gem`
2. Název: `Svatební cesta 2026`
3. Instructions: paste **stejný prompt** jako do NotebookLM (viz výše)
4. Knowledge → Upload file → vybrat `dist/bundle.md` z PC (nebo přes Drive)
5. Save
6. Test: "Co máme 15. den odpoledne?" — měl by citovat bundle s FILE separátorem
7. **Share** → copy link → pošli přítelkyni

---

## Privacy (před Task E)

1. [myaccount.google.com/activitycontrols](https://myaccount.google.com/activitycontrols)
2. **Gemini Apps Activity** → **OFF**

Bez tohoto jsou konverzace použité pro trénink Google AI modelů.

---

## Acceptance test (2–3 dny před odjezdem, ideálně 28. nebo 29. 4. 2026)

- [ ] iPhone letadlový režim → Books → "Svatební cesta 2026" → rotor navigace → VoiceOver čte den 1, 15, 27
- [ ] iPhone letadlový režim → Notebooks → den 15 → klikatelný odkaz funguje
- [ ] Samsung letadlový režim → Obsidian → README → klik na Den 10 → otevře
- [ ] Online: NotebookLM iOS → 5 testovacích dotazů (výše)
- [ ] Online: Roboti Gem iOS → stejné dotazy → kombinace s web search

Pokud něco selže, spadne se na rollback (design spec sekce 9).

---

## Tipy pro dlouhodobou údržbu

- **Před odjezdem** (1. 5. 2026): poslední `git pull` na Samsungu, poslední export EPUB do iPhonu.
- **Během cesty:** měnit plán nikdy nebudeš, repo je jen read-only reference.
- **Po cestě:** repo může zůstat public jako archive, nebo archivovat taky (`Settings → Archive`).
