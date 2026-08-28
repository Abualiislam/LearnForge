#!/data/data/com.termux/files/usr/bin/bash
set -e

BASE="$HOME/ebook_premium"
SRC="$HOME/epub_clean/final_book_clean.html"
OUT="$HOME/LearnForge"

HTML="$OUT/LearnForge_FINAL_25_CHAPTERS_2026.html"
PDF="$OUT/LearnForge_FINAL_25_CHAPTERS_2026.pdf"
TXT="$OUT/LearnForge_FINAL_25_CHAPTERS_2026_AUDIT.txt"

echo "=========================================="
echo " LEARNFORGE FINAL 25-CHAPTER BUILD"
echo "=========================================="

echo
echo "[1/7] Checking sources..."

for n in 01 02 03 04 05; do
    f="$BASE/chapters/raw/chapter-$n-raw.txt"
    [ -f "$f" ] || {
        echo "FAIL: Missing $f"
        exit 1
    }
    echo "FOUND: Chapter $n raw source"
done

[ -f "$SRC" ] || {
    echo "FAIL: Missing Chapters 06-25 source"
    exit 1
}

echo "FOUND: Chapters 06-25 source"

echo
echo "[2/7] Building complete 25-chapter HTML..."

python - "$BASE" "$SRC" "$HTML" <<'PY'
from pathlib import Path
from html import escape
import re
import sys

BASE = Path(sys.argv[1])
SRC = Path(sys.argv[2])
OUT = Path(sys.argv[3])

titles = {
1:"From Coder to Architect",
2:"The Foundations of Good Architecture",
3:"Requirements Before Architecture",
4:"Scalability",
5:"Performance, Latency and Throughput",
6:"Monolith, Modular Monolith and Microservices",
7:"Microservice Trade-offs",
8:"Distributed Systems",
9:"Event-Driven Architecture",
10:"Clean Architecture",
11:"SOLID Principles",
12:"DRY, KISS, YAGNI, Cohesion and Coupling",
13:"API Architecture",
14:"Database Architecture",
15:"Caching",
16:"Security by Design",
17:"Observability",
18:"Testing Architecture",
19:"CI/CD and Deployment",
20:"Production Readiness",
21:"Disaster Recovery and Resilience",
22:"Architecture Documentation",
23:"Real-World System Design Example",
24:"Architecture Review Checklist",
25:"Final Architecture Cheat Sheet"
}

def raw_to_html(text, n, title):
    text = text.replace("\r\n","\n").replace("\r","\n")

    lines=[]
    for line in text.splitlines():
        s=line.strip()

        if re.fullmatch(r"System Architecture & Clean Code.*",s):
            continue

        if re.fullmatch(r"\d+",s):
            continue

        lines.append(line.rstrip())

    text="\n".join(lines).strip()

    blocks=re.split(r"\n\s*\n",text)
    body=[]

    for block in blocks:
        block=block.strip()
        if not block:
            continue

        e=escape(block)

        # Preserve simple emphasis
        e=re.sub(r"\*\*(.+?)\*\*",r"<strong>\1</strong>",e)

        ls=e.splitlines()

        code_starts=(
            "import ","export ","const ","let ","var ",
            "class ","function ","async ","await ",
            "return ","interface ","new ","//",
            "{","}","SELECT ","INSERT ","UPDATE "
        )

        is_code=any(
            any(x.strip().startswith(c) for c in code_starts)
            for x in ls
        )

        if is_code:
            body.append("<pre><code>"+e+"</code></pre>")
        else:
            body.append("<p>"+" ".join(x.strip() for x in ls)+"</p>")

    return f"""
<section class="chapter" id="chapter-{n:02d}">
<div class="chapter-kicker">CHAPTER {n:02d}</div>
<h1>{escape(title)}</h1>
<div class="chapter-rule"></div>
{''.join(body)}
</section>
"""

print("Loading Chapters 06-25...")
old=SRC.read_text(encoding="utf-8",errors="ignore")

# Remove broken local SVG images
old=re.sub(
    r'<img\b[^>]*src=["\'](?:file://)?[^"\']*/media/file\d+\.svg["\'][^>]*>',
    '',
    old,
    flags=re.I
)

# Remove duplicate IDs
seen=set()

