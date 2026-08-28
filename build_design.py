from pathlib import Path
import re
import html

src = Path.home() / "book_full.txt"
html_out = Path.home() / "LearnForge" / "LearnForge_System_Architecture_Clean_Code_2026_DESIGN.html"
pdf_out = Path.home() / "LearnForge" / "LearnForge_System_Architecture_Clean_Code_2026_DESIGN.pdf"

text = src.read_text(encoding="utf-8")

# ============================================================
# CLEAN SOURCE
# ============================================================

# Remove accidental AI-generation/source-instruction text
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

# Remove CHAPTER labels
text = re.sub(r"\s*CHAPTER 0[1-5]\s*", "\n", text)

chapters = [
    "From Coder to Architect",
    "The Foundations of Good Architecture",
    "Requirements Before Architecture",
    "Scalability",
    "Performance, Latency and Throughput",
]

positions = [text.find(x) for x in chapters]
parts = []

for i, title in enumerate(chapters):
    start = positions[i]
    if start == -1:
        continue
    end = positions[i + 1] if i + 1 < len(positions) and positions[i + 1] != -1 else len(text)
    parts.append((i + 1, title, text[start:end]))


# ============================================================
# CONTENT FORMATTER
# ============================================================

SPECIAL = {
    "WHAT YOU WILL LEARN": "learn",
    "ARCHITECT'S RULE": "rule",
    "COMMON MISTAKE": "mistake",
    "PRODUCTION TIP": "tip",
    "KEY TAKEAWAYS": "takeaways",
    "QUICK REVIEW": "review",
    "ARCHITECT'S CHECKLIST": "checklist",
}

def esc(s):
    return html.escape(s.strip())

def looks_like_code(line):
    s = line.strip()

    if not s:
        return False

    patterns = [
        r"^(import|export|const|let|var|class|interface|async|function)\b",
        r"^(return|await|throw|try|catch|for|if|else)\b",
        r"^(app|redis|db|stripe)\.",
        r"^//",
        r"^[{}]\s*$",
        r"^[A-Za-z_][A-Za-z0-9_]*\s*=",
        r"^\s*}\s*[,;]?$",
    ]

    return any(re.search(p, s) for p in patterns)


def format_content(content):
    lines = content.splitlines()
    out = []
    i = 0

    while i < len(lines):
        raw = lines[i].rstrip()
        s = raw.strip()

        if not s:
            i += 1
            continue

        # Special callout sections
        if s in SPECIAL:
            kind = SPECIAL[s]
            box = []
            i += 1

            while i < len(lines):
                nxt = lines[i].strip()

                if nxt in SPECIAL:
                    break

                if nxt:
                    box.append(lines[i].strip())

                i += 1

            title = s.title()

            body = []

            for item in box:
                if item.startswith("•"):
                    body.append(f"<li>{esc(item[1:].strip())}</li>")
                elif item.startswith("☐"):
                    body.append(f"<li class='check-item'>{esc(item)}</li>")
                else:
                    body.append(f"<p>{esc(item)}</p>")

            out.append(
                f"""
                <div class="callout {kind}">
                    <div class="callout-title">{html.escape(title)}</div>
                    <div class="callout-body">
                        {''.join(body)}
                    </div>
                </div>
                """
            )
            continue

        # Code block detection
        if looks_like_code(raw):
            code = [raw]
            i += 1

            while i < len(lines):
                nxt = lines[i].rstrip()

                if not nxt:
                    # Keep one blank line if still inside code
                    if i + 1 < len(lines) and looks_like_code(lines[i + 1]):
                        code.append("")
                        i += 1
                        continue
                    break

                if looks_like_code(nxt):
                    code.append(nxt)
                    i += 1
                else:
                    break

            out.append(
                "<pre><code>" +
                esc("\n".join(code)) +
                "</code></pre>"
            )
            continue

        # Section headings
        if s in [
            "What It Means",
            "Why It Matters",
            "The Flaw of Averages",
            "Quantifying Systems: Back-of-the-Envelope Estimation",
            "Practical Example: Managing System Boundaries",
        ]:
            out.append(f"<h2 class='section-heading'>{esc(s)}</h2>")
            i += 1
            continue

        # Bullet
        if s.startswith("•"):
            items = [s[1:].strip()]
            i += 1

            while i < len(lines):
                nxt = lines[i].strip()
                if nxt.startswith("•"):
                    items.append(nxt[1:].strip())
                    i += 1
                else:
                    break

            out.append(
                "<ul>" +
                "".join(f"<li>{esc(x)}</li>" for x in items) +
                "</ul>"
            )
            continue

        # Checkbox
        if s.startswith("☐"):
            items = [s]
            i += 1

            while i < len(lines):
                nxt = lines[i].strip()
                if nxt.startswith("☐"):
                    items.append(nxt)
                    i += 1
                else:
                    break

            out.append(
                "<ul class='checklist'>" +
                "".join(f"<li>{esc(x)}</li>" for x in items) +
                "</ul>"
            )
            continue

        # Ignore isolated old layout fragments
        if re.fullmatch(r"[A-Z]{1,5}", s):
            i += 1
            continue

        # Normal paragraph
        out.append(f"<p>{esc(s)}</p>")
        i += 1

    return "\n".join(out)


