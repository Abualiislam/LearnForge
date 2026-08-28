from pathlib import Path
import re, html, shutil, subprocess

BASE = Path("CHAPTER_AUDIT")

sources = [
    BASE / "PART_1_CH01-09.txt",
    BASE / "PART_2_CH10-17.txt",
    BASE / "PART_3_CH18-25.txt",
]

OUT_HTML = Path("System_Architecture_and_Clean_Code_Expanded_2026_V2.html")
OUT_PDF  = Path("System_Architecture_and_Clean_Code_Expanded_2026_V2.pdf")

# ------------------------------------------------------------
# READ ONLY — ORIGINAL SOURCES ARE NEVER MODIFIED
# ------------------------------------------------------------

text = "\n\n".join(
    p.read_text(encoding="utf-8", errors="ignore")
    for p in sources
)

# Normalize attached page/header chapter markers
text = re.sub(
    r'(?i)(?:LEARNFORGE\s+SYSTEM\s+ARCHITECTURE\s*&\s*CLEAN\s+CODE)?\s*CHAPTER\s+0*(\d{1,2})\b',
    lambda m: f"\n[[CHAPTER:{int(m.group(1)):02d}]]",
    text
)

# Also catch explicit Chapter XX
text = re.sub(
    r'(?im)^\s*CHAPTER\s+0*(\d{1,2})(?:\s*[-:—.]?\s*)(.*)$',
    lambda m: (
        f"\n[[CHAPTER:{int(m.group(1)):02d}]] "
        f"{m.group(2).strip()}\n"
    ),
    text
)

# ------------------------------------------------------------
# KNOWN CHAPTER TITLES
# ------------------------------------------------------------

chapter_titles = {
    1: "From Coder to Architect",
    2: "Architectural Thinking",
    3: "Architecture Principles",
    4: "Architectural Patterns",
    5: "System Design Foundations",
    6: "Modular Architecture",
    7: "Service Boundaries",
    8: "Distributed Systems",
    9: "Event-Driven Architecture",
    10: "API Architecture",
    11: "Object-Oriented Design",
    12: "Clean Code & Design Principles",
    13: "API Design & Evolution",
    14: "Data Modeling",
    15: "Database Architecture",
    16: "Security Architecture",
    17: "Capacity & Resource Planning",
    18: "Scalability & Performance Architecture",
    19: "Reliability & Resilience Architecture",
    20: "Observability & Operations",
    21: "Testing Architecture",
    22: "Deployment & Delivery Architecture",
    23: "Infrastructure & Production Systems",
    24: "Practical System Design",
    25: "Architecture Patterns & Practical System Design",
}

# ------------------------------------------------------------
# SPLIT INTO CHAPTERS
# ------------------------------------------------------------

chapter_re = re.compile(
    r'\[\[CHAPTER:(\d{2})\]\]',
    re.I
)

matches = list(chapter_re.finditer(text))

chapters = []

for i, m in enumerate(matches):
    num = int(m.group(1))

    start = m.end()
    end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

    content = text[start:end].strip()

    # Remove duplicated page headers
    content = re.sub(
        r'(?im)LEARNFORGE\s*[•·]\s*Engineering Handbook\s*[•·]\s*2026',
        '',
        content
    )

    content = re.sub(
        r'(?im)SYSTEM\s+ARCHITECTURE\s*&\s*CLEAN\s+CODE',
        '',
        content
    )

    content = re.sub(
        r'(?im)LEARNFORGE',
        '',
        content
    )

    content = re.sub(r'\n{3,}', '\n\n', content).strip()

    chapters.append((num, content))

# Deduplicate chapter numbers while preserving first occurrence
unique = {}
for num, content in chapters:
    if num not in unique:
        unique[num] = content
    else:
        # If duplicate marker accidentally occurred, append content
        if content.strip():
            unique[num] += "\n\n" + content

chapters = [(n, unique[n]) for n in sorted(unique)]

# ------------------------------------------------------------
# HEADING DETECTION
# ------------------------------------------------------------

