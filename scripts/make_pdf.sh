#!/bin/bash
# Convert METHODS_AND_RESULTS.md to PDF using pandoc + xelatex + Noto Sans CJK SC
# With proper image centering and width constraints

conda activate ppi 2>/dev/null

pandoc METHODS_AND_RESULTS.md \
  -o METHODS_AND_RESULTS.pdf \
  --pdf-engine=xelatex \
  -V mainfont="Noto Sans CJK SC" \
  -V sansfont="Noto Sans CJK SC" \
  -V monofont="DejaVu Sans Mono" \
  -V geometry:margin=1in \
  -V fontsize=11pt \
  -V colorlinks=true \
  -V linkcolor=blue \
  --resource-path=. \
  --variable header-includes='
\usepackage{xeCJK}
\setCJKmainfont{Noto Sans CJK SC}
\usepackage{float}
\floatplacement{figure}{H}
\makeatletter
\renewenvironment{figure}[1][]{%
  \begin{center}
}{%
  \end{center}
}
\makeatother
\let\oldincludegraphics\includegraphics
\renewcommand{\includegraphics}[2][]{\begin{center}\oldincludegraphics[#1]{#2}\end{center}}
' \
  2>&1

echo "Exit code: $?"
ls -lh METHODS_AND_RESULTS.pdf 2>/dev/null
