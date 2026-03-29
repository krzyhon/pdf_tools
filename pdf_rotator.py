"""PDF rotator — rotate pages in a PDF.

Library usage:
    from pdf_rotator import rotate_pdf

    # Rotate all pages 90 degrees clockwise
    rotate_pdf("input.pdf", "output.pdf", angle=90)

    # Rotate only pages 1 and 3 by 180 degrees
    rotate_pdf("input.pdf", "output.pdf", angle=180, pages=[1, 3])

CLI usage:
    # Rotate all pages
    python pdf_rotator.py input.pdf output.pdf 90

    # Rotate specific pages
    python pdf_rotator.py input.pdf output.pdf 180 --pages 1 3 5
"""

import argparse
import sys
import traceback
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from tqdm import tqdm


def rotate_pdf(
    input_path: str,
    output_path: str,
    angle: int,
    pages: list[int] | None = None,
    show_progress: bool = False,
) -> int:
    """Rotate pages in a PDF.

    Args:
        input_path:  Path to the source PDF.
        output_path: Path to write the rotated PDF.
        angle:       Clockwise rotation in degrees. Must be 90, 180, or 270.
        pages:       1-based page numbers to rotate. None rotates all pages.
        show_progress: Show a tqdm progress bar while processing.

    Returns:
        Number of pages that were rotated.

    Raises:
        FileNotFoundError: If input_path does not exist.
        ValueError: If angle is invalid or any page number is out of range.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if angle % 90 != 0 or angle % 360 == 0:
        raise ValueError(f"Angle must be 90, 180, or 270, got {angle}.")

    reader = PdfReader(input_path)
    total_pages = len(reader.pages)

    if pages is not None:
        invalid = [p for p in pages if p < 1 or p > total_pages]
        if invalid:
            raise ValueError(
                f"Page numbers out of range (document has {total_pages} pages): {invalid}"
            )
        pages_set = set(pages)
    else:
        pages_set = None

    writer = PdfWriter()
    rotated = 0

    page_iter = (
        tqdm(
            enumerate(reader.pages, 1), desc="Rotating", unit="page", total=total_pages
        )
        if show_progress
        else enumerate(reader.pages, 1)
    )

    for page_num, page in page_iter:
        if pages_set is None or page_num in pages_set:
            page.rotate(angle)
            rotated += 1
        writer.add_page(page)

    with open(output_path, "wb") as f:
        writer.write(f)

    return rotated


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="Rotate pages in a PDF.",
        usage=(
            "%(prog)s input.pdf output.pdf ANGLE\n"
            "       %(prog)s input.pdf output.pdf ANGLE --pages 1 3 5"
        ),
    )
    parser.add_argument("input", help="Source PDF file.")
    parser.add_argument("output", help="Path for the rotated output PDF.")
    parser.add_argument(
        "angle",
        type=int,
        choices=[90, 180, 270],
        help="Clockwise rotation in degrees: 90, 180, or 270.",
    )
    parser.add_argument(
        "--pages",
        nargs="+",
        type=int,
        metavar="N",
        help="1-based page numbers to rotate. Omit to rotate all pages.",
    )
    args = parser.parse_args()

    try:
        rotated = rotate_pdf(
            args.input,
            args.output,
            args.angle,
            pages=args.pages,
            show_progress=True,
        )
        print(
            f"Rotated {rotated} page(s) by {args.angle}°. Written to '{args.output}'."
        )
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
