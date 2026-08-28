#!/data/data/com.termux/files/usr/bin/bash
set -e

SRC="$HOME/LearnForge/LearnForge_FINAL_25_CHAPTERS_2026.html"
HTML="$HOME/LearnForge/LearnForge_PREMIUM_V3_25_CHAPTERS_2026.html"
PDF="$HOME/LearnForge/LearnForge_PREMIUM_V3_25_CHAPTERS_2026.pdf"
AUDIT="$HOME/LearnForge/LearnForge_PREMIUM_V3_25_CHAPTERS_2026_AUDIT.txt"
DOWNLOAD="$HOME/storage/downloads/LearnForge_PREMIUM_V3_25_CHAPTERS_2026.pdf"

[ -f "$SRC" ] || {
  echo "ERROR: Source PDF HTML not found:"
  echo "$SRC"
  exit 1
}

echo "=========================================="
echo " LEARNFORGE PREMIUM V3"
echo " COLORFUL PROFESSIONAL EDITION"
echo "=========================================="

python - "$SRC" "$HTML" <<'PY'
from pathlib import Path
import sys,re

src=Path(sys.argv[1])
out=Path(sys.argv[2])

s=src.read_text(encoding="utf-8",errors="ignore")

CSS=r'''
<style>

/* ===== LEARNFORGE PREMIUM V3 ===== */

:root{
  --navy:#071426;
  --blue:#087fce;
  --cyan:#00b8d9;
  --purple:#7048e8;
  --green:#16a085;
  --gold:#f59f00;
  --red:#e03131;
  --ink:#172033;
  --muted:#64748b;
  --light:#f4f8fc;
  --line:#dbe5ef;
}

/* PAGE */

@page{
  size:A4;
  margin:20mm 17mm 22mm 17mm;

  @top-left{
    content:"LEARNFORGE";
    color:#087fce;
    font-size:8pt;
    font-weight:bold;
    letter-spacing:2px;
  }

  @top-right{
    content:"SYSTEM ARCHITECTURE & CLEAN CODE";
    color:#64748b;
    font-size:7pt;
  }

  @bottom-left{
    content:"LearnForge • Engineering Handbook • 2026";
    color:#64748b;
    font-size:7.5pt;
  }

  @bottom-right{
    content:counter(page);
    color:#087fce;
    font-size:8pt;
    font-weight:bold;
  }
}

html{
  font-family:Arial,Helvetica,sans-serif;
  color:var(--ink);
  background:white;
}

body{
  margin:0;
  font-size:10.5pt;
  line-height:1.62;
  color:var(--ink);
}

/* COVER */

.cover,
[class*="cover"]{
  position:relative;
}

.cover{
  min-height:250mm;
  padding:28mm 18mm;
  color:white;
  background:
    radial-gradient(circle at 85% 15%,rgba(0,184,217,.35),transparent 25%),
    radial-gradient(circle at 15% 80%,rgba(112,72,232,.35),transparent 28%),
    linear-gradient(135deg,#06111f,#0b2744 55%,#101936);
  border-radius:8mm;
  page-break-after:always;
}

.cover:before{
  content:"";
  position:absolute;
  width:55mm;
  height:55mm;
  right:15mm;
  top:35mm;
  border:1px solid rgba(0,229,255,.35);
  border-radius:50%;
}

.cover:after{
  content:"";
  position:absolute;
  width:35mm;
  height:35mm;
  right:25mm;
  top:45mm;
  border:1px solid rgba(255,255,255,.2);
  border-radius:50%;
}

.cover h1{
  font-size:34pt;
  line-height:1.05;
  margin:35mm 0 8mm;
  color:white;
}

.cover .subtitle{
  font-size:14pt;
  line-height:1.55;
  max-width:145mm;
  color:#d9f5ff;
}

.cover .brand{
  font-size:11pt;
  font-weight:bold;
  letter-spacing:4px;
  color:#62e7ff;
}

.cover .edition{
  position:absolute;
  bottom:22mm;
  left:18mm;
  font-size:9pt;
  letter-spacing:2px;
  color:#a9d9ea;
}

/* TABLE OF CONTENTS */

.toc{
  page-break-after:always;
}

.toc h1{
  font-size:27pt;
  color:var(--navy);
  border-left:5px solid var(--cyan);
  padding-left:6mm;
  margin-bottom:12mm;
}

.toc ol{
  list-style:none;
  padding:0;
}

.toc li{
  padding:3.5mm 4mm;
  margin-bottom:1.5mm;
  border-radius:2mm;
  background:#f4f8fc;
  border-left:3px solid #087fce;
}

.toc li:nth-child(3n){
  border-left-color:#7048e8;
}

.toc li:nth-child(4n){
  border-left-color:#16a085;
}

.num{
  display:inline-block;
  width:14mm;
  font-weight:bold;
  color:#087fce;
}

/* CHAPTER */

.chapter{
  page-break-before:always;
  break-before:page;
}

.chapter:first-of-type{
  page-break-before:auto;
  break-before:auto;
}

.chapter-kicker{
  display:inline-block;
  padding:2mm 4mm;
  border-radius:10mm;
  background:linear-gradient(90deg,#087fce,#7048e8);
  color:white;
  font-size:8pt;
  font-weight:bold;
  letter-spacing:2px;
  margin-bottom:5mm;
}

.chapter h1{
  font-size:27pt;
  line-height:1.12;
  color:#071426;
  margin:0 0 5mm;
  padding-bottom:5mm;
  border-bottom:3px solid #00b8d9;
}

.chapter h2{
  font-size:18pt;
  color:#087fce;
  margin-top:10mm;
  padding-left:4mm;
  border-left:4px solid #00b8d9;
}

.chapter h3{
  font-size:13.5pt;
  color:#7048e8;
  margin-top:7mm;
}

p{
  margin:0 0 5mm;
}

strong{
  color:#075985;
}

/* LISTS */

ul,ol{
  margin:4mm 0 6mm;
  padding-left:8mm;
}

li{
  margin-bottom:2mm;
}

/* CODE */

pre{
  background:
    linear-gradient(135deg,#08111f,#111d31);
  color:#d9f7ff;
  padding:6mm;
  border-radius:3mm;
  border-left:4px solid #00b8d9;
  box-shadow:0 2mm 5mm rgba(7,20,38,.15);
  white-space:pre-wrap;
  overflow-wrap:anywhere;
  font-family:"DejaVu Sans Mono",monospace;
  font-size:8.5pt;
  line-height:1.48;
  margin:6mm 0;
}

code{
  font-family:"DejaVu Sans Mono",monospace;
}

/* TABLES */

table{
  width:100%;
  border-collapse:collapse;
  margin:7mm 0;
  font-size:9pt;
  box-shadow:0 1mm 4mm rgba(0,0,0,.06);
}

th{
  background:linear-gradient(90deg,#087fce,#7048e8);
  color:white;
  padding:3mm;
  text-align:left;
}

td{
  padding:3mm;
  border:1px solid #dbe5ef;
}

tr:nth-child(even) td{
  background:#f5f9fc;
}

/* BLOCKQUOTES */

blockquote{
  margin:6mm 0;
  padding:5mm 6mm;
  border-left:5px solid #7048e8;
  background:#f5f1ff;
  color:#39266b;
  border-radius:2mm;
}

/* LINKS */

a{
  color:#087fce;
}

/* IMAGES */

img{
  max-width:100%;
  height:auto;
  border-radius:3mm;
}

/* FIGURES */

figure{
  margin:7mm 0;
  text-align:center;
}

figcaption{
  color:#64748b;
  font-size:8.5pt;
  margin-top:2mm;
}

/* KEEP ELEMENTS TOGETHER */

h1,h2,h3,h4{
  page-break-after:avoid;
  break-after:avoid;
}

pre,table,blockquote,figure{
  page-break-inside:avoid;
  break-inside:avoid;
}

/* PRINT */

@media print{
  .chapter{
    break-before:page;
  }
}

</style>
'''

