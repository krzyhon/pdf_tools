"""PDF OCR — convert a scanned PDF or image into a searchable PDF.

Each page is rendered to an image, passed through Tesseract OCR, and written
back as a PDF with a transparent text layer on top of the original image.
The result looks identical to the input but is fully searchable and
copy-pasteable.

Requires Tesseract to be installed on the system:
    macOS:          brew install tesseract
    Ubuntu/Debian:  sudo apt install tesseract-ocr
    Windows:        winget install UB-Mannheim.TesseractOCR

Additional language packs (default is English):
    macOS:          brew install tesseract-lang
    Ubuntu/Debian:  sudo apt install tesseract-ocr-<lang>  (e.g. tesseract-ocr-pol)

Library usage:
    from pdf_ocr import ocr_to_pdf

    # Scanned PDF → searchable PDF
    pages = ocr_to_pdf("scan.pdf", "searchable.pdf")

    # Image → searchable PDF
    pages = ocr_to_pdf("scan.png", "searchable.pdf")

    # Non-English document
    pages = ocr_to_pdf("scan.pdf", "searchable.pdf", language="pol")

CLI usage:
    python pdf_ocr.py scan.pdf searchable.pdf
    python pdf_ocr.py scan.png searchable.pdf
    python pdf_ocr.py scan.pdf searchable.pdf --lang pol
    python pdf_ocr.py scan.pdf searchable.pdf --dpi 200
"""

import argparse
import sys
import traceback
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageSequence
from tqdm import tqdm


_PDF_EXTENSIONS = frozenset({".pdf"})
_IMAGE_EXTENSIONS = frozenset(
    {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}
)
_ALL_EXTENSIONS = _PDF_EXTENSIONS | _IMAGE_EXTENSIONS


def ocr_to_pdf(
    input_path: str,
    output_path: str,
    language: str = "eng",
    dpi: int = 300,
    show_progress: bool = False,
) -> int:
    """Run OCR on a scanned PDF or image and produce a searchable PDF.

    Args:
        input_path:  Path to the source file (PDF or image).
        output_path: Path to write the searchable PDF.
        language:    Tesseract language code (default: "eng").
                     Use "pol" for Polish, "deu" for German, etc.
                     Multiple languages: "eng+pol".
        dpi:         Resolution for rendering PDF pages before OCR (default: 300).
                     Higher DPI improves accuracy but increases processing time.
        show_progress: Show a tqdm progress bar while processing.

    Returns:
        Number of pages written to the output PDF.

    Raises:
        FileNotFoundError: If input_path does not exist.
        ValueError: If the file format is not supported or dpi is not positive.
        RuntimeError: If Tesseract is not installed or the language pack is missing.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    suffix = Path(input_path).suffix.lower()
    if suffix not in _ALL_EXTENSIONS:
        raise ValueError(
            f"Unsupported format '{suffix}'. "
            f"Supported: {', '.join(sorted(_ALL_EXTENSIONS))}."
        )
    if not 1 <= dpi <= 600:
        raise ValueError(f"DPI must be between 1 and 600, got {dpi}.")

    # Collect PIL images to OCR
    images: list[Image.Image] = []

    if suffix in _PDF_EXTENSIONS:
        doc = fitz.open(input_path)
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pages_iter = (
            doc if not show_progress else tqdm(doc, desc="Rendering", unit="page")
        )
        for page in pages_iter:
            pix = page.get_pixmap(matrix=mat)
            images.append(Image.frombytes("RGB", (pix.width, pix.height), pix.samples))
        doc.close()
    else:
        img = Image.open(input_path)
        # Handle both single-frame and multi-frame images (e.g. multi-page TIFFs)
        for frame in ImageSequence.Iterator(img):
            images.append(frame.copy().convert("RGB"))

    # Run OCR on each image and combine into a single output PDF
    try:
        out_doc = fitz.open()
        ocr_iter = (
            images
            if not show_progress
            else tqdm(
                images,
                desc="OCR",
                unit="page",
                initial=0,
            )
        )
        for ocr_img in ocr_iter:
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(
                ocr_img, extension="pdf", lang=language
            )
            page_doc = fitz.open("pdf", pdf_bytes)
            out_doc.insert_pdf(page_doc)
            page_doc.close()

        out_doc.save(output_path, garbage=4, deflate=True)
        out_doc.close()

    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract is not installed or not on PATH. "
            "Install it with: brew install tesseract  (macOS) or "
            "sudo apt install tesseract-ocr  (Ubuntu/Debian)."
        )
    except pytesseract.TesseractError as e:
        raise RuntimeError(
            f"Tesseract error: {e}. "
            f"If this is a language error, install the pack for '{language}'."
        )

    return len(images)


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="Convert a scanned PDF or image to a searchable PDF using OCR.",
        usage="%(prog)s input output [--lang CODE] [--dpi N]",
    )
    parser.add_argument(
        "input", help="Source file: scanned PDF or image (PNG, JPG, TIFF, …)."
    )
    parser.add_argument("output", help="Path for the searchable output PDF.")
    parser.add_argument(
        "--lang",
        "-l",
        default="eng",
        metavar="CODE",
        help=(
            'Tesseract language code (default: "eng"). '
            'Examples: pol, deu, fra. Combine with "+": "eng+pol".'
        ),
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        metavar="N",
        help="Render resolution for PDF pages (default: 300). Higher = better quality, slower.",
    )
    args = parser.parse_args()

    try:
        count = ocr_to_pdf(
            args.input,
            args.output,
            language=args.lang,
            dpi=args.dpi,
            show_progress=True,
        )
        print(f"OCR complete: {count} page(s) written to '{args.output}'.")
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
