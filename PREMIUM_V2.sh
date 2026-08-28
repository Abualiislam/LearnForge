#!/data/data/com.termux/files/usr/bin/bash
set -e

SRC="$HOME/LearnForge/LearnForge_FINAL_25_CHAPTERS_2026.html"
OUT="$HOME/LearnForge"
HTML="$OUT/LearnForge_PREMIUM_V2_25_CHAPTERS_2026.html"
PDF="$OUT/LearnForge_PREMIUM_V2_25_CHAPTERS_2026.pdf"
TXT="$OUT/LearnForge_PREMIUM_V2_AUDIT.txt"

echo "=============================================="
echo " LEARNFORGE — PREMIUM V2 DESIGN BUILD"
echo "=============================================="

[ -f "$SRC" ] || {
  echo "ERROR: Source PDF/HTML HTML not found:"
  echo "$SRC"
  exit 1
}

echo
echo "[1/7] Applying Premium V2 design..."

python - "$SRC" "$HTML" <<'PY'
from pathlib import Path
import re, sys

src = Path(sys.argv[1])
out = Path(sys.argv[2])

s = src.read_text(encoding="utf-8", errors="ignore")

# ------------------------------------------------
# Remove old injected style blocks
# ------------------------------------------------
s = re.sub(
    r'<style\b[^>]*>.*?</style>',
    '',
    s,
    flags=re.I | re.S
)

# ------------------------------------------------
# Remove broken local SVG references
# ------------------------------------------------
s = re.sub(
    r'<img\b[^>]*src=["\'](?:file://)?[^"\']*/media/file\d+\.svg["\'][^>]*>',
    '',
    s,
    flags=re.I
)

# ------------------------------------------------
# Remove duplicated explicit footer text
# ------------------------------------------------
s = re.sub(
    r'<p[^>]*>\s*System Architecture\s*&amp;\s*Clean Code\s*\(2026\)\s+\d+\s*</p>',
    '',
    s,
    flags=re.I
)