# Remove old style blocks and inject V3
s=re.sub(r'<style\b[^>]*>.*?</style>','',s,flags=re.I|re.S)

if re.search(r'</head>',s,re.I):
    s=re.sub(r'</head>',CSS+'</head>',s,count=1,flags=re.I)
else:
    s=CSS+s

out.write_text(s,encoding="utf-8")
print("Premium V3 HTML created.")
print("Characters:",len(s))
PY

echo
echo "[1/7] PREMIUM V3 HTML CREATED"

echo
echo "[2/7] VERIFYING 25 CHAPTERS..."

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

[ "$PASS" -eq 25 ] || {
  echo "ERROR: HTML is not 25/25."
  exit 1
}

echo "PASS: HTML 25/25"

echo
echo "[3/7] CHECKING BROKEN IMAGES..."

if grep -Eqi 'file:///[^"]+|media/file[0-9]+\.svg' "$HTML"; then
  echo "WARNING: image reference detected."
else
  echo "PASS: No broken local SVG references."
fi

echo
echo "[4/7] CHECKING SUSPICIOUS TEXT..."

if grep -n -Ei \
"Due to strict|output character|physically impossible|save this directly|Headless Chrome|character limits|response limits|single-file HTML" \
"$HTML"; then
  echo "FAIL: Suspicious generated text found."
  exit 1
else
  echo "PASS: Clean."
fi

echo
echo "[5/7] GENERATING PREMIUM V3 PDF..."

rm -f "$PDF"

weasyprint \
  --encoding utf-8 \
  --media-type print \
  --optimize-images \
  "$HTML" \
  "$PDF"

[ -s "$PDF" ] || {
  echo "ERROR: PDF generation failed."
  exit 1
}

echo
echo "PDF CREATED:"
ls -lh "$PDF"

echo
echo "[6/7] PDF AUDIT..."

pdftotext -layout "$PDF" "$AUDIT"

P=0
F=0

for i in $(seq 1 25); do
  title="${titles[$((i-1))]}"
  if grep -Fqi "$title" "$AUDIT"; then
    printf "PDF Chapter %02d : PASS\n" "$i"
    P=$((P+1))
  else
    printf "PDF Chapter %02d : FAIL — %s\n" "$i" "$title"
    F=$((F+1))
  fi
done

WORDS=$(pdftotext "$PDF" - | wc -w)
PAGES=$(pdfinfo "$PDF" | awk '/^Pages:/ {print $2}')

echo
echo "=========================================="
echo " PREMIUM V3 FINAL RESULT"
echo "=========================================="
echo "Chapters : $P / 25"
echo "Failed   : $F / 25"
echo "Pages    : $PAGES"
echo "Words    : $WORDS"
echo "=========================================="

[ "$P" -eq 25 ] || {
  echo "BUILD FAILED: PDF is not 25/25."
  exit 1
}

echo
echo "[7/7] COPYING TO ANDROID DOWNLOADS..."

cp -f "$PDF" "$DOWNLOAD"

ls -lh "$DOWNLOAD"

echo
echo "=========================================="
echo " SUCCESS — PREMIUM V3 COMPLETE"
echo " 25/25 CHAPTERS VERIFIED"
echo " PDF COPIED TO DOWNLOADS"
echo "=========================================="
echo
echo "$DOWNLOAD"
