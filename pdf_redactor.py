"""PDF redactor — permanently redact content from a PDF.

Redaction removes both the visual content and the underlying data (text,
images) from the specified areas. The result cannot be reversed.

Coordinates use a top-left origin with y increasing downward, in PDF points
(1 pt = 1/72 inch). Page numbers are 1-based.

Library usage:
    from pdf_redactor import redact_areas, redact_text

    # Redact a rectangle on page 1 (x0, y0, x1, y1)
    redact_areas("input.pdf", "output.pdf", areas=[(1, 100, 50, 400, 80)])

    # Redact every occurrence of a phrase across all pages
    redact_text("input.pdf", "output.pdf", terms=["John Doe", "secret"])

    # Both at once
    redact_areas("input.pdf", "output.pdf",
                 areas=[(1, 100, 50, 400, 80)],
                 terms=["confidential"])

CLI usage:
    # By coordinates
    python pdf_redactor.py input.pdf output.pdf --areas "1:100,50,400,80"

    # By text search
    python pdf_redactor.py input.pdf output.pdf --text "John Doe" "secret"

    # Combined
    python pdf_redactor.py input.pdf output.pdf --text "secret" --areas "1:100,50,400,80"
"""

import argparse
import sys
import traceback
from pathlib import Path

import fitz  # PyMuPDF
from tqdm import tqdm

# Redaction fill colour — solid black (RGB 0-1 scale)
_FILL = (0, 0, 0)


def redact_areas(
    input_path: str,
    output_path: str,
    areas: list[tuple[int, float, float, float, float]],
    terms: list[str] | None = None,
    show_progress: bool = False,
) -> int:
    """Redact rectangular areas and/or text terms from a PDF.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to write the redacted PDF.
        areas: List of (page, x0, y0, x1, y1) tuples. Page is 1-based.
               Coordinates are in PDF points from the top-left corner.
        terms: Optional list of text strings to search and redact on all pages.
        show_progress: Show a tqdm progress bar while processing.

    Returns:
        Total number of redactions applied.

    Raises:
        FileNotFoundError: If input_path does not exist.
        ValueError: If areas and terms are both empty, or a page number is invalid.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not areas and not terms:
        raise ValueError("Provide at least one area or one search term.")

    doc = fitz.open(input_path)
    total_pages = doc.page_count

    # Validate page numbers up front
    for page_num, *_ in (areas or []):
        if page_num < 1 or page_num > total_pages:
            raise ValueError(
                f"Page {page_num} is out of range (document has {total_pages} pages)."
            )

    redaction_count = 0
    pages = tqdm(doc, desc="Redacting", unit="page") if show_progress else doc

    for page in pages:
        page_1based = page.number + 1

        # Area-based redactions on this page
        for p, x0, y0, x1, y1 in (areas or []):
            if p == page_1based:
                rect = fitz.Rect(x0, y0, x1, y1)
                page.add_redact_annot(rect, fill=_FILL)
                redaction_count += 1

        # Text-search redactions on this page
        for term in (terms or []):
            for rect in page.search_for(term):
                page.add_redact_annot(rect, fill=_FILL)
                redaction_count += 1

        page.apply_redactions()

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

    return redaction_count


# Convenience wrapper for text-only usage
def redact_text(
    input_path: str,
    output_path: str,
    terms: list[str],
    show_progress: bool = False,
) -> int:
    """Redact all occurrences of text terms across every page.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to write the redacted PDF.
        terms: Text strings to search for and redact.
        show_progress: Show a tqdm progress bar while processing.

    Returns:
        Total number of redactions applied.

    Raises:
        FileNotFoundError: If input_path does not exist.
        ValueError: If terms is empty.
    """
    if not terms:
        raise ValueError("Provide at least one search term.")
    return redact_areas(input_path, output_path, areas=[], terms=terms,
                        show_progress=show_progress)


def _parse_area(value: str) -> tuple[int, float, float, float, float]:
    """Parse 'PAGE:x0,y0,x1,y1' into a typed tuple."""
    try:
        page_part, coords_part = value.split(":", 1)
        page = int(page_part)
        x0, y0, x1, y1 = (float(v) for v in coords_part.split(","))
    except Exception:
        raise argparse.ArgumentTypeError(
            f"Invalid area '{value}'. Expected format: PAGE:x0,y0,x1,y1  (e.g. 1:100,50,400,80)"
        )
    return (page, x0, y0, x1, y1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Permanently redact content from a PDF.",
        usage=(
            "%(prog)s input.pdf output.pdf [--areas PAGE:x0,y0,x1,y1 ...] [--text TERM ...]\n\n"
            "Coordinates are in PDF points (1 pt = 1/72 inch) from the top-left corner.\n"
            "At least one of --areas or --text is required."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", help="Source PDF file.")
    parser.add_argument("output", help="Path for the redacted output PDF.")
    parser.add_argument(
        "--areas",
        nargs="+",
        metavar="PAGE:x0,y0,x1,y1",
        type=_parse_area,
        default=[],
        help="Rectangles to redact. PAGE is 1-based. Example: 1:100,50,400,80",
    )
    parser.add_argument(
        "--text",
        nargs="+",
        metavar="TERM",
        default=[],
        help="Text phrases to search and redact across all pages.",
    )
    args = parser.parse_args()

    if not args.areas and not args.text:
        parser.error("Provide at least one of --areas or --text.")

    try:
        count = redact_areas(
            args.input, args.output,
            areas=args.areas,
            terms=args.text,
            show_progress=True,
        )
        print(f"Applied {count} redaction(s). Written to '{args.output}'.")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