# ============================================================
# CHAPTER HTML
# ============================================================

chapter_html = []

for num, title, content in parts:
    chapter_html.append(
        f"""
<section class="chapter">

    <div class="chapter-top">
        <span class="chapter-label">CHAPTER {num:02d}</span>
        <span class="chapter-line"></span>
    </div>

    <h1>{html.escape(title)}</h1>

    <div class="chapter-accent"></div>

    {format_content(content)}

</section>
"""
    )


# ============================================================
# FINAL HTML
# ============================================================

document = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">

<title>LearnForge — System Architecture &amp; Clean Code</title>

<style>

/* ============================================================
   PAGE
   ============================================================ */

@page {{
    size: A4;
    margin: 17mm 16mm 19mm 16mm;

    @bottom-left {{
        content: "LEARNFORGE";
        color: #64748b;
        font-size: 7pt;
        font-weight: bold;
        letter-spacing: 1px;
    }}

    @bottom-right {{
        content: counter(page);
        color: #64748b;
        font-size: 8pt;
    }}
}}


/* ============================================================
   GLOBAL
   ============================================================ */

* {{
    box-sizing: border-box;
}}

html {{
    background: #ffffff;
}}

body {{
    margin: 0;
    font-family: "DejaVu Sans", sans-serif;
    color: #172033;
    font-size: 9.5pt;
    line-height: 1.48;
}}

p {{
    margin: 0 0 3.5mm;
}}

h1, h2, h3 {{
    page-break-after: avoid;
}}

ul {{
    margin: 2mm 0 5mm 6mm;
    padding-left: 5mm;
}}

li {{
    margin-bottom: 1.7mm;
}}

strong {{
    font-weight: 700;
}}


/* ============================================================
   COVER
   ============================================================ */

