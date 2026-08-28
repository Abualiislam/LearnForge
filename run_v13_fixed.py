from pathlib import Path
import re
import shutil
import subprocess
import sys

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("❌ BeautifulSoup missing")
    print("Run: pip install beautifulsoup4")
    sys.exit(1)

SRC = Path("CHAPTERS_FIXED_V12.html")
OUT = Path("CHAPTERS_FIXED_V13.html")
QA = Path("final_qa.py")
QA_BACKUP = Path("final_qa.py.v12_backup")

TARGETS = {
    "02": "The Foundations of Good Architecture",
    "03": "Requirements Before Architecture",
    "04": "Scalability",
}

MIN_WORDS = 300

if not SRC.exists():
    print(f"❌ Missing: {SRC}")
    sys.exit(1)

if not QA.exists():
    print(f"❌ Missing: {QA}")
    sys.exit(1)

print("=" * 100)
print("LEARNFORGE — V13 FIXED CH02/03/04 REPAIR + FINAL QA")
print("=" * 100)
print(f"SOURCE : {SRC}")
print(f"OUTPUT : {OUT}")
print(f"MIN    : {MIN_WORDS}")
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
    return len(re.findall(
        r"\b[\w’'-]+\b",
        clean_text(node),
        flags=re.UNICODE
    ))


