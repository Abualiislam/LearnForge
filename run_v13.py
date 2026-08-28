from pathlib import Path
import re
import shutil
import sys

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ BeautifulSoup not installed.")
    print("Run: pip install beautifulsoup4")
    sys.exit(1)

SRC = Path("CHAPTERS_FIXED_V12.html")
OUT = Path("CHAPTERS_FIXED_V13.html")
QA  = Path("final_qa.py")
QA_BACKUP = Path("final_qa.py.v12_backup")

TARGETS = {
    "02": "The Foundations of Good Architecture",
    "03": "Requirements Before Architecture",
    "04": "Scalability",
}

MIN_WORDS = 300

if not SRC.exists():
    print(f"❌ Missing source: {SRC}")
    sys.exit(1)

print("=" * 100)
print("LEARNFORGE — V13 CH02/03/04 REPAIR + VERIFY")
print("=" * 100)
print(f"SOURCE: {SRC}")
print(f"OUTPUT: {OUT}")
print(f"MINIMUM WORDS: {MIN_WORDS}")
print()

html = SRC.read_text(encoding="utf-8", errors="ignore")
soup = BeautifulSoup(html, "html.parser")


def clean_text(node):
    if node is None:
        return ""
    clone = BeautifulSoup(str(node), "html.parser")
    for x in clone(["script", "style"]):
        x.decompose()
    return " ".join(clone.get_text(" ", strip=True).split())


def word_count(node):
    text = clean_text(node)
    return len(re.findall(r"\b[\w’'-]+\b", text, flags=re.UNICODE))


