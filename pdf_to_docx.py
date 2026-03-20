"""PDF to DOCX converter — convert a PDF file to a Word document.

Conversion is best-effort: PDF is a fixed-layout format while DOCX is
flow-based, so complex layouts (multi-column, overlapping elements) may
not be reproduced exactly. Text, images, and simple tables are handled well.

Library usage:
    from pdf_to_docx import convert_pdf_to_docx

    convert_pdf_to_docx("input.pdf", "output.docx")

    # Convert only pages 2 to 4
    convert_pdf_to_docx("input.pdf", "output.docx", start_page=2, end_page=4)

CLI usage:
    python pdf_to_docx.py input.pdf output.docx
    python pdf_to_docx.py input.pdf output.docx --start 2 --end 4
"""

import argparse
import sys
from pathlib import Path

from pdf2docx import Converter


def convert_pdf_to_docx(
    input_path: str,
    output_path: str,
    start_page: int = 1,
    end_page: int | None = None,
) -> None:
    """Convert a PDF file to a DOCX Word document.

    Args:
        input_path:  Path to the source PDF.
        output_path: Path to write the output .docx file.
        start_page:  First page to convert (1-based, default: 1).
        end_page:    Last page to convert (1-based, inclusive, default: last page).

    Raises:
        FileNotFoundError: If input_path does not exist.
        ValueError: If start_page or end_page are out of range, or start > end.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if Path(output_path).suffix.lower() != ".docx":
        output_path = output_path + ".docx"

    if start_page < 1:
        raise ValueError(f"start_page must be >= 1, got {start_page}.")

    if end_page is not None:
        if end_page < 1:
            raise ValueError(f"end_page must be >= 1, got {end_page}.")
        if start_page > end_page:
            raise ValueError(
                f"start_page ({start_page}) must be <= end_page ({end_page})."
            )

    cv = Converter(input_path)
    try:
        # pdf2docx uses 0-based page indices
        start = start_page - 1
        end = end_page  # None means convert to the last page
        cv.convert(output_path, start=start, end=end)
    finally:
        cv.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a PDF file to a Word document (.docx).",
        usage=(
            "%(prog)s input.pdf output.docx\n"
            "       %(prog)s input.pdf output.docx --start 2 --end 4"
        ),
    )
    parser.add_argument("input",  help="Source PDF file.")
    parser.add_argument("output", help="Path for the output .docx file.")
    parser.add_argument(
        "--start", type=int, default=1, metavar="N",
        help="First page to convert (1-based, default: 1).",
    )
    parser.add_argument(
        "--end", type=int, default=None, metavar="N",
        help="Last page to convert (1-based, inclusive, default: last page).",
    )
    args = parser.parse_args()

    try:
        convert_pdf_to_docx(args.input, args.output, start_page=args.start, end_page=args.end)
        print(f"Converted '{args.input}' to '{args.output}'.")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