def normalize(s):
    s = s.lower()
    s = re.sub(r"\bchapter\s*0*\d+\b", "", s)
    s = re.sub(r"\bch\s*0*\d+\b", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return " ".join(s.split())


def title_match(h1, expected):
    actual = normalize(h1.get_text(" ", strip=True))
    wanted = normalize(expected)

    return (
        actual == wanted
        or wanted in actual
        or actual in wanted
    )


def section_for_h1(h1):
    sec = h1.find_parent("section")
    if sec:
        return sec

    sec = soup.new_tag("section")

    for node in list(h1.next_siblings):
        if getattr(node, "name", None) == "h1":
            break
        sec.append(node)

    return sec


# ------------------------------------------------------------------
# Find ALL H1s by TITLE, not by "CHAPTER 02" text.
# ------------------------------------------------------------------

all_h1 = soup.find_all("h1")

print(f"TOTAL H1 FOUND: {len(all_h1)}")
print()

candidates = {}

for num, title in TARGETS.items():
    found = []

    for h1 in all_h1:
        if title_match(h1, title):
            sec = section_for_h1(h1)
            wc = word_count(sec)

            attrs = (
                str(sec.attrs).lower()
                + " "
                + " ".join(sec.get("class", [])).lower()
            )

            hidden = any(x in attrs for x in [
                "hidden",
                "obsolete",
                "duplicate",
                "display:none"
            ])

            found.append({
                "h1": h1,
                "section": sec,
                "words": wc,
                "hidden": hidden,
            })

    found.sort(
        key=lambda x: (
            not x["hidden"],
            x["words"]
        ),
        reverse=True
    )

    candidates[num] = found

    print(f"===== CH{num} CANDIDATES =====")

    if not found:
        print(f"❌ No H1 matching: {title}")
    else:
        for i, c in enumerate(found, 1):
            print(
                f"{i:02d}. words={c['words']:5d} "
                f"hidden={str(c['hidden']):5s} "
                f"title={c['h1'].get_text(' ', strip=True)}"
            )

    print()


# ------------------------------------------------------------------
# Repair CH02 / CH03 / CH04.
#
# Never fabricate text.
# Only replace a short chapter with another legitimate section
# having the SAME title and >=300 words.
# ------------------------------------------------------------------

repair_log = []

for num, title in TARGETS.items():

    print(f"===== CH{num} REPAIR =====")

    found = candidates[num]

    if not found:
        print(f"❌ CH{num}: title not found")
        repair_log.append((num, "NOT_FOUND"))
        print()
        continue

    # Current/active section = visible candidate with highest word count.
    visible = [x for x in found if not x["hidden"]]

    if visible:
        current = visible[0]
    else:
        current = found[0]

    current_words = current["words"]

    print(f"Current: {current_words} words")
    print(f"Title  : {title}")

    if current_words >= MIN_WORDS:
        print(
            f"✅ CH{num} already >= {MIN_WORDS} words — untouched"
        )
        repair_log.append(
            (num, "UNCHANGED", current_words)
        )
        print()
        continue

    # Find a stronger legitimate duplicate/alternate.
    alternatives = [
        x for x in found
        if x["section"] is not current["section"]
        and x["words"] >= MIN_WORDS
    ]

    if not alternatives:
        print(
            f"❌ CH{num}: NO legitimate >= {MIN_WORDS}-word "
            f"same-title section found."
        )
        print("   NO FABRICATION PERFORMED.")
        repair_log.append(
            (num, "NO_VALID_ALTERNATIVE", current_words)
        )
        print()
        continue

    best = alternatives[0]

    print(
        f"Selected alternative: {best['words']} words"
    )

    replacement_soup = BeautifulSoup(
        str(best["section"]),
        "html.parser"
    )

    replacement = replacement_soup.find("section")

    if replacement is None:
        print(f"❌ CH{num}: replacement parse failed")
        repair_log.append(
            (num, "PARSE_FAILED")
        )
        print()
        continue

    # Preserve current section attributes.
    for key, value in current["section"].attrs.items():
        if key not in replacement.attrs:
            replacement.attrs[key] = value

    current["section"].replace_with(replacement)

    # Remove obsolete/duplicate copies of this chapter.
    removed = 0

    for sec in soup.find_all("section"):

        if sec is replacement:
            continue

        h1 = sec.find("h1")

        if h1 is None:
            continue

        if not title_match(h1, title):
            continue

        attrs = (
            str(sec.attrs).lower()
            + " "
            + " ".join(sec.get("class", [])).lower()
        )

        if (
            "duplicate" in attrs
            or "obsolete" in attrs
        ):
            sec.decompose()
            removed += 1

    final_words = word_count(replacement)

    if final_words >= MIN_WORDS:
        print(
            f"✅ CH{num} REPAIRED: "
            f"{current_words} → {final_words} words"
        )
        print(f"   Removed duplicate/obsolete: {removed}")

        repair_log.append(
            (
                num,
                "REPAIRED",
                current_words,
                final_words
            )
        )
    else:
        print(
            f"❌ CH{num} verification failed: "
            f"{final_words} words"
        )
        repair_log.append(
            (
                num,
                "VERIFY_FAILED",
                final_words
            )
        )

    print()


# ------------------------------------------------------------------
# Verify target chapters BEFORE writing V13.
# ------------------------------------------------------------------

print("=" * 100)
print("V13 PRE-WRITE VERIFICATION")
print("=" * 100)

failed = False

for num, title in TARGETS.items():

    matches = []

    for h1 in soup.find_all("h1"):
        if title_match(h1, title):
            sec = section_for_h1(h1)
            wc = word_count(sec)
            matches.append(wc)

    valid = [x for x in matches if x >= MIN_WORDS]

    if valid:
        print(
            f"✅ CH{num}: {max(valid)} words >= {MIN_WORDS}"
        )
    else:
        print(
            f"❌ CH{num}: NO >= {MIN_WORDS}-word chapter found"
        )
        failed = True

if failed:
    print()
    print("❌ V13 ABORTED — target repair verification failed.")
    print("❌ V12 was NOT overwritten.")
    sys.exit(1)


# ------------------------------------------------------------------
# Write V13.
# ------------------------------------------------------------------

out_html = str(soup)

if len(out_html.encode("utf-8")) < 10000:
    print("❌ Output unexpectedly tiny")
    sys.exit(1)

OUT.write_text(out_html, encoding="utf-8")

print()
print("=" * 100)
print("V13 CREATED")
print("=" * 100)
print(f"FILE : {OUT}")
print(f"SIZE : {OUT.stat().st_size:,} bytes")
print()


# ------------------------------------------------------------------
# Create a temporary FINAL QA script.
#
# IMPORTANT:
# We DO NOT modify the user's real final_qa.py.
# We make final_qa_v13.py which points to V13.
# ------------------------------------------------------------------

QA_V13 = Path("final_qa_v13.py")

qa = QA.read_text(
    encoding="utf-8",
    errors="ignore"
)

# Replace every obvious V12 filename reference with V13.
qa = qa.replace(
    "CHAPTERS_FIXED_V12.html",
    "CHAPTERS_FIXED_V13.html"
)

# Add a HARD 300-word gate immediately before the normal QA.
gate = r'''
# === V13_HARD_300_GATE ===
from pathlib import Path as _V13_Path
import re as _V13_re
import sys as _V13_sys

try:
    from bs4 import BeautifulSoup as _V13_BS

    _v13_file = _V13_Path("CHAPTERS_FIXED_V13.html")

    if not _v13_file.exists():
        print("❌ V13 HARD GATE: V13 file missing")
        _V13_sys.exit(1)

    _v13_soup = _V13_BS(
        _v13_file.read_text(
            encoding="utf-8",
            errors="ignore"
        ),
        "html.parser"
    )

    _v13_targets = {
        2: "The Foundations of Good Architecture",
        3: "Requirements Before Architecture",
        4: "Scalability",
    }

    _v13_fail = []

    def _v13_norm(s):
        s = s.lower()
        s = _V13_re.sub(
            r"\bchapter\s*0*\d+\b",
            "",
            s
        )
        s = _V13_re.sub(
            r"[^a-z0-9]+",
            " ",
            s
        )
        return " ".join(s.split())

    for _v13_h1 in _v13_soup.find_all("h1"):

        _v13_actual = _v13_norm(
            _v13_h1.get_text(" ", strip=True)
        )

        for _v13_num, _v13_title in _v13_targets.items():

            _v13_expected = _v13_norm(_v13_title)

            if (
                _v13_actual == _v13_expected
                or _v13_expected in _v13_actual
                or _v13_actual in _v13_expected
            ):
                _v13_sec = _v13_h1.find_parent("section")

                if _v13_sec is None:
                    _v13_fail.append(
                        (_v13_num, 0)
                    )
                    continue

                _v13_text = _v13_sec.get_text(
                    " ",
                    strip=True
                )

                _v13_words = len(
                    _V13_re.findall(
                        r"\b[\w’'-]+\b",
                        _v13_text,
                        flags=_V13_re.UNICODE
                    )
                )

                if _v13_words < 300:
                    _v13_fail.append(
                        (_v13_num, _v13_words)
                    )

                break

    if _v13_fail:
        print()
        print("=" * 100)
        print("❌ V13 HARD 300-WORD GATE — FAIL")
        print("=" * 100)

        for _n, _w in _v13_fail:
            print(
                f"❌ CH{_n:02d}: {_w} words "
                f"(minimum 300)"
            )

        print()
        print("❌ FINAL QA IS NOT APPROVED.")
        print("=" * 100)

        _v13_sys.exit(1)

    print("✅ V13 HARD 300-WORD GATE — PASS")

except SystemExit:
    raise

except Exception as _v13_exc:
    print(
        f"❌ V13 HARD GATE ERROR: {_v13_exc}"
    )
    _v13_sys.exit(1)

# === END V13_HARD_300_GATE ===
'''

# Avoid duplicate insertion.
if "V13_HARD_300_GATE" not in qa:

    lines = qa.splitlines(True)

    insert_at = 0

    for i, line in enumerate(lines):
        if line.startswith(("import ", "from ")):
            insert_at = i + 1

    lines.insert(insert_at, gate + "\n")
    qa = "".join(lines)

QA_V13.write_text(
    qa,
    encoding="utf-8"
)

print(f"✅ Created isolated QA: {QA_V13}")
print("ℹ️ Original final_qa.py was NOT modified.")
print()


# ------------------------------------------------------------------
# RUN FINAL QA ON V13.
# ------------------------------------------------------------------

print("=" * 100)
print("RUNNING FINAL QA — V13")
print("=" * 100)
print()

result = subprocess.run(
    [sys.executable, str(QA_V13)],
    cwd=str(Path.cwd())
)

print()
print("=" * 100)

if result.returncode == 0:

    print("🚀 V13 FINAL QA: SUCCESS")
    print()
    print("APPROVED:")
    print("  CH02 >= 300")
    print("  CH03 >= 300")
    print("  CH04 >= 300")
    print("  FINAL QA ran against CHAPTERS_FIXED_V13.html")
    print()
    print("NEXT STEP: PDF generation may proceed.")

else:

    print("❌ V13 FINAL QA: FAILED")
    print()
    print("DO NOT generate PDF.")
    print("DO NOT commit V13.")
    print()
    print(f"Exit code: {result.returncode}")

print("=" * 100)

sys.exit(result.returncode)
