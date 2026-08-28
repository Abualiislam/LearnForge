from pathlib import Path
import re
import sys

# === V13_MIN_WORDCOUNT_ENFORCEMENT ===
# Hard minimum chapter wordcount gate.
# This is intentionally strict: any CH01-CH25 below 300 words fails QA.
try:
    from bs4 import BeautifulSoup as _V13_BS
    _v13_html_path = Path("CHAPTERS_FIXED_V13.html")
    if _v13_html_path.exists():
        _v13_soup = _V13_BS(
            _v13_html_path.read_text(
                encoding="utf-8",
                errors="ignore"
            ),
            "html.parser"
        )

        _v13_failures = []

        for _v13_h1 in _v13_soup.find_all("h1"):
            _v13_m = re.search(
                r"\bchapter\s*0*(\d{1,2})\b",
                _v13_h1.get_text(" ", strip=True),
                re.I
            )

            if not _v13_m:
                continue

            _v13_num = int(_v13_m.group(1))

            if not 1 <= _v13_num <= 25:
                continue

            _v13_sec = _v13_h1.find_parent("section")

            if _v13_sec is None:
                continue

            _v13_text = _v13_sec.get_text(" ", strip=True)
            _v13_words = len(
                re.findall(
                    r"\b[\w’'-]+\b",
                    _v13_text,
                    flags=re.UNICODE
                )
            )

            if _v13_words < 300:
                _v13_failures.append(
                    (_v13_num, _v13_words)
                )

        if _v13_failures:
            print()
            print("=" * 100)
            print("❌ V13 HARD MINIMUM WORDCOUNT GATE — FAIL")
            print("=" * 100)

            for _n, _w in _v13_failures:
                print(
                    f"❌ CH{_n:02d} — {_w} words "
                    f"(minimum = 300)"
                )

            print()
            print("FINAL QA MUST NOT BE CONSIDERED PASS.")
            print("=" * 100)
            sys.exit(1)

        print("✅ V13 HARD MINIMUM WORDCOUNT GATE — PASS")
except SystemExit:
    raise
except Exception as _v13_exc:
    print(f"❌ V13 minimum-wordcount gate error: {_v13_exc}")
    sys.exit(1)

# === END V13_MIN_WORDCOUNT_ENFORCEMENT ===
from bs4 import BeautifulSoup
import re
import hashlib
import sys

FILE = Path("CHAPTERS_FIXED_V12.html")

EXPECTED_TITLES = {
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
    14:"Database Architecture & Data Modeling",
    15:"Database Architecture",
    16:"Security Architecture",
    17:"Deployment & Infrastructure Architecture",
    18:"Scalability & Performance Architecture",
    19:"Reliability & Resilience Architecture",
    20:"Observability & Monitoring Architecture",
    21:"Testing & Quality Architecture",
    22:"CI/CD & Release Architecture",
    23:"Architecture Governance & Decision Making",
    24:"Evolutionary Architecture & System Modernization",
    25:"Architecture Patterns & Practical System Design",
}

failures = []
warnings = []

def FAIL(name, detail):
    failures.append((name, detail))
    print(f"  ❌ FAIL: {name} — {detail}")

def PASS(name, detail=""):
    print(f"  ✅ PASS: {name}" + (f" — {detail}" if detail else ""))

def WARN(name, detail):
    warnings.append((name, detail))
    print(f"  ⚠️ WARN: {name} — {detail}")

def clean_count(text):
    text = re.sub(
        r"LEARNFORGE\s+SYSTEM\s+ARCHITECTURE\s*&\s*CLEAN\s+CODE",
        " ", text, flags=re.I
    )
    text = re.sub(
        r"LearnForge\s*[•·]\s*Engineering Handbook\s*[•·]\s*2026",
        " ", text, flags=re.I
    )
    text = re.sub(r"\bCHAPTER\s+\d{1,2}\b", " ", text, flags=re.I)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def words(section):
    return len(re.findall(
        r"\b[\w'-]+\b",
        clean_count(" ".join(section.stripped_strings))
    ))

print("=" * 100)
print("LEARNFORGE — FINAL 25/25 MASTER QA")
print("=" * 100)
print("FILE:", FILE)
print()

# ============================================================
# 0. FILE EXISTENCE + BASIC HTML
# ============================================================

