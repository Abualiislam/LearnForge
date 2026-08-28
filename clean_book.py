from pathlib import Path
import re

src = Path.home() / "book_full.txt"
out = Path.home() / "LearnForge" / "clean_book.html"

text = src.read_text(encoding="utf-8")

# Remove the accidental AI-generation/source-instruction text
text = re.sub(
    r"except inDue to strict output character limits.*?```html",
    "except in",
    text,
    flags=re.S | re.I,
)

# Remove the old 25-chapter table of contents
start = text.find("Table of Contents")
end = text.find("System Architecture & Clean Code (2026)", start + 20)

if start != -1 and end != -1:
    text = text[:start] + text[end:]

# Remove repeated PDF footer/page-number lines
text = re.sub(
    r"System Architecture & Clean Code 2026\s+\d+\s*",
    "",
    text,
)

# Escape HTML
import html
safe = html.escape(text)

html_doc = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>System Architecture & Clean Code — Expanded Digital Edition 2026</title>
<style>
@page {{
  size: A4;
  margin: 20mm 18mm 20mm 18mm;
  @bottom-center {{
    content: "System Architecture & Clean Code — 2026";
    font-size: 8pt;
  }}
}}

body {{
  font-family: "DejaVu Sans", sans-serif;
  font-size: 10.5pt;
  line-height: 1.55;
  color: #111;
}}

pre {{
  font-family: "DejaVu Sans Mono", monospace;
  font-size: 8.5pt;
  line-height: 1.4;
  white-space: pre-wrap;
  background: #f3f4f6;
  padding: 10px;
  border-radius: 5px;
}}

h1, h2, h3 {{
  page-break-after: avoid;
}}

.cover {{
  page-break-after: always;
  text-align: center;
  padding-top: 55mm;
}}

.chapter {{
  page-break-before: always;
}}

.small {{
  font-size: 9pt;
}}

.toc {{
  page-break-after: always;
}}

</style>
</head>
<body>

<section class="cover">
<h1>SYSTEM ARCHITECTURE &amp;<br>CLEAN CODE</h1>
<h2>A Practical Mindset-First Blueprint for Building Scalable,
Maintainable, and Production-Ready Software Systems</h2>
<p><strong>Expanded Digital Edition — 2026</strong></p>
<p>Author: Senior Software Architecture Group</p>
<p>Target Audience: Software Engineers, Tech Leads, System Architects</p>
</section>

<section>
<h2>Copyright &amp; Legal Disclaimer</h2>
<p>System Architecture &amp; Clean Code: A Practical Mindset-First Blueprint for Building
Scalable, Maintainable, and Production-Ready Software Systems.</p>
<p>Copyright © 2026. All rights reserved. No part of this publication may be reproduced,
distributed, or transmitted without prior written permission of the publisher.</p>
</section>

<section class="toc">
<h2>Table of Contents</h2>
<ol>
<li>From Coder to Architect</li>
<li>The Foundations of Good Architecture</li>
<li>Requirements Before Architecture</li>
<li>Scalability</li>
<li>Performance, Latency and Throughput</li>
</ol>
</section>

<section>
<h2>Clean Edition — Five Complete Chapters</h2>
<p>This edition contains five focused chapters covering the foundations of software
architecture, requirements, scalability, and performance.</p>
</section>

<section>
<pre>{safe}</pre>
</section>

</body>
</html>
"""

out.write_text(html_doc, encoding="utf-8")
print(f"Created: {out}")
