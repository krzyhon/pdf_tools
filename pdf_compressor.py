"""PDF compressor — reduce PDF file size.

Applies lossless compression: removes unused objects, deduplicates resources,
and re-compresses all data streams with deflate. Optionally downsamples
embedded images for more aggressive size reduction.

Library usage:
    from pdf_compressor import compress_pdf

    # Lossless compression only
    saved = compress_pdf("input.pdf", "output.pdf")

    # Also downsample images to 150 DPI (lossy)
    saved = compress_pdf("input.pdf", "output.pdf", image_dpi=150)

CLI usage:
    python pdf_compressor.py input.pdf output.pdf
    python pdf_compressor.py input.pdf output.pdf --image-dpi 150
"""

import argparse
import sys
import traceback
from pathlib import Path

import fitz  # PyMuPDF


def compress_pdf(
    input_path: str,
    output_path: str,
    image_dpi: int | None = None,
) -> tuple[int, int]:
    """Compress a PDF to reduce its file size.

    Lossless steps applied always:
    - Remove unused/duplicate objects (garbage collection level 4)
    - Re-compress all streams with deflate
    - Clean up content streams

    Lossy step (opt-in):
    - Downsample embedded images to the given DPI

    Args:
        input_path:  Path to the source PDF.
        output_path: Path to write the compressed PDF.
        image_dpi:   If set, downsample images to this DPI (e.g. 150).
                     None applies lossless compression only.

    Returns:
        Tuple of (original_bytes, compressed_bytes).

    Raises:
        FileNotFoundError: If input_path does not exist.
        ValueError: If image_dpi is given but not a positive integer.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if image_dpi is not None and image_dpi < 1:
        raise ValueError(f"image_dpi must be a positive integer, got {image_dpi}.")

    original_size = Path(input_path).stat().st_size

    doc = fitz.open(input_path)

    if image_dpi is not None:
        _downsample_images(doc, image_dpi)

    doc.save(
        output_path,
        garbage=4,  # remove unused objects + deduplicate
        deflate=True,  # compress all streams
        clean=True,  # clean up content streams
    )
    doc.close()

    compressed_size = Path(output_path).stat().st_size
    return original_size, compressed_size


def _downsample_images(doc: fitz.Document, target_dpi: int) -> None:
    """Replace high-resolution images in a document with downsampled versions."""
    for page in doc:
        for img in page.get_images(full=True):
            xref = img[0]
            base_image = doc.extract_image(xref)
            if not base_image:
                continue

            w, h = base_image["width"], base_image["height"]
            # Estimate current DPI from the image's placement on the page
            # Use the image rect for a rough DPI estimate
            img_rects = page.get_image_rects(xref)
            if not img_rects:
                continue
            rect = img_rects[0]
            render_w_pt = abs(rect.x1 - rect.x0)
            render_h_pt = abs(rect.y1 - rect.y0)
            if render_w_pt == 0 or render_h_pt == 0:
                continue
            current_dpi_x = w / render_w_pt * 72
            current_dpi_y = h / render_h_pt * 72
            current_dpi = max(current_dpi_x, current_dpi_y)

            if current_dpi <= target_dpi:
                continue  # already at or below target, skip

            scale = target_dpi / current_dpi
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))

            # Re-render the image at target DPI via a pixmap
            pix = fitz.Pixmap(doc, xref)
            if pix.n > 4:  # CMYK or other — convert to RGB first
                pix = fitz.Pixmap(fitz.csRGB, pix)
            pix = pix.scale(new_w, new_h)
            doc.update_stream(xref, pix.tobytes("png"))


def _fmt_size(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f} MB"
    if n >= 1_000:
        return f"{n / 1_000:.1f} KB"
    return f"{n} B"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reduce PDF file size via lossless compression and optional image downsampling.",
        usage=(
            "%(prog)s input.pdf output.pdf\n"
            "       %(prog)s input.pdf output.pdf --image-dpi 150"
        ),
    )
    parser.add_argument("input", help="Source PDF file.")
    parser.add_argument("output", help="Path for the compressed output PDF.")
    parser.add_argument(
        "--image-dpi",
        type=int,
        default=None,
        metavar="DPI",
        help="Downsample embedded images to this DPI (e.g. 150). "
        "Omit for lossless-only compression.",
    )
    args = parser.parse_args()

    try:
        original, compressed = compress_pdf(
            args.input, args.output, image_dpi=args.image_dpi
        )
        saved = original - compressed
        pct = (saved / original * 100) if original else 0
        mode = "lossless" + (
            f" + images downsampled to {args.image_dpi} DPI" if args.image_dpi else ""
        )
        print(
            f"{_fmt_size(original)} → {_fmt_size(compressed)} "
            f"(saved {_fmt_size(saved)}, {pct:.1f}%)  [{mode}]\n"
            f"Written to '{args.output}'."
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
