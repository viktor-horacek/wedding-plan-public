#!/usr/bin/env bash
set -euo pipefail

echo "==> Preprocessing markdown"
python preprocess.py

echo "==> Generating EPUB"
EPUB_ARGS=(
  --toc --toc-depth=2 --split-level=1
  --metadata "title=Svatební cesta 2026"
  --metadata "lang=cs"
)
if [ -f cover.jpg ]; then
  EPUB_ARGS+=(--epub-cover-image=cover.jpg)
fi
pandoc "${EPUB_ARGS[@]}" -o dist/svatebni-cesta.epub dist/bundle.md

echo "==> Generating MkDocs web"
python -m mkdocs build --clean --site-dir dist/web

echo "==> Zipping web for offline"
if command -v zip >/dev/null 2>&1; then
  (cd dist && zip -rq web.zip web)
else
  python -c "import shutil; shutil.make_archive('dist/web', 'zip', 'dist', 'web')"
fi

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
INDIVIDUAL_COUNT=$(find dist/individual -name '*.md' | wc -l | tr -d ' ')
echo "  - dist/individual/*.md         → $INDIVIDUAL_COUNT md pro NotebookLM (nahrát do Drive)"
