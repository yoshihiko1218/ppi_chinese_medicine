#!/bin/bash
# Convert METHODS_AND_RESULTS.md to PDF using pandoc + xelatex + Noto Sans SC
conda activate ppi

pandoc METHODS_AND_RESULTS.md \
  -o METHODS_AND_RESULTS.pdf \
  --pdf-engine=xelatex \
  -V mainfont="Noto Sans SC" \
  -V sansfont="Noto Sans SC" \
  -V monofont="DejaVu Sans Mono" \
  -V CJKmainfont="Noto Sans SC" \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  -V colorlinks=true \
  -V linkcolor=blue \
  -V urlcolor=blue \
  --resource-path=. \
  -V header-includes="\usepackage{xeCJK}\setCJKmainfont{Noto Sans SC}" \
  2>&1

echo "Exit code: $?"
ls -lh METHODS_AND_RESULTS.pdf 2>/dev/null
