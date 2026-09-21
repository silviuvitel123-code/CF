#!/usr/bin/env python3
"""
Scan a PDF (typically a LibreOffice-converted .docx PV template) page by
page and flag pages that look blank or near-blank.

Why a fixed threshold works here: every page of a PV document repeats the
same ~6-line company letterhead, which alone contributes roughly 230
characters of extracted text. A page with real content comfortably clears
that; a page that's blank (or holds only a stray signature block that
slipped onto its own page) barely does. This is a heuristic, not a proof —
always eyeball the pages this script flags (and a couple it doesn't) before
trusting the result.

Usage:
    python3 scan_pdf_pages.py <file.pdf> [--threshold 260]
"""
import sys
import argparse

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("PyMuPDF not installed. Try: pip install pymupdf")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("pdf_path")
    p.add_argument("--threshold", type=int, default=260,
                    help="pages with fewer extracted characters than this are flagged (default 260, tuned for a ~230-char repeating letterhead)")
    args = p.parse_args()

    doc = fitz.open(args.pdf_path)
    print(f"{args.pdf_path}: {len(doc)} pages\n")

    flagged = []
    for i, page in enumerate(doc):
        text = page.get_text().strip()
        chars = len(text)
        is_flagged = chars < args.threshold
        if is_flagged:
            flagged.append(i + 1)
        marker = "  <-- LOOKS BLANK/NEAR-BLANK" if is_flagged else ""
        print(f"page {i + 1:>3}: {chars:>5} chars{marker}")

    print()
    if flagged:
        print(f"FLAGGED: {len(flagged)} page(s) look blank/near-blank: {flagged}")
        sys.exit(1)
    else:
        print("No blank/near-blank pages found by this heuristic.")
        print("Still check manually: signature rows wrapping to 2 lines, and")
        print("titles that end a page without the rest of their own content.")


if __name__ == "__main__":
    main()
