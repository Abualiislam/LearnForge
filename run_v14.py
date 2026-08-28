from pathlib import Path
from bs4 import BeautifulSoup
import re
import subprocess
import sys

SRC = Path("CHAPTERS_FIXED_V12.html")
OUT = Path("CHAPTERS_FIXED_V14.html")
QA = Path("final_qa.py")
QA_V14 = Path("final_qa_v14.py")

TARGETS = {
    "02": ("The Foundations of Good Architecture", "chapter-02", "ch02"),
    "03": ("Requirements Before Architecture", "chapter-03", "ch03"),
    "04": ("Scalability", "chapter-04", "ch04"),
}

MIN_WORDS = 300

if not SRC.exists():
    print(f"❌ Missing: {SRC}")
    sys.exit(1)

if not QA.exists():
    print(f"❌ Missing: {QA}")
    sys.exit(1)

print("=" * 100)
print("LEARNFORGE — V14 FINAL CH02/03/04 REPAIR")
print("=" * 100)
print(f"SOURCE : {SRC}")
print(f"OUTPUT : {OUT}")
print(f"MIN    : {MIN_WORDS}")
print()

html = SRC.read_text(encoding="utf-8", errors="ignore")
soup = BeautifulSoup(html, "html.parser")


def clean_text(node):
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


def find_id(sec_id):
    return soup.find(id=sec_id)


def verify_section(sec, expected_title):
    if sec is None:
        return False, 0

    h1 = sec.find("h1")
    if h1 is None:
        return False, 0

    actual = " ".join(h1.get_text(" ", strip=True).split()).lower()
    expected = expected_title.lower()

    if expected not in actual and actual not in expected:
        return False, word_count(sec)

    wc = word_count(sec)
    return wc >= MIN_WORDS, wc


print("===== V14 DISCOVERY =====")

for num, (title, final_id, visible_id) in TARGETS.items():

    final_sec = find_id(final_id)
    visible_sec = find_id(visible_id)

    print()
    print(f"CH{num}: {title}")

    if final_sec is None:
        print(f"❌ Missing final section: #{final_id}")
        sys.exit(1)

    if visible_sec is None:
        print(f"❌ Missing visible section: #{visible_id}")
        sys.exit(1)

    final_wc = word_count(final_sec)
    visible_wc = word_count(visible_sec)

    print(f"  #{final_id} : {final_wc} words")
    print(f"  #{visible_id}: {visible_wc} words")

    ok, _ = verify_section(visible_sec, title)

    if not ok:
        print(
            f"❌ Visible source #{visible_id} is NOT a valid "
            f">= {MIN_WORDS}-word source."
        )
        print("❌ V14 ABORTED — no fabrication performed.")
        sys.exit(1)

    print(
        f"✅ Valid source found: #{visible_id} "
        f"({visible_wc} words)"
    )


print()
print("=" * 100)
print("V14 REPAIR")
print("=" * 100)

repair_log = []

for num, (title, final_id, visible_id) in TARGETS.items():

    final_sec = find_id(final_id)
    visible_sec = find_id(visible_id)

    before = word_count(final_sec)
    source_words = word_count(visible_sec)

    print()
    print(f"===== CH{num} =====")
    print(f"FINAL TARGET : #{final_id}")
    print(f"SOURCE       : #{visible_id}")
    print(f"BEFORE       : {before} words")
    print(f"SOURCE       : {source_words} words")

    # Clone only the CONTENT of the legitimate visible chapter.
    source_clone = BeautifulSoup(
        str(visible_sec),
        "html.parser"
    ).find(id=visible_id)

    if source_clone is None:
        print(f"❌ Could not clone #{visible_id}")
        sys.exit(1)

    # Preserve final chapter ID and required final class.
    source_clone["id"] = final_id

    if "class" not in source_clone.attrs:
        source_clone["class"] = ["chapter"]

    # Remove hidden display:none style from the final section.
    for style in source_clone.find_all("style"):
        if "display:none" in style.get_text(
            " ",
            strip=True
        ).replace(" ", "").lower():
            style.decompose()

    # Ensure chapter kicker remains correct.
    kicker = source_clone.find(
        class_=lambda c: c and "chapter-kicker" in c
    )

    if kicker is not None:
        kicker.string = f"CHAPTER {num}"

    # Replace the old hidden final chapter with the
    # legitimate visible chapter content.
    final_sec.replace_with(source_clone)

    # Remove the old visible duplicate from the document.
    duplicate = soup.find(id=visible_id)

    if duplicate is not None:
        duplicate.decompose()
        print(f"🧹 Removed duplicate #{visible_id}")

    new_final = soup.find(id=final_id)

    if new_final is None:
        print(f"❌ CH{num}: final section disappeared")
        sys.exit(1)

    after = word_count(new_final)

    print(f"AFTER        : {after} words")

    if after < MIN_WORDS:
        print(
            f"❌ CH{num}: verification failed "
            f"({after} < {MIN_WORDS})"
        )
        sys.exit(1)

    print(
        f"✅ CH{num} REPAIRED: "
        f"{before} → {after} words"
    )

    repair_log.append(
        (num, before, source_words, after)
    )


print()
print("=" * 100)
print("V14 PRE-WRITE HARD VERIFICATION")
print("=" * 100)