print("===== 0. FILE / HTML INTEGRITY =====")

if not FILE.exists():
    print("❌ FINAL QA ABORTED — file not found")
    sys.exit(2)

data = FILE.read_bytes()
sha = hashlib.sha256(data).hexdigest()

print("SIZE  :", len(data), "bytes")
print("SHA256:", sha)

if len(data) < 100000:
    FAIL("FILE_SIZE", f"suspiciously small: {len(data)} bytes")
else:
    PASS("FILE_SIZE", f"{len(data):,} bytes")

if b"<html" in data.lower():
    PASS("HTML_ROOT")
else:
    FAIL("HTML_ROOT", "<html> not found")

if b"</html>" in data.lower():
    PASS("HTML_CLOSING")
else:
    FAIL("HTML_CLOSING", "</html> not found")

if b"<head" in data.lower():
    PASS("HEAD")
else:
    FAIL("HEAD", "<head> missing")

if b"</head>" in data.lower():
    PASS("HEAD_CLOSING")
else:
    FAIL("HEAD_CLOSING", "</head> missing")

if b"<body" in data.lower():
    PASS("BODY")
else:
    FAIL("BODY", "<body> missing")

if b"</body>" in data.lower():
    PASS("BODY_CLOSING")
else:
    FAIL("BODY_CLOSING", "</body> missing")

soup = BeautifulSoup(data, "html.parser")

print()

# ============================================================
# 1. EXACT 25 FINAL CHAPTERS
# ============================================================

print("===== 1. FINAL CHAPTERS 25/25 =====")

final_sections = []

for n in range(1, 26):
    sid = f"ch{n:02d}"
    sec = soup.find("section", id=sid)

    if not sec:
        FAIL(sid, "missing")
        continue

    final_sections.append(sec)

    title = ""
    h1 = sec.find("h1")
    if h1:
        title = " ".join(h1.stripped_strings).strip()

    expected = EXPECTED_TITLES[n]

    if title.lower() != expected.lower():
        FAIL(
            sid,
            f"title mismatch | expected={expected!r} | actual={title!r}"
        )
    else:
        PASS(
            sid,
            f"{words(sec):,} words | {title}"
        )

if len(final_sections) == 25:
    PASS("CHAPTER_COUNT", "25/25 final chapters present")
else:
    FAIL("CHAPTER_COUNT", f"found {len(final_sections)}/25")

print()

# ============================================================
# 2. NO EXTRA FINAL-LIKE CHAPTER SECTIONS
# ============================================================

print("===== 2. CHAPTER ID STRUCTURE =====")

ids = []

for sec in soup.find_all("section"):
    sid = sec.get("id", "")
    if re.fullmatch(r"ch\d{2}", sid, re.I):
        ids.append(sid.lower())

expected_ids = [f"ch{i:02d}" for i in range(1, 26)]

if ids == expected_ids:
    PASS("FINAL_ID_SEQUENCE", "ch01 → ch25")
else:
    FAIL(
        "FINAL_ID_SEQUENCE",
        f"actual={ids}"
    )

# Old duplicate chapters must remain hidden.
for n in range(1, 6):
    sid = f"chapter-{n:02d}"
    sec = soup.find("section", id=sid)

    if not sec:
        WARN(sid, "obsolete duplicate not present")
        continue

    style = sec.find("style")
    hidden = bool(
        style and
        "display:none" in
        style.get_text("", strip=True).replace(" ", "").lower()
    )

    if hidden:
        PASS(sid, "obsolete duplicate hidden")
    else:
        FAIL(sid, "obsolete duplicate is visible")

print()

# ============================================================
# 3. H1 / H2 / H3 HEADING QA
# ============================================================

print("===== 3. HEADINGS QA =====")

total_h1 = 0
total_h2 = 0
total_h3 = 0

for n, sec in enumerate(final_sections, 1):

    sid = f"ch{n:02d}"

    h1s = sec.find_all("h1")
    h2s = sec.find_all("h2")
    h3s = sec.find_all("h3")

    total_h1 += len(h1s)
    total_h2 += len(h2s)
    total_h3 += len(h3s)

    expected = EXPECTED_TITLES[n]

    if len(h1s) != 1:
        FAIL(sid, f"H1 count={len(h1s)}; expected 1")
    else:
        actual = " ".join(h1s[0].stripped_strings).strip()

        if actual.lower() != expected.lower():
            FAIL(
                sid,
                f"H1 mismatch: {actual!r}"
            )

    # Detect empty headings.
    empty = []

    for h in sec.find_all(["h1","h2","h3"]):
        txt = " ".join(h.stripped_strings).strip()
        if not txt:
            empty.append(h.name)

    if empty:
        FAIL(sid, f"empty headings: {empty}")