heading_terms = {
    "WHAT YOU WILL LEARN",
    "WHAT IT MEANS",
    "KEY TAKEAWAYS",
    "ARCHITECT'S RULE",
    "ARCHITECTS RULE",
    "COMMON MISTAKE",
    "PRODUCTION TIP",
    "PRACTICAL CHECKLIST",
    "WHY IT MATTERS",
    "DESIGN CONSIDERATIONS",
    "SUMMARY",
}

def render_content(content):
    lines = content.splitlines()
    out = []

    paragraph = []
    code = []

    def flush_paragraph():
        if paragraph:
            s = " ".join(x.strip() for x in paragraph).strip()
            if s:
                out.append(
                    f"<p>{html.escape(s)}</p>"
                )
            paragraph.clear()

    def flush_code():
        if code:
            out.append(
                '<pre class="code"><code>'
                + html.escape("\n".join(code))
                + '</code></pre>'
            )
            code.clear()

    in_code = False

    for raw in lines:
        line = raw.strip()

        if not line:
            if in_code:
                flush_code()
            else:
                flush_paragraph()
            continue

        if line.startswith("```"):
            flush_paragraph()

            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code.append(raw)
            continue

        # Known section headings
        clean_upper = re.sub(r'[^A-Z0-9 &\'-]', '', line.upper()).strip()

        if clean_upper in heading_terms:
            flush_paragraph()
            out.append(
                f'<h2>{html.escape(line)}</h2>'
            )
            continue

        # Numbered headings such as:
        # 1. Why Database Architecture Matters
        # 12. Backpressure
        if re.match(r'^\d{1,2}\.\s+[A-Z][A-Za-z0-9 &,\-\'()]+$', line):
            flush_paragraph()
            out.append(
                f'<h3>{html.escape(line)}</h3>'
            )
            continue

        # Figure captions
        if re.match(r'^Figure\s+\d+(?:\.\d+)?\s*[—:-]', line, re.I):
            flush_paragraph()
            out.append(
                f'<div class="figure-caption">{html.escape(line)}</div>'
            )
            continue

        # Bullets
        if re.match(r'^[•◦▪●*-]\s+', line):
            flush_paragraph()
            item = re.sub(r'^[•◦▪●*-]\s+', '', line)
            out.append(
                f'<div class="bullet">• {html.escape(item)}</div>'
            )
            continue

        # Table-ish lines
        if "|" in line and line.count("|") >= 2:
            flush_paragraph()
            cells = [
                x.strip()
                for x in line.strip("|").split("|")
            ]

            out.append(
                '<table><tr>' +
                ''.join(
                    f'<td>{html.escape(c)}</td>'
                    for c in cells
                ) +
                '</tr></table>'
            )
            continue

        # Code-like lines
        code_signal = (
            line.startswith((
                "const ", "let ", "var ", "import ",
                "export ", "function ", "class ",
                "app.", "curl ", "npm ", "SELECT ",
                "CREATE ", "$ "
            ))
            or "=>" in line
            or re.search(r'[{};]$', line)
        )

        if code_signal and len(line) < 500:
            flush_paragraph()
            code.append(raw)
            in_code = True
            continue

        paragraph.append(line)

    flush_code()
    flush_paragraph()

    return "\n".join(out)

# ------------------------------------------------------------
# BUILD CHAPTER HTML
# ------------------------------------------------------------

chapter_html = []
toc_rows = []

for num, content in chapters:
    title = chapter_titles.get(
        num,
        f"Chapter {num}"
    )

    rendered = render_content(content)

    chapter_html.append(f'''
<section class="chapter-open" id="chapter-{num}">
    <div class="chapter-open-inner">
        <div class="chapter-label">CHAPTER {num:02d}</div>
        <div class="chapter-rule"></div>
        <h1>{html.escape(title)}</h1>
        <div class="chapter-brand">LEARNFORGE</div>
        <div class="chapter-subtitle">
            System Architecture &amp; Clean Code
        </div>
    </div>
</section>

<section class="chapter-content">
    <div class="chapter-header-small">
        CHAPTER {num:02d} · {html.escape(title)}
    </div>
    {rendered}
</section>
''')

    toc_rows.append(
        f'''
        <div class="toc-row">
            <span>{num:02d}. {html.escape(title)}</span>
            <span class="toc-dots"></span>
        </div>
        '''
    )

