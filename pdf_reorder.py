"""PDF reorder — rearrange pages in a PDF.

Library usage:
    from pdf_reorder import reorder_pdf

    # Reverse a 3-page PDF
    reorder_pdf("input.pdf", "output.pdf", [3, 2, 1])

    # Duplicate page 1, then page 2
    reorder_pdf("input.pdf", "output.pdf", [1, 1, 2])

    # Extract only pages 2 and 4
    reorder_pdf("input.pdf", "output.pdf", [2, 4])

CLI usage:
    python pdf_reorder.py input.pdf output.pdf 3 2 1
"""

import argparse
import sys
import traceback
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from tqdm import tqdm


def reorder_pdf(
    input_path: str,
    output_path: str,
    page_order: list[int],
    show_progress: bool = False,
) -> int:
    """Rearrange pages of a PDF into a new order.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to write the reordered PDF.
        page_order: 1-based page numbers in the desired output order.
                    Pages may be repeated or omitted.
        show_progress: Show a tqdm progress bar while processing.

    Returns:
        Number of pages in the output document.

    Raises:
        FileNotFoundError: If input_path does not exist.
        ValueError: If page_order is empty or contains out-of-range numbers.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not page_order:
        raise ValueError("page_order must not be empty.")

    reader = PdfReader(input_path)
    total_pages = len(reader.pages)

    invalid = [p for p in page_order if p < 1 or p > total_pages]
    if invalid:
        raise ValueError(
            f"Page numbers out of range (document has {total_pages} pages): {invalid}"
        )

    writer = PdfWriter()
    try:
        pages = (
            tqdm(page_order, desc="Reordering", unit="page")
            if show_progress
            else page_order
        )
        for page_num in pages:
            writer.add_page(reader.pages[page_num - 1])  # convert to 0-based
        writer.write(output_path)
    finally:
        writer.close()

    return len(page_order)


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="Rearrange pages of a PDF into a new order.",
        usage="%(prog)s input.pdf output.pdf PAGE [PAGE ...]",
        epilog=(
            "Pages are 1-based. You may repeat or omit pages.\n"
            "Examples:\n"
            "  Reverse:        %(prog)s in.pdf out.pdf 3 2 1\n"
            "  Duplicate p1:   %(prog)s in.pdf out.pdf 1 1 2 3\n"
            "  Extract p2, p4: %(prog)s in.pdf out.pdf 2 4"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", help="Source PDF file.")
    parser.add_argument("output", help="Path for the reordered output PDF.")
    parser.add_argument(
        "pages",
        nargs="+",
        metavar="PAGE",
        type=int,
        help="1-based page numbers in desired output order.",
    )
    args = parser.parse_args()

    try:
        count = reorder_pdf(args.input, args.output, args.pages, show_progress=True)
        print(f"Written '{args.output}' ({count} pages).")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