# ------------------------------------------------
# Premium V2 CSS
# ------------------------------------------------
css = r'''
<style>

:root {
  --navy: #07111f;
  --navy2: #0b1f35;
  --blue: #1769aa;
  --cyan: #06b6d4;
  --sky: #38bdf8;
  --green: #10b981;
  --purple: #7c3aed;
  --orange: #f59e0b;
  --red: #ef4444;
  --text: #172033;
  --muted: #64748b;
  --light: #f1f5f9;
  --border: #dbe4ee;
  --white: #ffffff;
}

@page {
  size: A4;
  margin: 18mm 16mm 20mm 16mm;

  @bottom-left {
    content: "LEARNFORGE  •  SYSTEM ARCHITECTURE & CLEAN CODE";
    color: #64748b;
    font-size: 7.5pt;
    letter-spacing: .4px;
  }

  @bottom-right {
    content: counter(page);
    color: #1769aa;
    font-size: 8pt;
    font-weight: bold;
  }
}

/* ------------------------------
   GLOBAL
------------------------------ */

* {
  box-sizing: border-box;
}

html {
  font-family:
    Inter,
    "Segoe UI",
    Arial,
    Helvetica,
    sans-serif;
  color: var(--text);
  background: #ffffff;
}

body {
  margin: 0;
  background: #ffffff;
  color: var(--text);
  font-size: 10.5pt;
  line-height: 1.65;
}

/* ------------------------------
   COVER
------------------------------ */

.cover {
  min-height: 250mm;
  padding: 28mm 20mm;
  color: white;
  position: relative;

  background:
    radial-gradient(
      circle at 85% 15%,
      rgba(56,189,248,.25),
      transparent 30%
    ),
    radial-gradient(
      circle at 15% 85%,
      rgba(124,58,237,.22),
      transparent 35%
    ),
    linear-gradient(
      145deg,
      #050b14,
      #071b31 45%,
      #0b2d4d
    );

  page-break-after: always;
  overflow: hidden;
}

.cover:before {
  content: "";
  position: absolute;
  width: 150mm;
  height: 150mm;
  right: -65mm;
  top: -65mm;
  border: 1px solid rgba(56,189,248,.25);
  border-radius: 50%;
}

.cover:after {
  content: "";
  position: absolute;
  width: 110mm;
  height: 110mm;
  left: -55mm;
  bottom: -55mm;
  border: 1px solid rgba(124,58,237,.25);
  border-radius: 50%;
}

.cover .brand {
  position: relative;
  z-index: 2;
  font-size: 10pt;
  font-weight: 700;
  letter-spacing: 3.5px;
  color: #67e8f9;
  text-transform: uppercase;
  margin-bottom: 48mm;
}

.cover h1 {
  position: relative;
  z-index: 2;
  font-size: 34pt;
  line-height: 1.02;
  letter-spacing: -1px;
  margin: 0 0 9mm;
  color: white;
}

.cover .subtitle {
  position: relative;
  z-index: 2;
  max-width: 145mm;
  font-size: 13pt;
  line-height: 1.55;
  color: #dbeafe;
}

.cover .edition {
  position: absolute;
  z-index: 2;
  bottom: 22mm;
  left: 20mm;
  font-size: 8.5pt;
  letter-spacing: 2px;
  color: #bae6fd;
  font-weight: 600;
}

/* ------------------------------
   TOC
------------------------------ */

.toc {
  page-break-after: always;
  padding-top: 5mm;
}

.toc h1 {
  font-size: 25pt;
  color: var(--navy);
  margin-bottom: 10mm;
}

.toc h1:after {
  content: "";
  display: block;
  width: 28mm;
  height: 3px;
  margin-top: 4mm;
  background: linear-gradient(
    90deg,
    var(--cyan),
    var(--purple)
  );
}

.toc ol {
  list-style: none;
  padding: 0;
  margin: 0;
}

.toc li {
  display: block;
  padding: 3.4mm 2mm;
  margin-bottom: 1mm;
  border-bottom: 1px solid #e5eaf0;
  color: #26364a;
}

.toc li:nth-child(5n+1) {
  border-left: 3px solid var(--cyan);
}

.toc li:nth-child(5n+2) {
  border-left: 3px solid var(--blue);
}

.toc li:nth-child(5n+3) {
  border-left: 3px solid var(--purple);
}

.toc li:nth-child(5n+4) {
  border-left: 3px solid var(--green);
}

.toc li:nth-child(5n+5) {
  border-left: 3px solid var(--orange);
}

.num {
  display: inline-block;
  width: 14mm;
  font-weight: 800;
  color: var(--blue);
}

/* ------------------------------
   CHAPTERS
------------------------------ */

.chapter {
  page-break-before: always;
  break-before: page;
  position: relative;
  padding-top: 4mm;
}

.chapter:first-of-type {
  page-break-before: auto;
  break-before: auto;
}

.chapter-kicker {
  display: inline-block;
  padding: 2mm 4mm;
  margin-bottom: 5mm;

  color: white;
  background:
    linear-gradient(
      90deg,
      var(--blue),
      var(--cyan)
    );

  border-radius: 999px;
  font-size: 8pt;
  font-weight: 800;
  letter-spacing: 2px;
}

.chapter h1 {
  font-size: 26pt;
  line-height: 1.12;
  letter-spacing: -.5px;
  color: var(--navy);
  margin: 0 0 5mm;
}

.chapter-rule {
  height: 3px;
  width: 35mm;
  margin-bottom: 9mm;

  background:
    linear-gradient(
      90deg,
      var(--cyan),
      var(--purple)
    );

  border-radius: 999px;
}

.chapter p {
  margin: 0 0 5mm;
  color: #27364a;
  text-align: left;
}

.chapter h2 {
  color: var(--blue);
  font-size: 17pt;
  margin-top: 9mm;
  margin-bottom: 4mm;
}

.chapter h3 {
  color: var(--navy2);
  font-size: 13pt;
  margin-top: 7mm;
  margin-bottom: 3mm;
}

/* ------------------------------
   EMPHASIS
------------------------------ */

strong {
  color: #075985;
  font-weight: 750;
}

/* ------------------------------
   CODE BLOCKS
------------------------------ */

pre {
  background:
    linear-gradient(
      135deg,
      #07111f,
      #0d2035
    );

  color: #e2e8f0;

  padding: 6mm;
  margin: 7mm 0;

  border-radius: 4mm;
  border-left: 4px solid var(--cyan);

  white-space: pre-wrap;
  overflow-wrap: anywhere;

  font-family:
    "DejaVu Sans Mono",
    "Courier New",
    monospace;

  font-size: 8.3pt;
  line-height: 1.55;

  box-shadow:
    0 3px 12px rgba(7,17,31,.12);
}

code {
  font-family:
    "DejaVu Sans Mono",
    monospace;
}

/* ------------------------------
   TABLES
------------------------------ */

table {
  width: 100%;
  border-collapse: collapse;
  margin: 7mm 0;
  font-size: 9pt;
  border: 1px solid var(--border);
}

th {
  background:
    linear-gradient(
      90deg,
      var(--navy2),
      var(--blue)
    );
  color: white;
  padding: 3mm;
  text-align: left;
}

td {
  padding: 2.7mm 3mm;
  border-bottom: 1px solid var(--border);
  vertical-align: top;
}

tr:nth-child(even) td {
  background: #f8fafc;
}

/* ------------------------------
   LISTS
------------------------------ */

ul, ol {
  margin-top: 3mm;
  margin-bottom: 5mm;
}

li {
  margin-bottom: 2mm;
}

/* ------------------------------
   BLOCKQUOTES / CALLOUTS
------------------------------ */

blockquote {
  margin: 7mm 0;
  padding: 5mm 6mm;

  border-left: 4px solid var(--cyan);
  border-radius: 2mm;

  background: #ecfeff;
  color: #164e63;

  font-weight: 500;
}

/* ------------------------------
   LINKS
------------------------------ */

a {
  color: var(--blue);
  text-decoration: none;
}

/* ------------------------------
   PRINT SAFETY
------------------------------ */

h1, h2, h3, h4 {
  page-break-after: avoid;
  break-after: avoid;
}

pre, table, blockquote, figure {
  page-break-inside: avoid;
  break-inside: avoid;
}

img {
  max-width: 100%;
  height: auto;
}

@media print {
  .chapter {
    break-before: page;
  }
}

</style>
'''

