"""PDF diff - compare two PDFs and report or visualise differences.

Text differences are identified by comparing extracted text per page.
Visual differences are highlighted in the output PDF (yellow for changed
regions, green border for added pages, red placeholder for removed pages).

Library usage:
    from pdf_diff import diff_report, diff_visual

    # Get a structured text diff
    report = diff_report("v1.pdf", "v2.pdf")
    for item in report["changed_pages"]:
        print(f"Page {item['page']}:")
        print(item["diff"])

    # Produce a PDF with visual highlights
    report = diff_visual("v1.pdf", "v2.pdf", "diff.pdf")

CLI usage:
    # Print text diff report only
    python pdf_diff.py v1.pdf v2.pdf

    # Also produce a visual diff PDF
    python pdf_diff.py v1.pdf v2.pdf --output diff.pdf

    # Control render DPI for pixel comparison (default 150; lower = faster)
    python pdf_diff.py v1.pdf v2.pdf --output diff.pdf --dpi 100
"""

import argparse
import difflib
import sys
import traceback
from pathlib import Path

import fitz  # PyMuPDF
from tqdm import tqdm


def diff_report(
    pdf_a: str,
    pdf_b: str,
) -> dict:
    """Compare two PDFs and return a structured text-based diff report.

    Args:
        pdf_a: Path to the first (original) PDF.
        pdf_b: Path to the second (modified) PDF.

    Returns:
        A dict with keys:
            - pages_a (int): page count of pdf_a.
            - pages_b (int): page count of pdf_b.
            - added_pages (list[int]): 1-based page numbers present in B only.
            - removed_pages (list[int]): 1-based page numbers present in A only.
            - changed_pages (list[dict]): pages with text differences, each with:
                - page (int): 1-based page number.
                - diff (str): unified diff of the page text.

    Raises:
        FileNotFoundError: If either PDF does not exist.
    """
    for path in (pdf_a, pdf_b):
        if not Path(path).exists():
            raise FileNotFoundError(f"File not found: {path}")

    doc_a = fitz.open(pdf_a)
    doc_b = fitz.open(pdf_b)

    n_a = doc_a.page_count
    n_b = doc_b.page_count
    n_common = min(n_a, n_b)

    changed_pages = []
    for i in range(n_common):
        text_a = doc_a[i].get_text().splitlines(keepends=True)
        text_b = doc_b[i].get_text().splitlines(keepends=True)
        if text_a != text_b:
            diff = "".join(difflib.unified_diff(
                text_a, text_b,
                fromfile=f"a/page {i + 1}",
                tofile=f"b/page {i + 1}",
            ))
            changed_pages.append({"page": i + 1, "diff": diff})

    doc_a.close()
    doc_b.close()

    return {
        "pages_a": n_a,
        "pages_b": n_b,
        "added_pages": list(range(n_common + 1, n_b + 1)) if n_b > n_a else [],
        "removed_pages": list(range(n_common + 1, n_a + 1)) if n_a > n_b else [],
        "changed_pages": changed_pages,
    }


def _insert_side_by_side(
    out_doc: fitz.Document,
    doc_a: fitz.Document,
    doc_b: fitz.Document,
    page_a_idx: int,
    page_b_idx: int,
    gap: float,
    label_h: float,
    word_rects_a: list[fitz.Rect] | None = None,
    word_rects_b: list[fitz.Rect] | None = None,
    bands: list[tuple[int, int]] | None = None,
    pix_h: int = 0,
    h_a: float = 0,
    h_b: float = 0,
) -> None:
    """Create a side-by-side page: doc_a on left, doc_b on right.

    Word-level highlights take priority:
      - word_rects_a: rects on the A side highlighted in red (removed/changed words).
      - word_rects_b: rects on the B side highlighted in green (added/changed words).

    If no word highlights are provided, yellow row-band highlights are drawn
    instead (fallback for visual-only changes).
    Labels "A - original" and "B - modified" are placed at the bottom.
    """
    page_a = doc_a[page_a_idx]
    page_b = doc_b[page_b_idx]
    w_a = page_a.rect.width
    w_b = page_b.rect.width
    content_h = max(page_a.rect.height, page_b.rect.height)
    total_w = w_a + gap + w_b
    total_h = content_h + label_h

    out_page = out_doc.new_page(width=total_w, height=total_h)

    # Render source pages into the two halves
    rect_a = fitz.Rect(0, 0, w_a, page_a.rect.height)
    rect_b = fitz.Rect(w_a + gap, 0, total_w, page_b.rect.height)
    out_page.show_pdf_page(rect_a, doc_a, page_a_idx)
    out_page.show_pdf_page(rect_b, doc_b, page_b_idx)

    # Dividing line
    out_page.draw_line(fitz.Point(w_a + gap / 2, 0),
                       fitz.Point(w_a + gap / 2, content_h),
                       color=(0.7, 0.7, 0.7), width=1)

    if word_rects_a or word_rects_b:
        # Word-level highlights: red on A side, green on B side
        for rect in (word_rects_a or []):
            out_page.draw_rect(rect, color=None, fill=(1.0, 0.4, 0.4), fill_opacity=0.5, width=0)
        for rect in (word_rects_b or []):
            shifted = fitz.Rect(rect.x0 + w_a + gap, rect.y0,
                                rect.x1 + w_a + gap, rect.y1)
            out_page.draw_rect(shifted, color=None, fill=(0.3, 1.0, 0.3), fill_opacity=0.5, width=0)
    elif bands and pix_h > 0:
        # Fallback: yellow row bands for visual-only changes
        scale_a = h_a / pix_h
        scale_b = h_b / pix_h
        for r0, r1 in bands:
            y0_a, y1_a = r0 * scale_a, (r1 + 1) * scale_a
            out_page.draw_rect(fitz.Rect(0, y0_a, w_a, y1_a),
                               color=None, fill=(1.0, 0.9, 0.0), fill_opacity=0.4, width=0)
            y0_b, y1_b = r0 * scale_b, (r1 + 1) * scale_b
            out_page.draw_rect(fitz.Rect(w_a + gap, y0_b, total_w, y1_b),
                               color=None, fill=(1.0, 0.9, 0.0), fill_opacity=0.4, width=0)

    # Labels
    label_y = content_h + label_h - 4
    out_page.insert_text(fitz.Point(4, label_y), "A - original",
                         fontsize=10, color=(0.6, 0.1, 0.1))
    out_page.insert_text(fitz.Point(w_a + gap + 4, label_y), "B - modified",
                         fontsize=10, color=(0.1, 0.5, 0.1))