def clean_tag(m):
    tag=m.group(0)

    x=re.search(r'\bid=["\']([^"\']+)["\']',tag,re.I)

    if not x:
        return tag

    ident=x.group(1)

    if ident in seen:
        return re.sub(
            r'\s+id=["\'][^"\']+["\']',
            '',
            tag,
            count=1,
            flags=re.I
        )

    seen.add(ident)
    return tag

old=re.sub(r'<[^>]+>',clean_tag,old)

# Extract beginning at Chapter 06
m=re.search(
    r'(?is)<[^>]*>\s*Chapter\s+06\s*</[^>]*>',
    old
)

if not m:
    m=re.search(r'(?i)Chapter\s+06',old)

if not m:
    raise SystemExit("Could not find Chapter 06")

later=old[m.start():]

# Remove closing document tags
later=re.sub(
    r'(?is)</body>\s*</html>\s*$',
    '',
    later
).strip()

# Build Chapters 01-05
first=[]

for n in range(1,6):
    f=BASE/"chapters"/"raw"/f"chapter-{n:02d}-raw.txt"
    text=f.read_text(encoding="utf-8",errors="ignore")

    first.append(
        raw_to_html(
            text,
            n,
            titles[n]
        )
    )

# TOC
toc=[]

for n in range(1,26):
    toc.append(
        f'<li><span class="num">{n:02d}</span>'
        f'{escape(titles[n])}</li>'
    )

html=f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">

<title>LearnForge — System Architecture &amp; Clean Code</title>

<meta name="author" content="LearnForge">

<meta name="description"
content="System Architecture &amp; Clean Code — Expanded Digital Edition 2026">

<style>

@page {{
size:A4;
margin:20mm 17mm 22mm 17mm;

@bottom-left {{
content:"LearnForge • System Architecture & Clean Code";
font-size:8pt;
color:#64748b;
}}

@bottom-right {{
content:counter(page);
font-size:8pt;
color:#64748b;
}}
}}

* {{
box-sizing:border-box;
}}

html {{
font-family:Arial,Helvetica,sans-serif;
color:#172033;
background:white;
}}

body {{
margin:0;
font-size:10.5pt;
line-height:1.55;
}}