# Insert CSS
if re.search(r'</head>', s, re.I):
    s = re.sub(
        r'</head>',
        css + '</head>',
        s,
        count=1,
        flags=re.I
    )
else:
    s = "<style>" + css + "</style>" + s

# ------------------------------------------------
# Add metadata
# ------------------------------------------------
s = re.sub(
    r'<title>.*?</title>',
    '<title>LearnForge — System Architecture &amp; Clean Code — Premium Edition 2026</title>',
    s,
    count=1,
    flags=re.I | re.S
)

out.write_text(s, encoding="utf-8")

print("Created:", out)
print("Characters:", len(s))
PY

echo "PASS: Premium V2 design applied."

echo
echo "[2/7] Verifying all 25 chapters..."

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
FAIL=0

for i in $(seq 1 25); do
    title="${titles[$((i-1))]}"

    if grep -Fqi "$title" "$HTML"; then
        printf "Chapter %02d : PASS\n" "$i"
        PASS=$((PASS+1))
    else
        printf "Chapter %02d : FAIL — %s\n" "$i" "$title"
        FAIL=$((FAIL+1))
    fi
done

echo
echo "HTML RESULT: $PASS / 25"

[ "$PASS" -eq 25 ] || {
    echo "ERROR: Chapter verification failed."
    exit 1
}

echo
echo "[3/7] Checking broken images..."

if grep -Eqi \
'file:///[^"]*|media/file[0-9]+\.svg' \
"$HTML"; then
    echo "FAIL: Broken local media references found."
    grep -Ein \
    'file:///[^"]*|media/file[0-9]+\.svg' \
    "$HTML" | head -20
    exit 1
else
    echo "PASS: No broken local SVG references."
fi

echo
echo "[4/7] Checking suspicious generated text..."

if grep -n -Ei \
"Due to strict|output character|physically impossible|save this directly|Headless Chrome|character limits|response limits|single-file HTML" \
"$HTML"; then
    echo "FAIL: Suspicious generated text detected."
    exit 1
else
    echo "PASS: No suspicious generated text."
fi

echo
echo "[5/7] Generating Premium V2 PDF..."

rm -f "$PDF"

weasyprint \
  --encoding utf-8 \
  --media-type print \
  --optimize-images \
  "$HTML" \
  "$PDF"

[ -s "$PDF" ] || {
    echo "FAIL: PDF was not created."
    exit 1
}

echo
echo "PDF CREATED:"
ls -lh "$PDF"

echo
echo "[6/7] PDF AUDIT..."

pdftotext -layout "$PDF" "$TXT"

echo
echo "===== PDF INFO ====="

pdfinfo "$PDF" | grep -E \
"Title:|Author:|Pages:|Page size:|File size:|Encrypted:|PDF version:"

WORDS=$(pdftotext "$PDF" - | wc -w)

echo
echo "===== WORD COUNT ====="
echo "Words: $WORDS"

echo
echo "===== FINAL 25/25 PDF TEST ====="

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
echo "=============================================="
echo " LEARNFORGE PREMIUM V2 FINAL RESULT"
echo "=============================================="
echo "PASS: $PASS / 25"
echo "FAIL: $FAIL / 25"
echo "WORDS: $WORDS"

if [ "$PASS" -ne 25 ]; then
    echo
    echo "BUILD FAILED: PDF is not 25/25."
    exit 1
fi

echo
echo "SUCCESS: PREMIUM V2 PDF — 25/25 VERIFIED."
echo
echo "HTML:"
echo "$HTML"
echo
echo "PDF:"
echo "$PDF"
echo
echo "AUDIT:"
echo "$TXT"
echo "=============================================="

echo
echo "[7/7] Copying PDF to Android Downloads..."

cp "$PDF" "$HOME/storage/downloads/"

echo "DONE:"
ls -lh "$HOME/storage/downloads/LearnForge_PREMIUM_V2_25_CHAPTERS_2026.pdf"

echo
echo "Opening PDF..."
termux-open "$HOME/storage/downloads/LearnForge_PREMIUM_V2_25_CHAPTERS_2026.pdf" 2>/dev/null || true
