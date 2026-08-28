from pathlib import Path
from html import escape
import re

HOME = Path.home()
BASE = HOME / "ebook_premium"
OLD = HOME / "epub_clean" / "final_book_clean.html"
OUT = HOME / "LearnForge"

chapter_titles = {
    1: "From Coder to Architect",
    2: "The Foundations of Good Architecture",
    3: "Requirements Before Architecture",
    4: "Scalability",
    5: "Performance, Latency and Throughput",
    6: "Monolith, Modular Monolith and Microservices",
    7: "Microservice Trade-offs",
    8: "Distributed Systems",
    9: "Event-Driven Architecture",
    10: "Clean Architecture",
    11: "SOLID Principles",
    12: "DRY, KISS, YAGNI, Cohesion and Coupling",
    13: "API Architecture",
    14: "Database Architecture",
    15: "Caching",
    16: "Security by Design",
    17: "Observability",
    18: "Testing Architecture",
    19: "CI/CD and Deployment",
    20: "Production Readiness",
    21: "Disaster Recovery and Resilience",
    22: "Architecture Documentation",
    23: "Real-World System Design Example",
    24: "Architecture Review Checklist",
    25: "Final Architecture Cheat Sheet",
}

def raw_to_html(text, number, title):
    """
    Convert chapters 01-05 raw text into safe readable HTML.
    Preserve code-like blocks and paragraphs.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove obvious page-number/header noise if present
    lines = text.splitlines()

    cleaned = []
    for line in lines:
        s = line.strip()

        if not s:
            cleaned.append("")
            continue

        if re.fullmatch(r"System Architecture & Clean Code.*", s):
            continue

        if re.fullmatch(r"\d+", s):
            continue

        cleaned.append(line.rstrip())

    text = "\n".join(cleaned).strip()

    # Escape everything first
    escaped = escape(text)

    # Restore simple markdown-ish emphasis
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)

    # Split into paragraphs
    blocks = re.split(r"\n\s*\n", escaped)

    body = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        lines = block.splitlines()

        # Code-looking blocks
        code_words = [
            "import ", "export ", "const ", "class ", "function ",
            "async ", "await ", "return ", "app.", "redis.",
            "{", "}", "interface ", "new ", "//"
        ]

        if any(any(line.strip().startswith(x) for x in code_words)
               for line in lines):
            body.append("<pre><code>" + "\n".join(lines) + "</code></pre>")
        else:
            paragraph = " ".join(x.strip() for x in lines)
            body.append(f"<p>{paragraph}</p>")

    return f"""
<section class="chapter" id="chapter-{number:02d}">
  <div class="chapter-kicker">CHAPTER {number:02d}</div>
  <h1>{escape(title)}</h1>
  <div class="chapter-rule"></div>
  {''.join(body)}
