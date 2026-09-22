#!/usr/bin/env python3
"""
Verify that each PV in a generated PDF starts on its OWN page, in order —
one marker string per PV, in the exact sequence they appear in the
document. This catches the exact bug class that "no blank pages" alone
misses: two short PVs sharing one page, or a page-count that happens to
match the PV count by coincidence while content is actually crammed
together or split wrong.

Why this exists: LibreOffice and real Microsoft Word do NOT always agree on
where short content wraps to a new page. A PV left to "flow naturally"
(no pageBreakBefore) can render correctly under LibreOffice — the tool this
skill's other check (scan_pdf_pages.py) uses — while rendering with two or
three PVs crammed onto one page in real Word, because Word's font-metric
rounding differs slightly at the margin. LibreOffice-only verification is
NOT sufficient proof of correct pagination for a hand-authored template;
this script narrows that gap by asserting the page boundary explicitly,
but it still cannot fully replace checking in real Word when possible.

Usage:
    python3 check_one_pv_per_page.py <file.pdf> "<marker 1>" "<marker 2>" ...

Each <marker N> should be a short, unique substring from PV N's title
(the second title line works well, e.g. "A SĂPĂTURILOR LA REZERVOR") —
enough to find but not so generic it matches other pages' body text.
"""
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("PyMuPDF not installed. Try: pip install pymupdf")


def main():
    if len(sys.argv) < 3:
        sys.exit("Usage: check_one_pv_per_page.py <file.pdf> <marker1> [marker2 ...]")
    pdf_path = sys.argv[1]
    markers = sys.argv[2:]

    doc = fitz.open(pdf_path)
    page_texts = [doc[i].get_text() for i in range(len(doc))]

    if len(doc) != len(markers):
        print(f"FAIL: expected {len(markers)} pages (one per PV marker given), got {len(doc)} pages in {pdf_path}")
        sys.exit(1)

    failed = False
    for i, marker in enumerate(markers):
        found_on = [p + 1 for p, text in enumerate(page_texts) if marker in text]
        if found_on == [i + 1]:
            print(f"OK: marker {i + 1} ({marker!r}) found on page {i + 1} only")
        elif not found_on:
            print(f"FAIL: marker {i + 1} ({marker!r}) not found on any page")
            failed = True
        elif len(found_on) > 1:
            print(f"FAIL: marker {i + 1} ({marker!r}) found on multiple pages {found_on} — a PV is split or duplicated")
            failed = True
        else:
            print(f"FAIL: marker {i + 1} ({marker!r}) found on page {found_on[0]}, expected page {i + 1} — PVs are sharing/skipping pages")
            failed = True

    if failed:
        sys.exit(1)
    print(f"\nAll {len(markers)} PVs confirmed one-per-page, in order.")


if __name__ == "__main__":
    main()