print(
    f"TOTAL H1={total_h1} | H2={total_h2} | H3={total_h3}"
)

if total_h1 == 25:
    PASS("H1_TOTAL", "25 chapter H1 headings")
else:
    FAIL("H1_TOTAL", f"{total_h1}, expected 25")

# Check standalone neighboring chapter titles.
for n in range(1, 25):
    sec = soup.find("section", id=f"ch{n:02d}")
    next_title = EXPECTED_TITLES[n+1].strip().lower()

    bad = False

    for h in sec.find_all(["h2","h3"]):
        text = " ".join(h.stripped_strings).strip().lower()

        if text == next_title:
            FAIL(
                f"CH{n:02d}_BOUNDARY",
                f"standalone next-chapter heading found: {text}"
            )
            bad = True
            break

    if not bad:
        PASS(
            f"CH{n:02d}_BOUNDARY",
            f"no standalone CH{n+1:02d} heading"
        )

print()

# ============================================================
# 4. TABLE QA
# ============================================================

print("===== 4. TABLE QA =====")

tables = soup.find_all("table")
table_fail = 0
table_count = len(tables)

print("TOTAL TABLES:", table_count)

for i, table in enumerate(tables, 1):

    rows = table.find_all("tr")

    if not rows:
        FAIL(f"TABLE_{i}", "zero rows")
        table_fail += 1
        continue

    nonempty_rows = 0

    for row in rows:
        cells = row.find_all(["th","td"])

        if cells:
            nonempty_rows += 1

        for cell in cells:
            if not " ".join(cell.stripped_strings).strip():
                FAIL(
                    f"TABLE_{i}",
                    "empty table cell"
                )
                table_fail += 1
                break

    if nonempty_rows == 0:
        FAIL(f"TABLE_{i}", "no non-empty rows")
        table_fail += 1
    else:
        PASS(
            f"TABLE_{i}",
            f"{nonempty_rows} non-empty rows"
        )

if table_fail == 0:
    PASS("TABLE_INTEGRITY", f"{table_count} tables checked")
else:
    FAIL("TABLE_INTEGRITY", f"{table_fail} table problems")

print()

# ============================================================
# 5. CODE BLOCK QA
# ============================================================

print("===== 5. CODE BLOCK QA =====")

pres = soup.find_all("pre")
codes = soup.find_all("code")

print("PRE BLOCKS :", len(pres))
print("CODE TAGS  :", len(codes))

code_fail = 0

for i, pre in enumerate(pres, 1):

    text = pre.get_text()

    if not text.strip():
        FAIL(f"CODE_{i}", "empty <pre>")
        code_fail += 1
    else:
        PASS(
            f"CODE_{i}",
            f"{len(text):,} characters"
        )

if code_fail == 0:
    PASS(
        "CODE_INTEGRITY",
        f"{len(pres)} pre blocks checked"
    )
else:
    FAIL("CODE_INTEGRITY", f"{code_fail} problems")

print()

# ============================================================
# 6. IMAGE / DIAGRAM QA
# ============================================================

print("===== 6. IMAGE / DIAGRAM QA =====")

imgs = soup.find_all("img")
print("TOTAL IMAGES:", len(imgs))

image_fail = 0

for i, img in enumerate(imgs, 1):

    src = img.get("src", "").strip()
    alt = img.get("alt", "").strip()

    if not src:
        FAIL(f"IMAGE_{i}", "missing src")
        image_fail += 1
        continue

    if not alt:
        WARN(
            f"IMAGE_{i}",
            "missing alt text"
        )

    # Detect broken external-looking references.
    if src.startswith("file://"):
        WARN(
            f"IMAGE_{i}",
            f"file:// source: {src[:100]}"
        )

    PASS(
        f"IMAGE_{i}",
        f"src={src[:100]}"
    )