.cover {{
    page-break-after: always;
    height: 250mm;
    position: relative;
    overflow: hidden;

    background:
        linear-gradient(145deg, #07111f 0%, #0b1830 52%, #102b47 100%);

    color: white;
    padding: 22mm 18mm;
}}

.cover::before {{
    content: "";
    position: absolute;
    width: 125mm;
    height: 125mm;
    border: 1px solid rgba(34, 211, 238, .25);
    border-radius: 50%;
    right: -55mm;
    top: -45mm;
}}

.cover::after {{
    content: "";
    position: absolute;
    width: 95mm;
    height: 95mm;
    border: 1px solid rgba(56, 189, 248, .18);
    border-radius: 50%;
    left: -45mm;
    bottom: -35mm;
}}

.cover-inner {{
    position: relative;
    z-index: 2;
}}

.cover-brand {{
    display: inline-block;
    border: 1px solid rgba(103, 232, 249, .5);
    padding: 3mm 5mm;
    font-size: 8pt;
    letter-spacing: 2.5px;
    color: #67e8f9;
    font-weight: bold;
}}

.cover h1 {{
    font-size: 31pt;
    line-height: 1.05;
    margin: 32mm 0 8mm;
    letter-spacing: -1px;
}}

.cover h2 {{
    font-size: 12.5pt;
    line-height: 1.55;
    font-weight: normal;
    color: #cbd5e1;
    max-width: 150mm;
}}

.cover-edition {{
    margin-top: 17mm;
    color: #67e8f9;
    font-size: 9pt;
    letter-spacing: 2px;
    font-weight: bold;
}}

.cover-author {{
    margin-top: 24mm;
    font-size: 9pt;
    color: #cbd5e1;
}}

.cover-grid {{
    position: absolute;
    left: 18mm;
    right: 18mm;
    bottom: 24mm;
    height: 38mm;
    border-top: 1px solid rgba(103,232,249,.25);
    border-bottom: 1px solid rgba(103,232,249,.15);
}}

.cover-grid span {{
    display: inline-block;
    margin-top: 11mm;
    margin-right: 12mm;
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 8pt;
    color: #94a3b8;
}}


/* ============================================================
   LEGAL
   ============================================================ */

.legal {{
    page-break-after: always;
    padding-top: 20mm;
}}

.legal h1 {{
    color: #0f2742;
    font-size: 22pt;
    margin-bottom: 10mm;
}}

.legal p {{
    color: #475569;
    line-height: 1.7;
}}


/* ============================================================
   TOC
   ============================================================ */

.toc {{
    page-break-after: always;
    padding-top: 8mm;
}}

.toc-kicker {{
    color: #0891b2;
    font-size: 8pt;
    letter-spacing: 2px;
    font-weight: bold;
}}

.toc h1 {{
    font-size: 25pt;
    color: #0f2742;
    margin: 4mm 0 12mm;
}}

.toc-list {{
    padding: 0;
    margin: 0;
    list-style: none;
}}

.toc-list li {{
    margin: 0;
    padding: 5mm 0;
    border-bottom: 1px solid #dbe4ee;
    font-size: 10.5pt;
}}

.toc-num {{
    display: inline-block;
    width: 14mm;
    color: #0891b2;
    font-weight: bold;
    font-family: "DejaVu Sans Mono", monospace;
}}

.toc-footer {{
    margin-top: 18mm;
    padding: 7mm;
    background: #eef9fc;
    border-left: 3px solid #06b6d4;
    color: #334155;
}}


/* ============================================================
   CHAPTER
   ============================================================ */

.chapter {{
    page-break-before: always;
}}

.chapter-top {{
    display: flex;
    align-items: center;
    gap: 4mm;
    margin-bottom: 5mm;
}}

.chapter-label {{
    color: #0891b2;
    font-size: 8pt;
    font-weight: bold;
    letter-spacing: 2px;
}}

.chapter-line {{
    height: 1px;
    background: #cbd5e1;
    flex: 1;
}}

.chapter h1 {{
    color: #0b1f35;
    font-size: 24pt;
    line-height: 1.12;
    margin: 0;
}}

.chapter-accent {{
    width: 25mm;
    height: 2px;
    margin: 5mm 0 8mm;
    background: #06b6d4;
}}

.section-heading {{
    color: #0f2742;
    font-size: 12pt;
    margin: 7mm 0 3mm;
    padding-left: 3mm;
    border-left: 3px solid #06b6d4;
}}

.chapter ul {{
    padding-left: 6mm;
}}


/* ============================================================
   CALLOUTS
   ============================================================ */

.callout {{
    margin: 6mm 0;
    padding: 5mm 6mm;
    border-radius: 2mm;
    page-break-inside: avoid;
}}

.callout-title {{
    font-size: 8pt;
    letter-spacing: 1.5px;
    font-weight: bold;
    margin-bottom: 2.5mm;
    text-transform: uppercase;
}}

.callout-body p {{
    margin-bottom: 2mm;
}}

.callout-body p:last-child {{
    margin-bottom: 0;
}}

.callout ul {{
    margin-bottom: 0;
}}

.learn {{
    background: #eef9fc;
    border-left: 4px solid #06b6d4;
}}

.learn .callout-title {{
    color: #087f9b;
}}

.rule {{
    background: #eff6ff;
    border-left: 4px solid #3b82f6;
}}

.rule .callout-title {{
    color: #2563eb;
}}

.mistake {{
    background: #fff7ed;
    border-left: 4px solid #f97316;
}}

.mistake .callout-title {{
    color: #c2410c;
}}

.tip {{
    background: #f0fdf4;
    border-left: 4px solid #22c55e;
}}

.tip .callout-title {{
    color: #15803d;
}}

.takeaways {{
    background: #f5f3ff;
    border-left: 4px solid #8b5cf6;
}}

.takeaways .callout-title {{
    color: #6d28d9;
}}

.review {{
    background: #f8fafc;
    border-left: 4px solid #64748b;
}}

.review .callout-title {{
    color: #475569;
}}

.checklist {{
    background: #f8fafc;
    border-left: 4px solid #0f2742;
}}

.checklist .callout-title {{
    color: #0f2742;
}}


/* ============================================================
   CODE
   ============================================================ */

pre {{
    page-break-inside: avoid;
    margin: 5mm 0;
    padding: 5mm;
    background: #0b1322;
    color: #d8f7ff;
    border-radius: 2mm;
    border: 1px solid #18324d;
    box-shadow: 0 2px 5px rgba(0,0,0,.08);
    white-space: pre-wrap;
    overflow-wrap: anywhere;
}}

code {{
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 7.2pt;
    line-height: 1.4;
}}


/* ============================================================
   CHECKLIST
   ============================================================ */

.checklist {{
    list-style: none;
    margin-left: 0;
    padding-left: 0;
}}

.checklist li {{
    padding: 2mm 0 2mm 8mm;
    position: relative;
}}

.checklist li::before {{
    content: "✓";
    position: absolute;
    left: 0;
    color: #0891b2;
    font-weight: bold;
}}

.check-item {{
    list-style: none;
}}


/* ============================================================
   QUALITY
   ============================================================ */

section {{
    orphans: 3;
    widows: 3;
}}

</style>
</head>

<body>

<!-- COVER -->
<section class="cover">
    <div class="cover-inner">

        <div class="cover-brand">
            LEARNFORGE • ENGINEERING HANDBOOK 2026
        </div>

        <h1>
            SYSTEM<br>
            ARCHITECTURE<br>
            &amp; CLEAN CODE
        </h1>

        <h2>
            A Practical Mindset-First Blueprint for Building
            Scalable, Maintainable, and Production-Ready Software Systems
        </h2>

        <div class="cover-edition">
            EXPANDED DIGITAL EDITION — 2026
        </div>

        <div class="cover-author">
            <strong>Senior Software Architecture Group</strong><br>
            Software Engineers • Tech Leads • System Architects
        </div>

    </div>

    <div class="cover-grid">
        <span>CLIENTS</span>
        <span>API GATEWAY</span>
        <span>SERVICES</span>
        <span>DATABASE</span>
        <span>EVENT BUS</span>
    </div>
</section>


<!-- LEGAL -->
<section class="legal">

    <div class="toc-kicker">LEARNFORGE PUBLICATION</div>

    <h1>Copyright &amp; Legal Disclaimer</h1>

    <p>
        <strong>System Architecture &amp; Clean Code</strong>:
        A Practical Mindset-First Blueprint for Building Scalable,
        Maintainable, and Production-Ready Software Systems
        (Expanded Digital Edition 2026).
    </p>

    <p>
        Copyright © 2026. All rights reserved. No part of this publication
        may be reproduced, distributed, or transmitted in any form or by
        any means without prior written permission of the publisher.
    </p>

</section>


<!-- TOC -->
<section class="toc">

    <div class="toc-kicker">CONTENTS</div>

    <h1>Table of Contents</h1>

    <ol class="toc-list">
        <li><span class="toc-num">01</span> From Coder to Architect</li>
        <li><span class="toc-num">02</span> The Foundations of Good Architecture</li>
        <li><span class="toc-num">03</span> Requirements Before Architecture</li>
        <li><span class="toc-num">04</span> Scalability</li>
        <li><span class="toc-num">05</span> Performance, Latency and Throughput</li>
    </ol>

    <div class="toc-footer">
        <strong>Inside this edition</strong><br>
        Architecture mindset • Quality attributes • Requirements
        engineering • Scalability • Performance • Production practices
    </div>

</section>


{''.join(chapter_html)}

</body>
</html>
"""

html_out.write_text(document, encoding="utf-8")

print("HTML created:")
print(html_out)

