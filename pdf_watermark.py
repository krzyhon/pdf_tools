"""PDF watermark — stamp text onto every page of a PDF.

Library usage:
    from pdf_watermark import watermark_pdf

    # Default: diagonal "CONFIDENTIAL" in gray across every page
    watermark_pdf("input.pdf", "output.pdf", text="CONFIDENTIAL")

    # Custom appearance
    watermark_pdf("input.pdf", "output.pdf", text="DRAFT",
                  fontsize=80, opacity=0.15, angle=30, color=(1, 0, 0))

CLI usage:
    python pdf_watermark.py input.pdf output.pdf "DRAFT"
    python pdf_watermark.py input.pdf output.pdf "CONFIDENTIAL" --opacity 0.1 --angle 45 --fontsize 72
"""

import argparse
import sys
import traceback
from pathlib import Path

import fitz  # PyMuPDF
from tqdm import tqdm


def watermark_pdf(
    input_path: str,
    output_path: str,
    text: str,
    fontsize: float = 60.0,
    opacity: float = 0.15,
    angle: float = 45.0,
    color: tuple[float, float, float] = (0.5, 0.5, 0.5),
    show_progress: bool = False,
) -> None:
    """Stamp a text watermark onto every page of a PDF.

    Args:
        input_path:  Path to the source PDF.
        output_path: Path to write the watermarked PDF.
        text:        Watermark text (e.g. "DRAFT", "CONFIDENTIAL").
        fontsize:    Font size in points (default 60).
        opacity:     Opacity from 0.0 (invisible) to 1.0 (opaque). Default 0.15.
        angle:       Rotation angle in degrees, counter-clockwise. Default 45.
        color:       RGB colour as floats in [0, 1]. Default gray (0.5, 0.5, 0.5).
        show_progress: Show a tqdm progress bar while processing.

    Raises:
        FileNotFoundError: If input_path does not exist.
        ValueError: If opacity is not in [0, 1] or text is empty.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if not text.strip():
        raise ValueError("Watermark text must not be empty.")
    if not 0.0 <= opacity <= 1.0:
        raise ValueError(f"Opacity must be between 0.0 and 1.0, got {opacity}.")

    doc = fitz.open(input_path)
    font = fitz.Font("helv")
    pages = tqdm(doc, desc="Watermarking", unit="page") if show_progress else doc

    for page in pages:
        cx = page.rect.width / 2
        cy = page.rect.height / 2

        # Measure text so we can centre it before rotating
        text_width = font.text_length(text, fontsize=fontsize)

        tw = fitz.TextWriter(page.rect)
        # Place baseline-left so the text centre lands on the page centre
        tw.append(
            fitz.Point(cx - text_width / 2, cy + fontsize * 0.3),
            text,
            font=font,
            fontsize=fontsize,
        )
        tw.write_text(
            page,
            color=color,
            opacity=opacity,
            morph=(fitz.Point(cx, cy), fitz.Matrix(angle)),
        )

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="Stamp a text watermark onto every page of a PDF.",
        usage="%(prog)s input.pdf output.pdf TEXT [options]",
    )
    parser.add_argument("input", help="Source PDF file.")
    parser.add_argument("output", help="Path for the watermarked output PDF.")
    parser.add_argument("text", help='Watermark text, e.g. "DRAFT".')
    parser.add_argument(
        "--fontsize",
        type=float,
        default=60.0,
        metavar="PT",
        help="Font size in points (default: 60).",
    )
    parser.add_argument(
        "--opacity",
        type=float,
        default=0.15,
        metavar="N",
        help="Opacity 0.0–1.0 (default: 0.15).",
    )
    parser.add_argument(
        "--angle",
        type=float,
        default=45.0,
        metavar="DEG",
        help="Rotation in degrees, counter-clockwise (default: 45).",
    )
    parser.add_argument(
        "--color",
        nargs=3,
        type=float,
        default=[0.5, 0.5, 0.5],
        metavar=("R", "G", "B"),
        help="RGB colour, each value 0.0–1.0 (default: 0.5 0.5 0.5 = gray).",
    )
    args = parser.parse_args()

    try:
        watermark_pdf(
            args.input,
            args.output,
            args.text,
            fontsize=args.fontsize,
            opacity=args.opacity,
            angle=args.angle,
            color=tuple(args.color),
            show_progress=True,
        )
        print(f"Watermarked PDF written to '{args.output}'.")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