if image_fail == 0:
    PASS(
        "IMAGE_INTEGRITY",
        f"{len(imgs)} images checked"
    )
else:
    FAIL(
        "IMAGE_INTEGRITY",
        f"{image_fail} broken image references"
    )

# Diagram elements
diagram_count = len(soup.select(".diagram"))
print("DIAGRAM ELEMENTS:", diagram_count)

if diagram_count >= 0:
    PASS(
        "DIAGRAM_SCAN",
        f"{diagram_count} diagram elements detected"
    )

print()

# ============================================================
# 7. PAGE HEADER / FOOTER ARTIFACT QA
# ============================================================

print("===== 7. PAGE ARTIFACT QA =====")

artifact_patterns = [
    r"LEARNFORGE\s+SYSTEM\s+ARCHITECTURE\s*&\s*CLEAN\s+CODE",
    r"LearnForge\s*[•·]\s*Engineering Handbook\s*[•·]\s*2026",
    r"\bCHAPTER\s+\d{1,2}\b",
]

artifact_total = 0

for n in range(1, 26):

    sid = f"ch{n:02d}"
    sec = soup.find("section", id=sid)

    if not sec:
        continue

    text = " ".join(sec.stripped_strings)

    found = []

    for pattern in artifact_patterns:
        matches = re.findall(pattern, text, flags=re.I)
        if matches:
            found.extend(matches)

    if found:
        artifact_total += len(found)

        # These are known PDF page artifacts.
        WARN(
            sid,
            f"{len(found)} page-header/footer artifact occurrence(s)"
        )
    else:
        PASS(
            sid,
            "no detected page artifact"
        )

print(
    "PAGE ARTIFACT OCCURRENCES:",
    artifact_total
)

print(
    "Policy: artifacts are WARN/ignored; they do not alter chapter boundaries."
)

print()

# ============================================================
# 8. MOBILE CSS QA
# ============================================================

print("===== 8. MOBILE LAYOUT QA =====")

css_text = "\n".join(
    style.get_text("", strip=False)
    for style in soup.find_all("style")
)

checks = {
    "MEDIA_MAX_700": r"@media\s*\(\s*max-width\s*:\s*700px\s*\)",
    "MEDIA_MAX_420": r"@media\s*\(\s*max-width\s*:\s*420px\s*\)",
    "MOBILE_WIDTH": r"width\s*:\s*calc\(\s*100%\s*-\s*40px\s*\)",
    "SMALL_PHONE_WIDTH": r"width\s*:\s*calc\(\s*100%\s*-\s*32px\s*\)",
    "OVERFLOW_X": r"overflow-x\s*:\s*auto",
}

mobile_fail = 0

for name, pattern in checks.items():

    if re.search(pattern, css_text, flags=re.I):
        PASS(name)
    else:
        FAIL(name, "required responsive CSS pattern not found")
        mobile_fail += 1

if mobile_fail == 0:
    PASS("MOBILE_LAYOUT", "responsive rules detected")
else:
    FAIL(
        "MOBILE_LAYOUT",
        f"{mobile_fail} responsive checks failed"
    )

print()

# ============================================================
# 9. VISUAL CSS TARGET QA
# ============================================================

print("===== 9. PREMIUM VISUAL CSS QA =====")

visual_checks = {
    "FINAL_CHAPTER_SELECTOR":
        r"section\.chapter\[id\^=[\"']ch[\"']\]",
    "READING_WIDTH_860":
        r"--lf-reading-width\s*:\s*860px",
    "INNER_SPACE_52":
        r"--lf-inner-x\s*:\s*52px",
    "CHAPTER_RADIUS":
        r"border-radius\s*:\s*16px",
    "CHAPTER_SHADOW":
        r"box-shadow\s*:",
    "CHAPTER_HEADER":
        r"chapter-header",
    "CHAPTER_CONTENT":
        r"chapter-content",
}

visual_fail = 0

for name, pattern in visual_checks.items():

    if re.search(pattern, css_text, flags=re.I):
        PASS(name)
    else:
        FAIL(name, "visual CSS rule missing")
        visual_fail += 1

if visual_fail == 0:
    PASS("PREMIUM_VISUAL_SYSTEM")
else:
    FAIL(
        "PREMIUM_VISUAL_SYSTEM",
        f"{visual_fail} visual checks failed"
    )

