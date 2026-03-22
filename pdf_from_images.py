"""PDF from images — create a PDF from image files.

Library usage:
    from pdf_from_images import images_to_pdf

    images_to_pdf(["page1.png", "page2.jpg"], "output.pdf")

CLI usage:
    python pdf_from_images.py output.pdf image1.png image2.jpg image3.png
"""

import argparse
import sys
from pathlib import Path

import fitz  # PyMuPDF
from tqdm import tqdm

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".gif", ".webp"}


def images_to_pdf(
    image_paths: list[str],
    output_path: str,
    show_progress: bool = False,
) -> int:
    """Create a PDF from a list of image files.

    Each image becomes one page. The page size matches the image dimensions.

    Args:
        image_paths:   Ordered list of image file paths (PNG, JPEG, BMP, TIFF, etc.).
        output_path:   Path to write the output PDF.
        show_progress: Show a tqdm progress bar while processing.

    Returns:
        Number of pages in the output PDF.

    Raises:
        ValueError: If no image paths provided or an extension is unsupported.
        FileNotFoundError: If any image file does not exist.
    """
    if not image_paths:
        raise ValueError("At least one image file is required.")

    for path in image_paths:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Image file not found: {path}")
        if p.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported image format '{p.suffix}' for file: {path}. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )

    doc = fitz.open()
    iterable = tqdm(image_paths, desc="Building PDF", unit="image") if show_progress else image_paths

    for path in iterable:
        img_doc = fitz.open(path)
        pdf_bytes = img_doc.convert_to_pdf()
        img_doc.close()
        img_pdf = fitz.open("pdf", pdf_bytes)
        doc.insert_pdf(img_pdf)
        img_pdf.close()

    doc.save(output_path, garbage=4, deflate=True)
    pages = len(doc)
    doc.close()
    return pages


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a PDF from image files (PNG, JPEG, BMP, TIFF, etc.).",
        usage="%(prog)s output.pdf image1.png image2.jpg [image3.png ...]",
    )
    parser.add_argument("output", help="Path for the output PDF.")
    parser.add_argument("images", nargs="+", metavar="image",
                        help="Image files to include, in order.")
    args = parser.parse_args()

    try:
        pages = images_to_pdf(args.images, args.output, show_progress=True)
        print(f"Created '{args.output}' with {pages} page(s) from {len(args.images)} image(s).")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