def diff_visual(
    pdf_a: str,
    pdf_b: str,
    output_path: str,
    dpi: int = 150,
    show_progress: bool = False,
) -> dict:
    """Produce a PDF highlighting differences between two PDFs.

    Changed pages are shown side-by-side (A on the left, B on the right).
    For text changes, removed words are highlighted in red on the A side and
    added words in green on the B side. For visual-only changes (e.g. images),
    yellow row bands mark the differing regions. Identical pages show only B's
    content. Added pages (present only in B) receive a green border. Removed
    pages (present only in A) are represented by a red placeholder.

    Args:
        pdf_a: Path to the first (original) PDF.
        pdf_b: Path to the second (modified) PDF.
        output_path: Path to write the diff PDF.
        dpi: Render resolution for pixel-level comparison (default 150).
        show_progress: Show a tqdm progress bar while processing.

    Returns:
        The same summary dict as diff_report (pages_a, pages_b,
        added_pages, removed_pages, changed_pages).

    Raises:
        FileNotFoundError: If either PDF does not exist.
        ValueError: If dpi is not positive.
    """
    for path in (pdf_a, pdf_b):
        if not Path(path).exists():
            raise FileNotFoundError(f"File not found: {path}")
    if not 1 <= dpi <= 600:
        raise ValueError(f"DPI must be between 1 and 600, got {dpi}.")

    doc_a = fitz.open(pdf_a)
    doc_b = fitz.open(pdf_b)
    out_doc = fitz.open()

    n_a = doc_a.page_count
    n_b = doc_b.page_count
    n_common = min(n_a, n_b)

    _ADDED   = (0.0, 0.7, 0.0)  # green - used for added-page border
    _REMOVED = (0.9, 0.1, 0.1)  # red   - used for removed-page placeholder

    changed_pages = []
    mat = fitz.Matrix(dpi / 72, dpi / 72)

    pages_iter = range(n_common)
    if show_progress:
        pages_iter = tqdm(pages_iter, desc="Comparing", unit="page")

    _GAP    = 12   # points between the two half-pages
    _LABEL  = 16   # points reserved at the bottom for labels

    for i in pages_iter:
        page_a = doc_a[i]
        page_b = doc_b[i]

        gray_a = page_a.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)
        gray_b = page_b.get_pixmap(matrix=mat, colorspace=fitz.csGRAY)

        # If page dimensions differ: side-by-side without pixel diff
        if gray_a.width != gray_b.width or gray_a.height != gray_b.height:
            _insert_side_by_side(out_doc, doc_a, doc_b, i, i, _GAP, _LABEL)
            changed_pages.append({"page": i + 1, "diff": "<page dimensions changed>"})
            continue

        # Find rows that differ (grayscale = 1 byte per pixel)
        pw = gray_b.width
        ph = gray_b.height
        samples_a = gray_a.samples
        samples_b = gray_b.samples

        changed_rows: set[int] = set()
        for row in range(ph):
            start = row * pw
            end = start + pw
            if samples_a[start:end] != samples_b[start:end]:
                changed_rows.add(row)

        if not changed_rows:
            # Pages are visually identical - copy B as-is
            out_doc.insert_pdf(doc_b, from_page=i, to_page=i)
            continue

        # Group contiguous changed rows into bands
        sorted_rows = sorted(changed_rows)
        bands: list[tuple[int, int]] = []
        band_start = band_end = sorted_rows[0]
        for row in sorted_rows[1:]:
            if row == band_end + 1:
                band_end = row
            else:
                bands.append((band_start, band_end))
                band_start = band_end = row
        bands.append((band_start, band_end))

        # Word-level diff for precise highlighting
        words_a = page_a.get_text("words")  # (x0, y0, x1, y1, word, ...)
        words_b = page_b.get_text("words")
        seq_a = [w[4] for w in words_a]
        seq_b = [w[4] for w in words_b]

        rects_a: list[fitz.Rect] = []
        rects_b: list[fitz.Rect] = []
        sm = difflib.SequenceMatcher(None, seq_a, seq_b, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            if tag in ("delete", "replace"):
                for w in words_a[i1:i2]:
                    rects_a.append(fitz.Rect(w[0], w[1], w[2], w[3]))
            if tag in ("insert", "replace"):
                for w in words_b[j1:j2]:
                    rects_b.append(fitz.Rect(w[0], w[1], w[2], w[3]))

        if rects_a or rects_b:
            # Text changed: use word-level red/green highlights
            _insert_side_by_side(out_doc, doc_a, doc_b, i, i, _GAP, _LABEL,
                                 word_rects_a=rects_a, word_rects_b=rects_b)
        else:
            # Visual-only change (e.g. image replaced): fall back to row bands
            _insert_side_by_side(out_doc, doc_a, doc_b, i, i, _GAP, _LABEL,
                                 bands=bands, pix_h=ph,
                                 h_a=page_a.rect.height, h_b=page_b.rect.height)

        # Record the text diff (or note a visual-only change)
        text_a = page_a.get_text().splitlines(keepends=True)
        text_b = page_b.get_text().splitlines(keepends=True)
        if text_a != text_b:
            diff = "".join(difflib.unified_diff(
                text_a, text_b,
                fromfile=f"a/page {i + 1}",
                tofile=f"b/page {i + 1}",
            ))
            changed_pages.append({"page": i + 1, "diff": diff})
        else:
            changed_pages.append({"page": i + 1, "diff": "<visual change only - text is identical>"})

    # Pages only in B (added)
    for i in range(n_common, n_b):
        out_doc.insert_pdf(doc_b, from_page=i, to_page=i)
        out_page = out_doc[-1]
        r = out_page.rect
        inner = fitz.Rect(r.x0 + 5, r.y0 + 5, r.x1 - 5, r.y1 - 5)
        out_page.draw_rect(inner, color=_ADDED, width=6)
        out_page.insert_text(fitz.Point(15, 25), f"[ADDED - page {i + 1}]",
                             fontsize=12, color=_ADDED)

    # Pages only in A (removed) - insert a placeholder
    for i in range(n_common, n_a):
        page_a = doc_a[i]
        out_page = out_doc.new_page(width=page_a.rect.width, height=page_a.rect.height)
        out_page.draw_rect(out_page.rect, color=_REMOVED, fill=_REMOVED, fill_opacity=0.12, width=4)
        out_page.insert_text(fitz.Point(15, 25),
                             f"[REMOVED - page {i + 1} of original]",
                             fontsize=12, color=_REMOVED)

    out_doc.save(output_path, garbage=4, deflate=True)
    out_doc.close()
    doc_a.close()
    doc_b.close()

    added_pages = list(range(n_common + 1, n_b + 1)) if n_b > n_a else []
    removed_pages = list(range(n_common + 1, n_a + 1)) if n_a > n_b else []

    return {
        "pages_a": n_a,
        "pages_b": n_b,
        "added_pages": added_pages,
        "removed_pages": removed_pages,
        "changed_pages": changed_pages,
    }


def _format_report(report: dict) -> str:
    lines = [
        f"PDF A: {report['pages_a']} page(s)",
        f"PDF B: {report['pages_b']} page(s)",
    ]
    if report["added_pages"]:
        lines.append(f"Added pages (in B only):   {report['added_pages']}")
    if report["removed_pages"]:
        lines.append(f"Removed pages (in A only): {report['removed_pages']}")

    if not report["changed_pages"] and not report["added_pages"] and not report["removed_pages"]:
        lines.append("No differences found.")
    elif report["changed_pages"]:
        lines.append(f"\nChanged pages ({len(report['changed_pages'])}):")
        for item in report["changed_pages"]:
            lines.append(f"\n--- Page {item['page']} ---")
            lines.append(item["diff"].rstrip())

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare two PDFs and report or visualise differences.",
        usage="%(prog)s a.pdf b.pdf [--output diff.pdf] [--dpi N]",
    )
    parser.add_argument("pdf_a", help="Original PDF (version A).")
    parser.add_argument("pdf_b", help="Modified PDF (version B).")
    parser.add_argument(
        "--output", "-o",
        metavar="FILE",
        help="Write a visual diff PDF to this path.",
    )
    parser.add_argument(
        "--dpi",
        type=int, default=150,
        metavar="N",
        help="Render DPI for pixel comparison (default: 150). Lower is faster.",
    )
    args = parser.parse_args()

    try:
        if args.output:
            report = diff_visual(
                args.pdf_a, args.pdf_b, args.output,
                dpi=args.dpi,
                show_progress=True,
            )
            print(_format_report(report))
            print(f"\nVisual diff written to '{args.output}'.")
        else:
            report = diff_report(args.pdf_a, args.pdf_b)
            print(_format_report(report))
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
