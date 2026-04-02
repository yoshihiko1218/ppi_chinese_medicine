#!/usr/bin/env python3
"""Convert METHODS_AND_RESULTS.md to a well-formatted PDF."""
import markdown
import os

# Read markdown
with open("METHODS_AND_RESULTS.md", "r") as f:
    md_text = f.read()

# Fix image paths to absolute paths for PDF rendering
base_dir = os.path.abspath(".")
md_text = md_text.replace("results/figures/", f"file://{base_dir}/results/figures/")

# Convert markdown to HTML
html_body = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "codehilite", "toc"],
)

# Wrap in full HTML with CSS styling
html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @page {{
    size: A4;
    margin: 2cm 2.5cm;
    @bottom-center {{
      content: counter(page);
      font-size: 9pt;
      color: #666;
    }}
  }}
  body {{
    font-family: "Noto Sans CJK SC", "Noto Sans SC", "WenQuanYi Micro Hei",
                 "Microsoft YaHei", "SimSun", "Helvetica Neue", Helvetica,
                 Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #222;
  }}
  h1 {{
    font-size: 20pt;
    color: #1a1a2e;
    border-bottom: 2px solid #16213e;
    padding-bottom: 8px;
    margin-top: 30px;
  }}
  h2 {{
    font-size: 16pt;
    color: #16213e;
    border-bottom: 1px solid #ccc;
    padding-bottom: 5px;
    margin-top: 25px;
    page-break-after: avoid;
  }}
  h3 {{
    font-size: 13pt;
    color: #0f3460;
    margin-top: 20px;
    page-break-after: avoid;
  }}
  h4 {{
    font-size: 11.5pt;
    color: #333;
    margin-top: 15px;
    page-break-after: avoid;
  }}
  p {{
    text-align: justify;
    margin-bottom: 8px;
  }}
  table {{
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
    font-size: 10pt;
    page-break-inside: avoid;
  }}
  th {{
    background-color: #16213e;
    color: white;
    padding: 6px 10px;
    text-align: left;
    font-weight: bold;
  }}
  td {{
    border: 1px solid #ddd;
    padding: 5px 10px;
  }}
  tr:nth-child(even) {{
    background-color: #f8f8f8;
  }}
  code {{
    font-family: "DejaVu Sans Mono", "Courier New", monospace;
    font-size: 9.5pt;
    background-color: #f4f4f4;
    padding: 1px 4px;
    border-radius: 3px;
  }}
  pre {{
    background-color: #f4f4f4;
    padding: 12px;
    border-radius: 5px;
    border: 1px solid #ddd;
    overflow-x: auto;
    font-size: 9pt;
    line-height: 1.4;
    page-break-inside: avoid;
  }}
  pre code {{
    background: none;
    padding: 0;
  }}
  img {{
    max-width: 100%;
    height: auto;
    display: block;
    margin: 15px auto;
    border: 1px solid #ddd;
    border-radius: 4px;
    page-break-inside: avoid;
  }}
  strong {{
    color: #16213e;
  }}
  hr {{
    border: none;
    border-top: 1px solid #ccc;
    margin: 25px 0;
  }}
  blockquote {{
    border-left: 4px solid #16213e;
    padding-left: 15px;
    color: #555;
    margin: 10px 0;
  }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""

# Save intermediate HTML
with open("METHODS_AND_RESULTS.html", "w") as f:
    f.write(html)
print("HTML saved: METHODS_AND_RESULTS.html")

# Convert to PDF using weasyprint
try:
    from weasyprint import HTML
    HTML(string=html, base_url=base_dir).write_pdf("METHODS_AND_RESULTS.pdf")
    print("PDF saved: METHODS_AND_RESULTS.pdf")
except Exception as e:
    print(f"WeasyPrint error: {e}")
    print("Trying alternative approach...")
    # Fallback: use pandoc with xelatex and a simpler approach
    import subprocess
    # Create a version without Chinese in title for xelatex fallback
    result = subprocess.run(
        ["pandoc", "METHODS_AND_RESULTS.html", "-o", "METHODS_AND_RESULTS.pdf",
         "--pdf-engine=xelatex",
         "-V", "CJKmainfont=WenQuanYi Micro Hei",
         "-V", "geometry:margin=1in"],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode == 0:
        print("PDF saved via pandoc fallback: METHODS_AND_RESULTS.pdf")
    else:
        print(f"Pandoc fallback also failed: {result.stderr[:500]}")
