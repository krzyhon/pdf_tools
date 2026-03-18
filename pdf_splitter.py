"""PDF splitter — split a PDF into multiple files.

Library usage:
    from pdf_splitter import split_pdf_pages, split_pdf_ranges

    # One file per page
    paths = split_pdf_pages("input.pdf", "output_dir/")

    # One file per page range (1-based, inclusive)
    paths = split_pdf_ranges("input.pdf", "output_dir/", [(1, 3), (4, 6)])

CLI usage:
    # Split every page
    python pdf_splitter.py input.pdf output_dir/

    # Split by ranges
    python pdf_splitter.py input.pdf output_dir/ --ranges 1-3 4-6
"""

import argparse
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from tqdm import tqdm


def split_pdf_pages(input_path: str, output_dir: str, show_progress: bool = False) -> list[str]:
    """Split every page of a PDF into a separate file.

    Args:
        input_path: Path to the source PDF.
        output_dir: Directory where output files are written.
                    Created automatically if it does not exist.
        show_progress: Show a tqdm progress bar while processing.

    Returns:
        List of created file paths, ordered by page number.

    Raises:
        FileNotFoundError: If input_path does not exist.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    reader = PdfReader(input_path)
    created = []
    pages = tqdm(reader.pages, desc="Splitting", unit="page") if show_progress else reader.pages
    for i, page in enumerate(pages):
        out_path = out_dir / f"page_{i + 1:03d}.pdf"
        writer = PdfWriter()
        writer.add_page(page)
        writer.write(str(out_path))
        writer.close()
        created.append(str(out_path))

    return created


def split_pdf_ranges(
    input_path: str,
    output_dir: str,
    ranges: list[tuple[int, int]],
    names: list[str] | None = None,
    show_progress: bool = False,
) -> list[str]:
    """Split a PDF into one file per page range.

    Args:
        input_path: Path to the source PDF.
        output_dir: Directory where output files are written.
                    Created automatically if it does not exist.
        ranges: List of (start, end) tuples using 1-based, inclusive page numbers.
                Example: [(1, 3), (4, 6)] extracts pages 1-3 and 4-6.
        names: Optional list of output filenames (without .pdf extension),
               one per range. Defaults to part_01, part_02, ...
        show_progress: Show a tqdm progress bar while processing.

    Returns:
        List of created file paths.

    Raises:
        FileNotFoundError: If input_path does not exist.
        ValueError: If ranges is empty, any range is invalid, or names length
                    does not match ranges length.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not ranges:
        raise ValueError("At least one range is required.")

    if names is not None and len(names) != len(ranges):
        raise ValueError(
            f"'names' length ({len(names)}) must match 'ranges' length ({len(ranges)})."
        )

    reader = PdfReader(input_path)
    total_pages = len(reader.pages)

    for start, end in ranges:
        if start < 1 or end < 1:
            raise ValueError(f"Page numbers must be >= 1, got range ({start}, {end}).")
        if start > end:
            raise ValueError(f"Range start must be <= end, got ({start}, {end}).")
        if end > total_pages:
            raise ValueError(
                f"Range ({start}, {end}) exceeds document length ({total_pages} pages)."
            )

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    created = []
    items = tqdm(enumerate(ranges), desc="Splitting", unit="range", total=len(ranges)) if show_progress else enumerate(ranges)
    for idx, (start, end) in items:
        name = names[idx] if names else f"part_{idx + 1:02d}"
        out_path = out_dir / f"{name}.pdf"
        writer = PdfWriter()
        writer.append(reader, pages=range(start - 1, end))  # convert to 0-based
        writer.write(str(out_path))
        writer.close()
        created.append(str(out_path))

    return created


def _parse_range(value: str) -> tuple[int, int]:
    """Parse a range string like '1-3' into a (1, 3) tuple."""
    parts = value.split("-")
    if len(parts) != 2:
        raise argparse.ArgumentTypeError(
            f"Invalid range '{value}'. Expected format: START-END (e.g. 1-3)."
        )
    try:
        start, end = int(parts[0]), int(parts[1])
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid range '{value}'. START and END must be integers."
        )
    return (start, end)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split a PDF into multiple files.",
        usage=(
            "%(prog)s input.pdf output_dir/\n"
            "       %(prog)s input.pdf output_dir/ --ranges 1-3 4-6"
        ),
    )
    parser.add_argument("input", help="Source PDF file.")
    parser.add_argument("output_dir", help="Directory for output files.")
    parser.add_argument(
        "--ranges",
        nargs="+",
        metavar="START-END",
        type=_parse_range,
        help="Page ranges to extract (1-based, inclusive). Example: 1-3 4-6",
    )
    args = parser.parse_args()

    try:
        if args.ranges:
            paths = split_pdf_ranges(args.input, args.output_dir, args.ranges, show_progress=True)
        else:
            paths = split_pdf_pages(args.input, args.output_dir, show_progress=True)

        for path in paths:
            print(path)
        print(f"\nCreated {len(paths)} file(s) in '{args.output_dir}'.")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
