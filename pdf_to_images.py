"""PDF to images — render PDF pages as image files.

Library usage:
    from pdf_to_images import pdf_to_images

    # Export all pages as PNG at 150 DPI
    paths = pdf_to_images("input.pdf", "output_dir/")

    # Export pages 2–4 as JPEG at 200 DPI
    paths = pdf_to_images("input.pdf", "output_dir/", fmt="jpeg", dpi=200, pages=[2, 3, 4])

CLI usage:
    # All pages → output_dir/page_001.png, page_002.png, ...
    python pdf_to_images.py input.pdf output_dir/

    # JPEG at 200 DPI, pages 1 and 3 only
    python pdf_to_images.py input.pdf output_dir/ --format jpeg --dpi 200 --pages 1 3
"""

import argparse
import sys
from pathlib import Path

import fitz  # PyMuPDF
from tqdm import tqdm


def pdf_to_images(
    input_path: str,
    output_dir: str,
    fmt: str = "png",
    dpi: int = 150,
    pages: list[int] | None = None,
    show_progress: bool = False,
) -> list[str]:
    """Render PDF pages as image files.

    Args:
        input_path:    Path to the source PDF.
        output_dir:    Directory where image files will be written (created if needed).
        fmt:           Output format: "png" or "jpeg".
        dpi:           Resolution in dots per inch (default 150).
        pages:         1-based page numbers to export. None exports all pages.
        show_progress: Show a tqdm progress bar while processing.

    Returns:
        List of output file paths (strings), one per exported page.

    Raises:
        FileNotFoundError: If input_path does not exist.
        ValueError: If fmt is invalid or any page number is out of range.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    fmt = fmt.lower()
    if fmt not in ("png", "jpeg", "jpg"):
        raise ValueError(f"Unsupported format '{fmt}'. Use 'png' or 'jpeg'.")
    ext = "jpg" if fmt in ("jpeg", "jpg") else "png"

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(input_path)
    total_pages = len(doc)

    if pages is not None:
        invalid = [p for p in pages if p < 1 or p > total_pages]
        if invalid:
            raise ValueError(
                f"Page numbers out of range (document has {total_pages} pages): {invalid}"
            )
        page_indices = [p - 1 for p in pages]
    else:
        page_indices = list(range(total_pages))

    zoom = dpi / 72  # PDF native resolution is 72 DPI
    mat = fitz.Matrix(zoom, zoom)

    output_paths = []
    iterable = tqdm(page_indices, desc="Rendering", unit="page") if show_progress else page_indices

    for idx in iterable:
        page = doc[idx]
        pix = page.get_pixmap(matrix=mat)
        filename = out_dir / f"page_{idx + 1:03d}.{ext}"
        pix.save(str(filename))
        output_paths.append(str(filename))

    doc.close()
    return output_paths


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Render PDF pages as PNG or JPEG image files.",
        usage=(
            "%(prog)s input.pdf output_dir/\n"
            "       %(prog)s input.pdf output_dir/ --format jpeg --dpi 200 --pages 1 3"
        ),
    )
    parser.add_argument("input", help="Source PDF file.")
    parser.add_argument("output_dir", help="Directory for output images (created if needed).")
    parser.add_argument("--format", dest="fmt", default="png", choices=["png", "jpeg"],
                        help="Image format (default: png).")
    parser.add_argument("--dpi", type=int, default=150,
                        help="Resolution in DPI (default: 150).")
    parser.add_argument("--pages", nargs="+", type=int, metavar="N",
                        help="1-based page numbers to export. Omit to export all pages.")
    args = parser.parse_args()

    try:
        paths = pdf_to_images(
            args.input, args.output_dir,
            fmt=args.fmt, dpi=args.dpi, pages=args.pages,
            show_progress=True,
        )
        print(f"Exported {len(paths)} page(s) to '{args.output_dir}'.")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