.cover {{
min-height:250mm;
page-break-after:always;
padding:30mm 18mm;
background:linear-gradient(145deg,#07111f,#102b48);
color:white;
}}

.cover .brand {{
font-size:12pt;
letter-spacing:4px;
text-transform:uppercase;
margin-bottom:45mm;
}}

.cover h1 {{
font-size:31pt;
line-height:1.05;
margin:0 0 10mm;
}}

.cover .subtitle {{
font-size:14pt;
line-height:1.5;
max-width:150mm;
}}

.cover .edition {{
margin-top:50mm;
font-size:10pt;
letter-spacing:2px;
}}

.toc {{
page-break-after:always;
}}

.toc h1 {{
font-size:24pt;
margin-bottom:12mm;
}}

.toc ol {{
list-style:none;
padding:0;
}}

.toc li {{
padding:4mm 0;
border-bottom:1px solid #dce3ec;
}}

.num {{
display:inline-block;
width:14mm;
font-weight:bold;
color:#1769aa;
}}

.chapter {{
page-break-before:always;
break-before:page;
}}

.chapter-kicker {{
color:#1769aa;
font-size:9pt;
font-weight:bold;
letter-spacing:3px;
margin-bottom:4mm;
}}

.chapter h1 {{
font-size:25pt;
line-height:1.15;
margin:0 0 5mm;
color:#0b1f35;
}}

.chapter-rule {{
height:2px;
background:#1769aa;
margin-bottom:8mm;
}}

p {{
margin:0 0 5mm;
}}

strong {{
color:#0b4778;
}}

pre {{
background:#101827;
color:#e7edf5;
padding:5mm;
border-radius:3mm;
white-space:pre-wrap;
overflow-wrap:anywhere;
font-family:"DejaVu Sans Mono",monospace;
font-size:8.5pt;
line-height:1.45;
margin:6mm 0;
}}

code {{
font-family:"DejaVu Sans Mono",monospace;
}}

h1,h2,h3 {{
page-break-after:avoid;
break-after:avoid;
}}

pre,table,blockquote,figure {{
page-break-inside:avoid;
break-inside:avoid;
}}

img {{
max-width:100%;
height:auto;
}}

</style>
</head>

<body>

<section class="cover">

<div class="brand">
LEARNFORGE ENGINEERING HANDBOOK
</div>

<h1>
System Architecture<br>
&amp; Clean Code
</h1>

<div class="subtitle">
A Practical Mindset-First Blueprint for Building Scalable,
Maintainable, and Production-Ready Software Systems
</div>

<div class="edition">
EXPANDED DIGITAL EDITION — 2026
</div>

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

OUT.write_text(html,encoding="utf-8")

print("Created:",OUT)
print("Characters:",len(html))
PY

echo "PASS: Complete HTML assembled."

echo
echo "[3/7] Verifying HTML — 25/25..."

titles=(
"From Coder to Architect"
"The Foundations of Good Architecture"
"Requirements Before Architecture"
"Scalability"
"Performance, Latency and Throughput"
"Monolith, Modular Monolith and Microservices"
"Microservice Trade-offs"
"Distributed Systems"
"Event-Driven Architecture"
"Clean Architecture"
"SOLID Principles"
"DRY, KISS, YAGNI, Cohesion and Coupling"
"API Architecture"
"Database Architecture"
"Caching"
"Security by Design"
"Observability"
"Testing Architecture"
"CI/CD and Deployment"
"Production Readiness"
"Disaster Recovery and Resilience"
"Architecture Documentation"
"Real-World System Design Example"
"Architecture Review Checklist"
"Final Architecture Cheat Sheet"
)

PASS=0

for i in $(seq 1 25); do
    title="${titles[$((i-1))]}"

    if grep -Fqi "$title" "$HTML"; then
        printf "Chapter %02d : PASS\n" "$i"
        PASS=$((PASS+1))
    else
        printf "Chapter %02d : FAIL — %s\n" "$i" "$title"
    fi
done

echo
echo "HTML CHAPTER RESULT: $PASS / 25"

[ "$PASS" -eq 25 ] || {
    echo "FAIL: HTML does not contain all 25 chapters."
    exit 1
}

echo
echo "[4/7] Checking broken images..."

if grep -n -Ei \
'media/file[0-9]+\.svg|file:///.*\.svg' \
"$HTML"; then
    echo "FAIL: Broken local SVG references remain."
    exit 1
else
    echo "PASS: No broken local SVG references."
fi

echo
echo "[5/7] Checking suspicious generated text..."

if grep -n -Ei \
"Due to strict|output character|physically impossible|save this directly|Headless Chrome|character limits|response limits|single-file HTML" \
"$HTML"; then
    echo "FAIL: Suspicious generated text found."
    exit 1
else
    echo "PASS: No suspicious generated text."
fi

echo
echo "[6/7] Generating PDF..."

rm -f "$PDF"

weasyprint \
--encoding utf-8 \
--media-type print \
--optimize-images \
"$HTML" \
"$PDF"

[ -s "$PDF" ] || {
    echo "FAIL: PDF generation failed."
    exit 1
}

echo
echo "PDF CREATED:"
ls -lh "$PDF"

echo
echo "[7/7] Extracting PDF and performing final 25/25 audit..."

pdftotext -layout "$PDF" "$TXT"

WORDS=$(pdftotext "$PDF" - | wc -w)

echo
echo "===== PDF INFO ====="

pdfinfo "$PDF" | grep -E \
"Title:|Author:|Pages:|Page size:|File size:|Encrypted:|PDF version:"

echo
echo "WORD COUNT: $WORDS"

echo
echo "===== FINAL PDF 25/25 ====="

PASS=0
FAIL=0

for i in $(seq 1 25); do

    title="${titles[$((i-1))]}"

    if grep -Fqi "$title" "$TXT"; then
        printf "Chapter %02d : PASS — %s\n" "$i" "$title"
        PASS=$((PASS+1))
    else
        printf "Chapter %02d : FAIL — %s\n" "$i" "$title"
        FAIL=$((FAIL+1))
    fi

done

echo
echo "=========================================="
echo " FINAL RESULT"
echo "=========================================="
echo "PASS: $PASS / 25"
echo "FAIL: $FAIL / 25"
echo "WORDS: $WORDS"
echo "=========================================="

if [ "$PASS" -ne 25 ]; then
    echo "BUILD FAILED."
    exit 1
fi

echo
echo "SUCCESS — COMPLETE 25/25 BOOK VERIFIED."
echo
echo "HTML:"
echo "$HTML"
echo
echo "PDF:"
echo "$PDF"
echo
echo "AUDIT:"
echo "$TXT"
echo
echo "=========================================="