# ------------------------------------------------------------
# COMPLETE HTML
# ------------------------------------------------------------

html_doc = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">

<title>
System Architecture &amp; Clean Code — Expanded Edition 2026
</title>

<style>

/* ============================================================
   PAGE
   ============================================================ */

@page {{
    size: A4;
    margin: 20mm 18mm 22mm 18mm;

    @bottom-center {{
        content: counter(page);
        font-family: Arial, sans-serif;
        font-size: 8pt;
        color: #718096;
    }}
}}

@page chapter {{
    margin: 0;
    @bottom-center {{
        content: "";
    }}
}}

/* ============================================================
   GLOBAL
   ============================================================ */

* {{
    box-sizing: border-box;
}}

html, body {{
    margin: 0;
    padding: 0;
}}

body {{
    font-family:
        Georgia,
        "Times New Roman",
        serif;

    font-size: 10.8pt;
    line-height: 1.62;

    color: #172033;

    background: white;
}}

/* ============================================================
   COVER
   ============================================================ */

.cover {{
    page: chapter;

    height: 297mm;

    page-break-after: always;

    display: flex;
    flex-direction: column;

    justify-content: center;
    align-items: center;

    text-align: center;

    padding: 30mm;
}}

.cover h1 {{
    font-family:
        Arial,
        Helvetica,
        sans-serif;

    font-size: 32pt;
    line-height: 1.15;

    color: #102a43;

    margin: 0 0 15pt 0;
}}

.cover h2 {{
    font-size: 17pt;
    font-weight: normal;

    color: #486581;

    margin: 0 0 28pt 0;
}}

.cover-brand {{
    font-family: Arial, sans-serif;

    font-size: 10pt;

    letter-spacing: 3px;

    color: #627d98;

    text-transform: uppercase;
}}

/* ============================================================
   TABLE OF CONTENTS
   ============================================================ */

.toc {{
    page-break-after: always;

    padding-top: 8mm;
}}

.toc h1 {{
    page-break-before: auto;

    font-family: Arial, sans-serif;

    font-size: 25pt;

    color: #102a43;

    border-bottom: 1px solid #bcccdc;

    padding-bottom: 9pt;

    margin-bottom: 25pt;
}}

.toc-row {{
    display: flex;

    align-items: baseline;

    width: 100%;

    margin: 0 0 11pt 0;

    font-family: Arial, sans-serif;

    font-size: 10.5pt;

    color: #243b53;
}}

.toc-dots {{
    flex: 1;

    border-bottom: 1px dotted #9fb3c8;

    margin: 0 8pt 4pt 8pt;
}}

/* ============================================================
   CHAPTER OPENING PAGE
   ============================================================ */

.chapter-open {{
    page: chapter;

    height: 297mm;

    page-break-before: always;
    page-break-after: always;

    display: flex;

    align-items: center;
    justify-content: center;

    text-align: center;

    padding: 35mm 25mm;
}}

.chapter-open-inner {{
    width: 100%;

    max-width: 170mm;

    margin: auto;
}}

.chapter-label {{
    font-family: Arial, Helvetica, sans-serif;

    font-size: 17pt;

    font-weight: bold;

    letter-spacing: 5px;

    color: #627d98;

    margin-bottom: 17pt;
}}

.chapter-rule {{
    width: 55mm;

    height: 2px;

    background: #829ab1;

    margin: 0 auto 22pt auto;
}}

.chapter-open h1 {{
    font-family:
        Arial,
        Helvetica,
        sans-serif;

    font-size: 34pt;

    line-height: 1.15;

    color: #102a43;

    margin: 0 auto 25pt auto;

    border: 0;

    padding: 0;

    max-width: 155mm;
}}

