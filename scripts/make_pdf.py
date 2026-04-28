#!/usr/bin/env python3
"""
Render METHODS_AND_RESULTS.md → HTML and PDF in the current working directory.

Reads ./METHODS_AND_RESULTS.md, writes ./METHODS_AND_RESULTS.html and
./METHODS_AND_RESULTS.pdf. Image references like `results/figures/...` are
rewritten to absolute file:// URLs so WeasyPrint resolves them.

Falls back to pandoc + xelatex if WeasyPrint fails.
"""
import os
import subprocess
import sys
import markdown


CSS = """
  @page {
    size: A4;
    margin: 2cm 2.5cm;
    @bottom-center { content: counter(page); font-size: 9pt; color: #666; }
  }
  body {
    font-family: "Noto Sans CJK SC", "Noto Sans SC", "WenQuanYi Micro Hei",
                 "Microsoft YaHei", "SimSun", "Helvetica Neue", Helvetica,
                 Arial, sans-serif;
    font-size: 11pt; line-height: 1.6; color: #222;
  }
  h1 { font-size: 20pt; color: #1a1a2e; border-bottom: 2px solid #16213e;
       padding-bottom: 8px; margin-top: 30px; }
  h2 { font-size: 16pt; color: #16213e; border-bottom: 1px solid #ccc;
       padding-bottom: 5px; margin-top: 25px; page-break-after: avoid; }
  h3 { font-size: 13pt; color: #0f3460; margin-top: 20px; page-break-after: avoid; }
  h4 { font-size: 11.5pt; color: #333; margin-top: 15px; page-break-after: avoid; }
  p  { text-align: justify; margin-bottom: 8px; }
  table { border-collapse: collapse; width: 100%; margin: 12px 0;
          font-size: 10pt; page-break-inside: avoid; }
  th { background-color: #16213e; color: white; padding: 6px 10px;
       text-align: left; font-weight: bold; }
  td { border: 1px solid #ddd; padding: 5px 10px; }
  tr:nth-child(even) { background-color: #f8f8f8; }
  code { font-family: "DejaVu Sans Mono", "Courier New", monospace;
         font-size: 9.5pt; background-color: #f4f4f4;
         padding: 1px 4px; border-radius: 3px; }
  pre  { background-color: #f4f4f4; padding: 12px; border-radius: 5px;
         border: 1px solid #ddd; overflow-x: auto; font-size: 9pt;
         line-height: 1.4; page-break-inside: avoid; }
  pre code { background: none; padding: 0; }
  img { max-width: 100%; height: auto; display: block; margin: 15px auto;
        border: 1px solid #ddd; border-radius: 4px; page-break-inside: avoid; }
  strong { color: #16213e; }
  hr { border: none; border-top: 1px solid #ccc; margin: 25px 0; }
  blockquote { border-left: 4px solid #16213e; padding-left: 15px;
               color: #555; margin: 10px 0; }
"""


def main():
    md_path = "METHODS_AND_RESULTS.md"
    html_path = "METHODS_AND_RESULTS.html"
    pdf_path = "METHODS_AND_RESULTS.pdf"

    if not os.path.exists(md_path):
        print(f"ERROR: {md_path} not found in {os.getcwd()}; "
              f"run stage 9 (make_report.py) first")
        sys.exit(1)

    with open(md_path) as f:
        md_text = f.read()

    base_dir = os.path.abspath(".")
    # Rewrite relative image paths to absolute file:// URLs so WeasyPrint can find them
    md_text = md_text.replace("results/figures/", f"file://{base_dir}/results/figures/")

    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "codehilite", "toc"],
    )
    html = (f"<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"utf-8\">\n"
            f"<style>{CSS}</style>\n</head>\n<body>\n{html_body}\n</body>\n</html>\n")

    with open(html_path, "w") as f:
        f.write(html)
    print(f"HTML saved: {html_path}")

    # PDF via WeasyPrint (preferred — pure Python, handles CJK if fonts available)
    try:
        from weasyprint import HTML
        HTML(string=html, base_url=base_dir).write_pdf(pdf_path)
        print(f"PDF saved: {pdf_path} ({os.path.getsize(pdf_path)/1024:.0f} KB)")
        return
    except Exception as e:
        print(f"WeasyPrint failed: {e}")

    # Fallback: pandoc + xelatex with CJK font
    print("Trying pandoc + xelatex fallback...")
    try:
        proc = subprocess.run(
            ["pandoc", md_path, "-o", pdf_path,
             "--pdf-engine=xelatex",
             "-V", "mainfont=Noto Sans CJK SC",
             "-V", "CJKmainfont=Noto Sans CJK SC",
             "-V", "geometry:margin=1in",
             "--resource-path=."],
            capture_output=True, text=True, timeout=180,
        )
        if proc.returncode == 0:
            print(f"PDF saved via pandoc: {pdf_path} "
                  f"({os.path.getsize(pdf_path)/1024:.0f} KB)")
        else:
            print(f"Pandoc fallback failed (exit {proc.returncode}):")
            print(proc.stderr[:800])
            sys.exit(2)
    except FileNotFoundError:
        print("Pandoc not installed — install pandoc or fix WeasyPrint to render PDF")
        sys.exit(2)


if __name__ == "__main__":
    main()
