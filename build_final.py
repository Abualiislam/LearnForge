from pathlib import Path
import re, html

src = Path.home() / "book_full.txt"
out = Path.home() / "LearnForge" / "LearnForge_System_Architecture_Clean_Code_2026.html"

text = src.read_text(encoding="utf-8")

# Remove accidental AI-generation text
text = re.sub(
    r"except inDue to strict output character limits.*?```html",
    "except in",
    text,
    flags=re.S | re.I
)

# Remove old 25-chapter TOC
text = re.sub(
    r"Table of Contents.*?25 — Final Architecture Cheat Sheet\s+102",
    "",
    text,
    flags=re.S
)

# Remove repeated PDF headers/footers
text = re.sub(
    r"System Architecture & Clean Code 2026\s+\d+",
    "",
    text
)

# Remove CHAPTER labels; we'll create clean chapter headings
text = re.sub(r"\s*CHAPTER 0[1-5]\s*", "\n", text)

# Split chapters
chapters = [
    "From Coder to Architect",
    "The Foundations of Good Architecture",
    "Requirements Before Architecture",
    "Scalability",
    "Performance, Latency and Throughput",
]

parts = []
positions = []

for title in chapters:
    p = text.find(title)
    positions.append(p)

for i, title in enumerate(chapters):
    start = positions[i]
    end = positions[i+1] if i+1 < len(positions) else len(text)
    if start != -1:
        parts.append((title, text[start:end]))

def esc(s):
    return html.escape(s.strip())

def format_content(s):
    lines = s.splitlines()
    result = []
    in_code = False
    code = []

    code_markers = (
        "import ", "export ", "const ", "async function",
        "function ", "class ", "app.", "//", "return ",
        "interface ", "await ", "for (", "  //"
    )

    for line in lines:
        raw = line.rstrip()

        if not raw:
            if in_code:
                code.append("")
            continue

        stripped = raw.strip()

        # Detect code blocks
        is_code = (
            stripped.startswith(code_markers)
            or stripped.startswith("}") 
            or stripped.startswith("{")
            or re.match(r"^[A-Za-z_][A-Za-z0-9_]*\s*=", stripped)
        )

        if is_code:
            if not in_code:
                in_code = True
                code = []
            code.append(raw)
            continue

        if in_code:
            result.append("<pre><code>" + esc("\n".join(code)) + "</code></pre>")
            code = []
            in_code = False

        if stripped in [
            "WHAT YOU WILL LEARN",
            "ARCHITECT'S RULE",
            "COMMON MISTAKE",
            "PRODUCTION TIP",
            "KEY TAKEAWAYS",
            "QUICK REVIEW",
            "ARCHITECT'S CHECKLIST",
            "What It Means",
            "Why It Matters",
            "The Flaw of Averages",
            "Quantifying Systems: Back-of-the-Envelope Estimation",
            "Practical Example: Managing System Boundaries",
        ]:
            result.append(f"<h3>{esc(stripped)}</h3>")
        elif stripped.startswith("•"):
            result.append(f"<li>{esc(stripped[1:].strip())}</li>")
        elif stripped.startswith("☐"):
            result.append(f"<li class='check'>{esc(stripped)}</li>")
        else:
            result.append(f"<p>{esc(stripped)}</p>")

    if in_code:
        result.append("<pre><code>" + esc("\n".join(code)) + "</code></pre>")

    return "\n".join(result)

chapter_html = []

for num, (title, content) in enumerate(parts, 1):
    chapter_html.append(f"""
<section class="chapter">
<div class="chapter-number">CHAPTER {num:02d}</div>
<h1>{html.escape(title)}</h1>
{format_content(content)}
</section>
""")

doc = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>LearnForge — System Architecture &amp; Clean Code</title>

<style>
@page {{
  size: A4;
  margin: 18mm 17mm 20mm 17mm;

  @bottom-center {{
    content: "LearnForge • System Architecture & Clean Code • 2026";
    font-size: 7.5pt;
    color: #666;
  }}
}}