</section>
"""

def extract_chapters_06_25(html):
    """
    Extract Chapter 06 onward from the existing 06–25 manuscript.
    We locate headings such as Chapter 06 and split from there.
    """
    # Try several heading forms
    pattern = re.compile(
        r'(?is)<[^>]*>\s*Chapter\s+06\s*</[^>]*>'
    )

    m = pattern.search(html)

    if not m:
        # fallback: plain-text heading
        m = re.search(r'(?i)Chapter\s+06', html)

    if not m:
        raise RuntimeError("Could not locate Chapter 06 in final_book_clean.html")

    return html[m.start():]

old = OLD.read_text(encoding="utf-8", errors="ignore")

# Find 06–25 section
later = extract_chapters_06_25(old)

# Remove accidental trailing full-document closing tags
later = re.sub(r'(?is)</body>\s*</html>\s*$', '', later).strip()

# Build first five chapters
first = []

for n in range(1, 6):
    path = BASE / "chapters" / "raw" / f"chapter-{n:02d}-raw.txt"
    text = path.read_text(encoding="utf-8", errors="ignore")
    first.append(raw_to_html(text, n, chapter_titles[n]))

# TOC
toc = []
for n, title in chapter_titles.items():
    toc.append(
        f'<li><span class="num">{n:02d}</span>{escape(title)}</li>'
    )

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="title" content="LearnForge — System Architecture & Clean Code">
<meta name="author" content="LearnForge">
<meta name="description" content="System Architecture & Clean Code — Expanded Digital Edition 2026">
<title>LearnForge — System Architecture & Clean Code</title>

<style>
@page {{
    size: A4;
    margin: 20mm 17mm 22mm 17mm;

    @bottom-left {{
        content: "LearnForge • System Architecture & Clean Code";
        font-size: 8pt;
    }}

    @bottom-right {{
        content: counter(page);
        font-size: 8pt;
    }}
}}

* {{
    box-sizing: border-box;
}}

html {{
    font-family: Arial, Helvetica, sans-serif;
    color: #172033;
    background: white;
}}

body {{
    margin: 0;
    line-height: 1.55;
    font-size: 10.5pt;
}}

.cover {{
    min-height: 250mm;
    page-break-after: always;
    padding: 30mm 18mm;
    background: linear-gradient(145deg, #07111f, #102b48);
    color: white;
    position: relative;
}}

.cover .brand {{
    font-size: 12pt;
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-bottom: 45mm;
}}

.cover h1 {{
    font-size: 31pt;
    line-height: 1.05;
    margin: 0 0 10mm;
}}

.cover .subtitle {{
    font-size: 14pt;
    line-height: 1.5;
    max-width: 150mm;
}}

.cover .edition {{
    position: absolute;
    bottom: 25mm;
    font-size: 10pt;
    letter-spacing: 2px;
}}

.toc {{
    page-break-after: always;
}}

.toc h1 {{
    font-size: 24pt;
    margin-bottom: 12mm;
}}

.toc ol {{
    list-style: none;
    padding: 0;
}}

.toc li {{
    padding: 4mm 0;
    border-bottom: 1px solid #dce3ec;
}}

.num {{
    display: inline-block;
    width: 14mm;
    font-weight: bold;
}}

.chapter {{
    page-break-before: always;
}}

.chapter-kicker {{
    color: #1769aa;
    font-size: 9pt;
    font-weight: bold;
    letter-spacing: 3px;
    margin-bottom: 4mm;
}}

.chapter h1 {{
    font-size: 25pt;
    line-height: 1.15;
    margin: 0 0 5mm;
    color: #0b1f35;
}}

.chapter-rule {{
    height: 2px;
    background: #1769aa;
    margin-bottom: 8mm;
}}

p {{
    margin: 0 0 5mm;
}}

strong {{
    color: #0b4778;
}}

pre {{
    background: #101827;
    color: #e7edf5;
    padding: 5mm;
    border-radius: 3mm;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 8.5pt;
    line-height: 1.45;
    margin: 6mm 0;
}}

code {{
    font-family: "DejaVu Sans Mono", monospace;
}}

h1, h2, h3 {{
    page-break-after: avoid;
}}

pre, table, blockquote {{
    page-break-inside: avoid;
}}

.chapter > h1 {{
    break-before: avoid;
}}

a {{
    color: #1769aa;
}}

@media print {{
    .chapter {{
        break-before: page;
    }}
}}
</style>
</head>

<body>

<section class="cover">
  <div class="brand">LEARNFORGE ENGINEERING HANDBOOK</div>
  <h1>System Architecture<br>&amp; Clean Code</h1>
  <div class="subtitle">
    A Practical Mindset-First Blueprint for Building Scalable,
    Maintainable, and Production-Ready Software Systems
  </div>
  <div class="edition">EXPANDED DIGITAL EDITION — 2026</div>
</section>

<section class="toc">
<h1>Table of Contents</h1>
<ol>
{''.join(toc)}
</ol>
</section>

{''.join(first)}

{later}

</body>
</html>
"""

target = OUT / "LearnForge_COMPLETE_25_CHAPTERS_2026.html"
target.write_text(html, encoding="utf-8")

print(f"Created: {target}")
print(f"HTML characters: {len(html):,}")