def normalize(s):
    s = s.lower()
    s = re.sub(r"chapter\s*\d+\s*", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def chapter_number_from_h1(h1):
    if not h1:
        return None
    m = re.search(r"\bchapter\s*0*(\d{1,2})\b", h1.get_text(" ", strip=True), re.I)
    return m.group(1).zfill(2) if m else None


def is_target_h1(tag, num):
    if tag.name != "h1":
        return False
    n = chapter_number_from_h1(tag)
    return n == num


def section_for_h1(h1):
    # Prefer nearest ancestor section.
    sec = h1.find_parent("section")
    if sec:
        return sec

    # Fallback: collect until next H1.
    container = soup.new_tag("section")
    for node in list(h1.next_siblings):
        if getattr(node, "name", None) == "h1":
            break
        container.append(node)
    return container


def candidate_info(h1, num, title):
    sec = section_for_h1(h1)
    text = clean_text(sec)
    wc = len(re.findall(r"\b[\w’'-]+\b", text, flags=re.UNICODE))

    htxt = " ".join(h1.get_text(" ", strip=True).split())
    nt = normalize(htxt)
    expected = normalize(title)

    score = 0

    # Exact chapter number is mandatory.
    if chapter_number_from_h1(h1) == num:
        score += 1000

    # Exact/strong title match.
    if nt == expected:
        score += 500
    elif expected in nt or nt in expected:
        score += 300

    # Prefer real content over tiny/damaged fragments.
    if wc >= MIN_WORDS:
        score += 500
    elif wc >= 250:
        score += 100
    else:
        score -= 500

    # Penalize obvious duplicate/hidden/damaged fragments.
    parent_classes = " ".join(
        str(x.get("class", "")) for x in sec.find_all()
    ).lower()

    attrs = " ".join(
        str(v) for v in sec.attrs.values()
    ).lower()

    blob = (parent_classes + " " + attrs + " " + str(sec)[:2000]).lower()

    if "duplicate" in blob:
        score -= 400
    if "obsolete" in blob:
        score -= 400
    if "hidden" in blob:
        score -= 250
    if "display:none" in blob.replace(" ", ""):
        score -= 250

    return {
        "h1": h1,
        "section": sec,
        "words": wc,
        "score": score,
        "heading": htxt,
    }


# ---------------------------------------------------------------------
# Discover all candidate chapter sections.
# ---------------------------------------------------------------------

all_candidates = {}

for num, title in TARGETS.items():
    candidates = []

    for h1 in soup.find_all("h1"):
        if is_target_h1(h1, num):
            candidates.append(candidate_info(h1, num, title))

    candidates.sort(key=lambda x: (x["score"], x["words"]), reverse=True)
    all_candidates[num] = candidates

    print(f"===== CH{num} CANDIDATES =====")

    if not candidates:
        print("❌ No candidate H1 found.")
        continue

    for i, c in enumerate(candidates, 1):
        print(
            f"{i:02d}. words={c['words']:5d} "
            f"score={c['score']:5d} "
            f"heading={c['heading']}"
        )

    print()


# ---------------------------------------------------------------------
# Identify the current active chapter sections.
# ---------------------------------------------------------------------

active_sections = {}

for num, title in TARGETS.items():
    matches = []

    for h1 in soup.find_all("h1"):
        if is_target_h1(h1, num):
            sec = section_for_h1(h1)

            # Prefer visible/non-obsolete section.
            text = clean_text(sec)
            wc = len(re.findall(r"\b[\w’'-]+\b", text))

            attrs = " ".join(str(v) for v in sec.attrs.values()).lower()
            cls = " ".join(sec.get("class", [])).lower()

            hidden = (
                "hidden" in attrs
                or "hidden" in cls
                or "obsolete" in attrs
                or "obsolete" in cls
                or "display:none" in str(sec).replace(" ", "").lower()
            )

            matches.append((hidden, wc, sec, h1))

    if matches:
        # Current active = visible candidate with highest reasonable
        # structural priority, not simply longest duplicate.
        visible = [x for x in matches if not x[0]]

        if visible:
            visible.sort(key=lambda x: x[1], reverse=True)
            active_sections[num] = visible[0]
        else:
            matches.sort(key=lambda x: x[1], reverse=True)
            active_sections[num] = matches[0]


# ---------------------------------------------------------------------
# Repair only CH02/03/04.
# Never fabricate text.
# ---------------------------------------------------------------------

repair_log = []

for num, title in TARGETS.items():

    candidates = all_candidates.get(num, [])
    current = active_sections.get(num)

    if not current:
        print(f"❌ CH{num}: active section not found.")
        repair_log.append((num, "NO_ACTIVE_SECTION"))
        continue

    current_hidden, current_words, current_sec, current_h1 = current

    print(f"===== CH{num} REPAIR =====")
    print(f"Current words: {current_words}")

    if current_words >= MIN_WORDS:
        print(f"✅ CH{num} already >= {MIN_WORDS}; untouched.")
        repair_log.append((num, "UNCHANGED", current_words))
        print()
        continue

    # Find best legitimate alternative.
    valid = [
        c for c in candidates
        if c["words"] >= MIN_WORDS
        and c["section"] is not current_sec
    ]

    if not valid:
        print(
            f"❌ CH{num}: no legitimate >= {MIN_WORDS}-word "
            f"candidate found. NO FABRICATION."
        )
        repair_log.append((num, "NO_VALID_CANDIDATE", current_words))
        print()
        continue

    best = valid[0]

    print(
        f"Candidate selected: {best['words']} words | "
        f"score={best['score']} | {best['heading']}"
    )

    # Preserve the current section's ID/class/style where possible,
    # while replacing its actual chapter content with the stronger
    # legitimate candidate section.
    replacement = BeautifulSoup(
        str(best["section"]),
        "html.parser"
    ).find("section")

    if replacement is None:
        print(f"❌ CH{num}: candidate section extraction failed.")
        repair_log.append((num, "CANDIDATE_PARSE_FAILED", current_words))
        print()
        continue

    # Preserve useful attributes from current section.
    for key, value in current_sec.attrs.items():
        if key not in replacement.attrs:
            replacement.attrs[key] = value

    current_sec.replace_with(replacement)

    # Remove the selected duplicate candidate if it still exists
    # elsewhere in the document.
    for sec in soup.find_all("section"):
        if sec is replacement:
            continue

        h1 = sec.find("h1")
        if not h1:
            continue

        if chapter_number_from_h1(h1) != num:
            continue

        wc = word_count(sec)

        # Remove only obvious duplicate/obsolete alternatives.
        attrs_blob = (
            str(sec.attrs).lower()
            + " "
            + " ".join(sec.get("class", [])).lower()
        )

        if "duplicate" in attrs_blob or "obsolete" in attrs_blob:
            sec.decompose()

    final_words = word_count(replacement)

    if final_words >= MIN_WORDS:
        print(f"✅ CH{num} repaired: {current_words} → {final_words}")
        repair_log.append((num, "REPAIRED", current_words, final_words))
    else:
        print(
            f"❌ CH{num} repair verification failed: "
            f"{final_words} words"
        )
        repair_log.append((num, "REPAIR_VERIFY_FAILED", final_words))

    print()


# ---------------------------------------------------------------------
# Write V13 only if the HTML is structurally serializable.
# ---------------------------------------------------------------------

out_html = str(soup)

if len(out_html.encode("utf-8")) < 10000:
    print("❌ V13 output unexpectedly tiny. Aborting.")
    sys.exit(1)

OUT.write_text(out_html, encoding="utf-8")

print("=" * 100)
print("V13 OUTPUT CREATED")
print("=" * 100)
print(f"FILE: {OUT}")
print(f"SIZE: {OUT.stat().st_size:,} bytes")
print()

# ---------------------------------------------------------------------
# Patch final_qa.py with HARD >=300 chapter wordcount enforcement.
# Backup original once.
# ---------------------------------------------------------------------

qa = QA.read_text(encoding="utf-8")

if not QA_BACKUP.exists():
    shutil.copy2(QA, QA_BACKUP)
    print(f"✅ Backup created: {QA_BACKUP}")

marker = "# === V13_MIN_WORDCOUNT_ENFORCEMENT ==="

if marker not in qa:
    injection = r'''
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
'''

    # Insert after imports so Path/re/sys are available.
    import_anchor = "from pathlib import Path"

    if import_anchor in qa:
        pos = qa.find(import_anchor)
        line_end = qa.find("\n", pos)

        qa = (
            qa[:line_end + 1]
            + "import re\nimport sys\n"
            + injection
            + qa[line_end + 1:]
        )
    else:
        qa = "import re\nimport sys\n" + injection + qa

    QA.write_text(qa, encoding="utf-8")
    print("✅ final_qa.py patched with V13 >=300 hard gate.")
else:
    print("ℹ️ V13 hard gate already present.")


# ---------------------------------------------------------------------
# Run final QA against V13.
# ---------------------------------------------------------------------

print()
print("=" * 100)
print("RUNNING FINAL QA ON V13")
print("=" * 100)

import subprocess

result = subprocess.run(
    [sys.executable, str(QA)],
    cwd=str(Path.cwd())
)

print()
print("=" * 100)

if result.returncode == 0:
    print("🚀 V13 FINAL QA PROCESS EXITED SUCCESSFULLY")
    print("Review the complete QA output above.")
else:
    print("❌ V13 FINAL QA FAILED")
    print("Do NOT generate the PDF yet.")
    print("Do NOT commit CHAPTERS_FIXED_V13.html yet.")

print("=" * 100)

sys.exit(result.returncode)
