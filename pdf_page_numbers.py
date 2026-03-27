"""PDF page numbers — stamp page numbers onto PDF pages.

The format string supports two placeholders:
    {n}  current page number (affected by --start)
    {N}  total number of pages in the document

Library usage:
    from pdf_page_numbers import add_page_numbers

    # Default: "1", "2", … centred at the bottom
    add_page_numbers("input.pdf", "output.pdf")

    # "Page 1 of 10" at the bottom-right, starting from page 5
    add_page_numbers("input.pdf", "output.pdf",
                     fmt="Page {n} of {N}",
                     position="bottom-right",
                     start=5)

    # Stamp only the first three pages
    add_page_numbers("input.pdf", "output.pdf", pages=[1, 2, 3])

CLI usage:
    python pdf_page_numbers.py input.pdf output.pdf
    python pdf_page_numbers.py input.pdf output.pdf --position bottom-right
    python pdf_page_numbers.py input.pdf output.pdf --format "Page {n} of {N}"
    python pdf_page_numbers.py input.pdf output.pdf --start 5 --fontsize 12
    python pdf_page_numbers.py input.pdf output.pdf --pages 1 2 3
"""

import argparse
import sys
import traceback
from pathlib import Path

import fitz  # PyMuPDF
from tqdm import tqdm


_VALID_POSITIONS = frozenset({
    "bottom-left", "bottom-center", "bottom-right",
    "top-left",    "top-center",    "top-right",
})

_FONT_NAME = "helv"


def add_page_numbers(
    input_path: str,
    output_path: str,
    position: str = "bottom-center",
    fmt: str = "{n}",
    start: int = 1,
    fontsize: float = 10.0,
    margin: float = 36.0,
    color: tuple[float, float, float] = (0.4, 0.4, 0.4),
    pages: list[int] | None = None,
    show_progress: bool = False,
) -> int:
    """Stamp page numbers onto PDF pages.

    Args:
        input_path:  Path to the source PDF.
        output_path: Path to write the numbered PDF.
        position:    Where to place the number. One of:
                     "bottom-left", "bottom-center", "bottom-right",
                     "top-left", "top-center", "top-right".
                     Default: "bottom-center".
        fmt:         Format string. Use {n} for the page number and {N}
                     for the total page count. Default: "{n}".
        start:       Number assigned to the first page (or first page in
                     the pages list). Default: 1.
        fontsize:    Font size in points. Default: 10.
        margin:      Distance in points from the nearest page edge.
                     Default: 36 (0.5 inch).
        color:       RGB colour as floats in [0, 1]. Default: dark gray.
        pages:       1-based page numbers to stamp. None stamps all pages.
        show_progress: Show a tqdm progress bar while processing.

    Returns:
        Number of pages stamped.

    Raises:
        FileNotFoundError: If input_path does not exist.
        ValueError: If position is invalid, start < 1, fontsize <= 0,
                    margin < 0, fmt is invalid, or any page is out of range.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if position not in _VALID_POSITIONS:
        raise ValueError(
            f"Invalid position '{position}'. "
            f"Choose from: {', '.join(sorted(_VALID_POSITIONS))}."
        )
    if start < 1:
        raise ValueError(f"Start number must be >= 1, got {start}.")
    if fontsize <= 0:
        raise ValueError(f"Font size must be positive, got {fontsize}.")
    if margin < 0:
        raise ValueError(f"Margin must be >= 0, got {margin}.")

    # Validate format string early with dummy values
    try:
        fmt.format(n=1, N=1)
    except (KeyError, ValueError) as e:
        raise ValueError(
            f"Invalid format string '{fmt}': {e}. "
            "Use {{n}} for page number and {{N}} for total pages."
        ) from e

    doc = fitz.open(input_path)
    total_pages = doc.page_count

    if pages is not None:
        invalid = [p for p in pages if p < 1 or p > total_pages]
        if invalid:
            raise ValueError(
                f"Page(s) out of range (document has {total_pages} page(s)): {invalid}"
            )
        target_pages = [(p - 1, start + i) for i, p in enumerate(pages)]
    else:
        target_pages = [(i, start + i) for i in range(total_pages)]

    font = fitz.Font(_FONT_NAME)
    v_edge, h_align = position.split("-")

    page_iter = target_pages
    if show_progress:
        page_iter = tqdm(target_pages, desc="Numbering", unit="page")

    for page_idx, page_num in page_iter:
        page = doc[page_idx]
        label = fmt.format(n=page_num, N=total_pages)
        text_width = font.text_length(label, fontsize=fontsize)

        # Horizontal position
        if h_align == "left":
            x = margin
        elif h_align == "center":
            x = (page.rect.width - text_width) / 2
        else:  # right
            x = page.rect.width - margin - text_width

        # Vertical position (insert_text uses baseline)
        if v_edge == "bottom":
            y = page.rect.height - margin
        else:  # top
            y = margin + fontsize

        tw = fitz.TextWriter(page.rect)
        tw.append(fitz.Point(x, y), label, font=font, fontsize=fontsize)
        tw.write_text(page, color=color)

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

    return len(target_pages)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stamp page numbers onto PDF pages.",
        usage=(
            "%(prog)s input.pdf output.pdf [options]\n\n"
            "Format placeholders: {n} = page number, {N} = total pages"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input",  help="Source PDF file.")
    parser.add_argument("output", help="Path for the numbered output PDF.")
    parser.add_argument(
        "--position", "-p",
        default="bottom-center",
        choices=sorted(_VALID_POSITIONS),
        metavar="POS",
        help=(
            "Where to place the number. "
            "Choices: bottom-left, bottom-center, bottom-right, "
            "top-left, top-center, top-right. Default: bottom-center."
        ),
    )
    parser.add_argument(
        "--format", "-f",
        dest="fmt",
        default="{n}",
        metavar="STRING",
        help='Format string. Use {n} for page number, {N} for total. Default: "{n}".',
    )
    parser.add_argument(
        "--start", "-s",
        type=int, default=1,
        metavar="N",
        help="Number to assign to the first stamped page. Default: 1.",
    )
    parser.add_argument(
        "--fontsize",
        type=float, default=10.0,
        metavar="PT",
        help="Font size in points. Default: 10.",
    )
    parser.add_argument(
        "--margin",
        type=float, default=36.0,
        metavar="PT",
        help="Distance from the page edge in points (default: 36 = 0.5 inch).",
    )
    parser.add_argument(
        "--pages",
        nargs="+", type=int,
        metavar="N",
        help="1-based page numbers to stamp. Omit to stamp all pages.",
    )
    args = parser.parse_args()

    try:
        count = add_page_numbers(
            args.input, args.output,
            position=args.position,
            fmt=args.fmt,
            start=args.start,
            fontsize=args.fontsize,
            margin=args.margin,
            pages=args.pages,
            show_progress=True,
        )
        print(f"Stamped {count} page(s). Written to '{args.output}'.")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