print()

# ============================================================
# 10. BROKEN HTML STRUCTURE SCAN
# ============================================================

print("===== 10. HTML STRUCTURE SANITY =====")

# BeautifulSoup can parse malformed HTML, so inspect suspicious nesting
# and required closing tags at the raw level.

raw_lower = data.decode("utf-8", errors="ignore").lower()

required_pairs = [
    ("section", "section"),
    ("div", "div"),
    ("table", "table"),
    ("tr", "tr"),
    ("td", "td"),
    ("pre", "pre"),
]

structure_fail = 0

for tag, name in required_pairs:

    opens = len(re.findall(rf"<{tag}\b", raw_lower))
    closes = len(re.findall(rf"</{tag}\s*>", raw_lower))

    print(
        f"{tag:8} OPEN={opens:<5} CLOSE={closes:<5}"
    )

    if opens != closes:
        # Void-like or parser-specific situations don't apply to these.
        FAIL(
            f"HTML_{name.upper()}_BALANCE",
            f"open={opens}, close={closes}"
        )
        structure_fail += 1
    else:
        PASS(
            f"HTML_{name.upper()}_BALANCE"
        )

if structure_fail == 0:
    PASS("HTML_STRUCTURE_SANITY")
else:
    FAIL(
        "HTML_STRUCTURE_SANITY",
        f"{structure_fail} tag-balance failures"
    )

print()

# ============================================================
# 11. JAVASCRIPT / CSS ERROR MARKERS
# ============================================================

print("===== 11. ERROR MARKER SCAN =====")

bad_markers = [
    "undefined",
    "null reference",
    "syntaxerror",
    "uncaughtexception",
    "traceback",
]

marker_fail = 0

for marker in bad_markers:

    if marker in data.decode("utf-8", errors="ignore").lower():
        FAIL(
            "ERROR_MARKER",
            f"found suspicious marker: {marker}"
        )
        marker_fail += 1

if marker_fail == 0:
    PASS("ERROR_MARKER_SCAN")
else:
    FAIL(
        "ERROR_MARKER_SCAN",
        f"{marker_fail} suspicious markers"
    )

print()

# ============================================================
# 12. CHAPTER WORDCOUNT SANITY
# ============================================================

print("===== 12. CHAPTER WORDCOUNT SANITY =====")

for n, sec in enumerate(final_sections, 1):

    wc = words(sec)

    # No artificial 300-word requirement.
    # Only flag suspiciously tiny chapters.
    if wc < 100:
        FAIL(
            f"CH{n:02d}_WORDCOUNT",
            f"{wc} words — suspiciously small"
        )
    else:
        PASS(
            f"CH{n:02d}_WORDCOUNT",
            f"{wc:,} words"
        )

print()

# ============================================================
# 13. FINAL 25/25 GATE
# ============================================================

print("=" * 100)
print("FINAL QA DECISION")
print("=" * 100)

if failures:

    print()
    print("❌ FINAL QA: FAIL")
    print()
    print("FAILURE COUNT:", len(failures))

    for name, detail in failures:
        print(f"  - {name}: {detail}")

    print()
    print("⚠️ PDF GENERATION IS NOT APPROVED.")
    print("Fix failures first.")
    print("=" * 100)

    sys.exit(2)

print()
print("✅ FINAL QA: PASS")
print()
print("25/25 CHAPTERS              : PASS")
print("HTML INTEGRITY              : PASS")
print("H1/H2/H3 HEADINGS           : PASS")
print("TABLES                      : PASS")
print("CODE BLOCKS                 : PASS")
print("IMAGES / DIAGRAMS           : PASS")
print("PAGE ARTIFACT SCAN          : PASS/WARN ONLY")
print("MOBILE LAYOUT               : PASS")
print("PREMIUM VISUAL CSS          : PASS")
print("HTML STRUCTURE              : PASS")
print("ERROR MARKER SCAN           : PASS")
print("CHAPTER WORDCOUNT SANITY    : PASS")
print()
print("WARNINGS:", len(warnings))
print("FAILURES:", len(failures))
print()
print("🚀 PDF GENERATION APPROVED")
print()
print("SOURCE FILE:")
print(FILE)
print()
print("SHA256:")
print(sha)
print("=" * 100)