for num, (title, final_id, visible_id) in TARGETS.items():

    sec = soup.find(id=final_id)

    if sec is None:
        print(f"❌ CH{num}: #{final_id} missing")
        sys.exit(1)

    h1 = sec.find("h1")

    if h1 is None:
        print(f"❌ CH{num}: H1 missing")
        sys.exit(1)

    wc = word_count(sec)

    print(
        f"CH{num}: {wc} words | "
        f"{h1.get_text(' ', strip=True)}"
    )

    if wc < MIN_WORDS:
        print(
            f"❌ CH{num} BELOW HARD MINIMUM "
            f"({wc} < {MIN_WORDS})"
        )
        sys.exit(1)

print()
print("✅ CH02 >= 300")
print("✅ CH03 >= 300")
print("✅ CH04 >= 300")

# Structural safety check.
out_html = str(soup)

if len(out_html.encode("utf-8")) < 10000:
    print("❌ V14 output unexpectedly tiny")
    sys.exit(1)

OUT.write_text(out_html, encoding="utf-8")

print()
print("=" * 100)
print("V14 CREATED")
print("=" * 100)
print(f"FILE : {OUT}")
print(f"SIZE : {OUT.stat().st_size:,} bytes")
print()

# ------------------------------------------------------------------
# Create isolated QA script.
# Original final_qa.py remains untouched.
# ------------------------------------------------------------------

qa = QA.read_text(
    encoding="utf-8",
    errors="ignore"
)

qa = qa.replace(
    "CHAPTERS_FIXED_V12.html",
    "CHAPTERS_FIXED_V14.html"
)

gate = r'''
# === V14_HARD_300_GATE ===
from pathlib import Path as _V14_Path
import re as _V14_re
import sys as _V14_sys

try:
    from bs4 import BeautifulSoup as _V14_BS

    _v14_file = _V14_Path("CHAPTERS_FIXED_V14.html")

    if not _v14_file.exists():
        print("❌ V14 HARD GATE: V14 file missing")
        _V14_sys.exit(1)

    _v14_soup = _V14_BS(
        _v14_file.read_text(
            encoding="utf-8",
            errors="ignore"
        ),
        "html.parser"
    )

    _v14_targets = {
        "02": (
            "The Foundations of Good Architecture",
            "chapter-02"
        ),
        "03": (
            "Requirements Before Architecture",
            "chapter-03"
        ),
        "04": (
            "Scalability",
            "chapter-04"
        ),
    }

    _v14_fail = []

    for _v14_num, (_v14_title, _v14_id) in _v14_targets.items():

        _v14_sec = _v14_soup.find(
            id=_v14_id
        )

        if _v14_sec is None:
            _v14_fail.append((_v14_num, 0))
            continue

        _v14_text = _v14_sec.get_text(
            " ",
            strip=True
        )

        _v14_words = len(
            _V14_re.findall(
                r"\b[\w’'-]+\b",
                _v14_text,
                flags=_V14_re.UNICODE
            )
        )

        if _v14_words < 300:
            _v14_fail.append(
                (_v14_num, _v14_words)
            )

    if _v14_fail:
        print()
        print("=" * 100)
        print("❌ V14 HARD 300-WORD GATE — FAIL")
        print("=" * 100)

        for _n, _w in _v14_fail:
            print(
                f"❌ CH{_n}: {_w} words "
                f"(minimum 300)"
            )

        print()
        print("❌ FINAL QA NOT APPROVED")
        print("=" * 100)
        _V14_sys.exit(1)

    print(
        "✅ V14 HARD 300-WORD GATE — PASS"
    )

except SystemExit:
    raise

except Exception as _v14_exc:
    print(
        f"❌ V14 HARD GATE ERROR: {_v14_exc}"
    )
    _V14_sys.exit(1)

# === END V14_HARD_300_GATE ===
'''

if "V14_HARD_300_GATE" not in qa:

    lines = qa.splitlines(True)

    insert_at = 0

    for i, line in enumerate(lines):
        if line.startswith(("import ", "from ")):
            insert_at = i + 1

    lines.insert(
        insert_at,
        gate + "\n"
    )

    qa = "".join(lines)

QA_V14.write_text(
    qa,
    encoding="utf-8"
)

print(
    f"✅ Created isolated QA: {QA_V14}"
)
print(
    "ℹ️ Original final_qa.py was NOT modified."
)
print()

# ------------------------------------------------------------------
# Run FINAL QA against V14.
# ------------------------------------------------------------------

print("=" * 100)
print("RUNNING FINAL QA — V14")
print("=" * 100)
print()

result = subprocess.run(
    [sys.executable, str(QA_V14)],
    cwd=str(Path.cwd())
)

print()
print("=" * 100)

if result.returncode == 0:

    print("🚀 V14 FINAL QA: SUCCESS")
    print()
    print("APPROVED:")
    print("  CH02 >= 300")
    print("  CH03 >= 300")
    print("  CH04 >= 300")
    print("  FINAL QA ran against CHAPTERS_FIXED_V14.html")
    print()
    print("NEXT STEP: PDF generation may proceed.")

else:

    print("❌ V14 FINAL QA: FAILED")
    print()
    print("DO NOT generate PDF.")
    print("DO NOT commit V14.")
    print()
    print(f"Exit code: {result.returncode}")

print("=" * 100)

sys.exit(result.returncode)