.chapter-brand {{
    font-family: Arial, sans-serif;

    font-size: 9pt;

    letter-spacing: 4px;

    color: #486581;

    margin-bottom: 7pt;
}}

.chapter-subtitle {{
    font-size: 10pt;

    color: #829ab1;

    letter-spacing: 1px;
}}

/* ============================================================
   CHAPTER CONTENT
   ============================================================ */

.chapter-content {{
    page-break-before: auto;

    padding-top: 2mm;
}}

.chapter-header-small {{
    font-family: Arial, sans-serif;

    font-size: 8.5pt;

    letter-spacing: 1.4px;

    text-transform: uppercase;

    color: #829ab1;

    border-bottom: 1px solid #d9e2ec;

    padding-bottom: 5pt;

    margin-bottom: 18pt;
}}

h2 {{
    font-family:
        Arial,
        Helvetica,
        sans-serif;

    font-size: 15pt;

    line-height: 1.3;

    color: #243b53;

    margin: 20pt 0 9pt 0;

    page-break-after: avoid;
}}

h3 {{
    font-family:
        Arial,
        Helvetica,
        sans-serif;

    font-size: 12pt;

    line-height: 1.35;

    color: #334e68;

    margin: 16pt 0 7pt 0;

    page-break-after: avoid;
}}

p {{
    margin: 0 0 10pt 0;

    text-align: justify;

    orphans: 3;
    widows: 3;
}}

.bullet {{
    margin: 0 0 6pt 13pt;

    padding-left: 8pt;

    line-height: 1.5;
}}

.figure-caption {{
    margin: 12pt 0 14pt 0;

    padding: 9pt 11pt;

    border-left: 3px solid #829ab1;

    background: #f7f9fc;

    font-family: Arial, sans-serif;

    font-size: 9.2pt;

    color: #486581;

    page-break-inside: avoid;
}}

.code {{
    font-family:
        "Courier New",
        monospace;

    font-size: 8.4pt;

    line-height: 1.4;

    background: #f5f7fa;

    border: 1px solid #d9e2ec;

    border-radius: 4px;

    padding: 10pt;

    margin: 11pt 0 14pt 0;

    white-space: pre-wrap;

    page-break-inside: avoid;
}}

table {{
    width: 100%;

    border-collapse: collapse;

    margin: 10pt 0 14pt 0;

    font-size: 9pt;

    page-break-inside: avoid;
}}

td {{
    border: 1px solid #bcccdc;

    padding: 5pt 7pt;

    vertical-align: top;
}}

</style>
</head>

<body>

<!-- COVER -->

<section class="cover">

    <h1>
        System Architecture<br>
        &amp; Clean Code
    </h1>

    <h2>
        Expanded Edition 2026
    </h2>

    <div class="cover-brand">
        LearnForge
    </div>

</section>


<!-- TABLE OF CONTENTS -->

<section class="toc">

    <h1>Table of Contents</h1>

    {''.join(toc_rows)}

</section>


<!-- CHAPTERS -->

{''.join(chapter_html)}

</body>
</html>
'''

OUT_HTML.write_text(html_doc, encoding="utf-8")

print("=" * 72)
print("LEARNFORGE — V2 PUBLICATION LAYOUT BUILD")
print("=" * 72)
print("Original sources modified : 0")
print("Original chunks modified  : 0")
print("Original PDF modified     : 0")
print("Chapters detected         :", len(chapters))
print("HTML output               :", OUT_HTML)
print("=" * 72)

# Build PDF
try:
    subprocess.run(
        [
            "weasyprint",
            str(OUT_HTML),
            str(OUT_PDF)
        ],
        check=True
    )

    print("PDF output                :", OUT_PDF)

except Exception as e:
    print("PDF BUILD ERROR:", e)
    raise

print("=" * 72)
print("V2 LAYOUT BUILD: PASS")
print("=" * 72)