* {{
  box-sizing: border-box;
}}

body {{
  font-family: "DejaVu Sans", sans-serif;
  color: #172033;
  font-size: 9.7pt;
  line-height: 1.48;
  margin: 0;
}}

.cover {{
  page-break-after: always;
  min-height: 250mm;
  display: flex;
  flex-direction: column;
  justify-content: center;
  text-align: center;
}}

.cover .brand {{
  font-size: 11pt;
  letter-spacing: 3px;
  font-weight: bold;
  margin-bottom: 25mm;
}}

.cover h1 {{
  font-size: 30pt;
  line-height: 1.1;
  margin: 0 0 10mm;
}}

.cover h2 {{
  font-size: 13pt;
  line-height: 1.5;
  font-weight: normal;
}}

.cover .edition {{
  margin-top: 18mm;
  font-size: 11pt;
  font-weight: bold;
}}

.cover .author {{
  margin-top: 12mm;
}}

.legal {{
  page-break-after: always;
}}

.toc {{
  page-break-after: always;
}}

.toc h1 {{
  font-size: 22pt;
}}

.toc ol {{
  padding-left: 25px;
}}

.toc li {{
  margin: 7px 0;
  font-size: 10.5pt;
}}

.chapter {{
  page-break-before: always;
}}

.chapter-number {{
  font-size: 9pt;
  letter-spacing: 3px;
  font-weight: bold;
  margin-bottom: 5mm;
}}

.chapter h1 {{
  font-size: 23pt;
  line-height: 1.15;
  margin: 0 0 8mm;
}}

.chapter h3 {{
  font-size: 10pt;
  letter-spacing: 1px;
  margin-top: 8mm;
  margin-bottom: 3mm;
  border-bottom: 1px solid #ddd;
  padding-bottom: 2mm;
}}

.chapter p {{
  margin: 0 0 4mm;
}}

pre {{
  font-family: "DejaVu Sans Mono", monospace;
  font-size: 7.5pt;
  line-height: 1.35;
  background: #f4f5f7;
  border: 1px solid #ddd;
  padding: 4mm;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  page-break-inside: avoid;
}}

li {{
  margin-bottom: 2mm;
}}

.check {{
  list-style: none;
}}

section {{
  orphans: 3;
  widows: 3;
}}
</style>
</head>

<body>

<section class="cover">
  <div class="brand">LEARNFORGE • ENGINEERING HANDBOOK 2026</div>

  <h1>SYSTEM ARCHITECTURE<br>&amp; CLEAN CODE</h1>

  <h2>
    A Practical Mindset-First Blueprint for Building
    Scalable, Maintainable, and Production-Ready Software Systems
  </h2>

  <div class="edition">EXPANDED DIGITAL EDITION — 2026</div>

  <div class="author">
    <strong>Senior Software Architecture Group</strong><br>
    Software Engineers • Tech Leads • System Architects
  </div>
</section>

<section class="legal">
  <h1>Copyright &amp; Legal Disclaimer</h1>
  <p>
    System Architecture &amp; Clean Code: A Practical Mindset-First Blueprint
    for Building Scalable, Maintainable, and Production-Ready Software Systems
    (Expanded Digital Edition 2026).
  </p>
  <p>
    Copyright © 2026. All rights reserved. No part of this publication may be
    reproduced, distributed, or transmitted in any form without prior written
    permission of the publisher.
  </p>
</section>

<section class="toc">
  <h1>Table of Contents</h1>
  <ol>
    <li>From Coder to Architect</li>
    <li>The Foundations of Good Architecture</li>
    <li>Requirements Before Architecture</li>
    <li>Scalability</li>
    <li>Performance, Latency and Throughput</li>
  </ol>
</section>

{''.join(chapter_html)}

</body>
</html>
"""

out.write_text(doc, encoding="utf-8")
print("HTML CREATED:")
print(out)
