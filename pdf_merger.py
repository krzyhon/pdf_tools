"""PDF merger — merge multiple PDF files into one.

Library usage:
    from pdf_merger import merge_pdfs
    merge_pdfs("output.pdf", ["file1.pdf", "file2.pdf"])

CLI usage:
    python pdf_merger.py output.pdf file1.pdf file2.pdf [...]
"""

import argparse
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from tqdm import tqdm


def merge_pdfs(output_path: str, input_paths: list[str], show_progress: bool = False) -> int:
    """Merge multiple PDF files into a single output file.

    Args:
        output_path: Path to write the merged PDF.
        input_paths: Ordered list of PDF paths to merge.
        show_progress: Show a tqdm progress bar while processing.

    Returns:
        Total number of pages in the merged document.

    Raises:
        ValueError: If fewer than 2 input files are provided.
        FileNotFoundError: If any input file does not exist.
    """
    if len(input_paths) < 2:
        raise ValueError(f"At least 2 input files required, got {len(input_paths)}.")

    for path in input_paths:
        if not Path(path).exists():
            raise FileNotFoundError(f"Input file not found: {path}")

    writer = PdfWriter()
    try:
        files = tqdm(input_paths, desc="Merging", unit="file") if show_progress else input_paths
        for path in files:
            writer.append(path)
        writer.write(output_path)
    finally:
        writer.close()

    return len(PdfReader(output_path).pages)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge multiple PDF files into one.",
        usage="%(prog)s output.pdf file1.pdf file2.pdf [file3.pdf ...]",
    )
    parser.add_argument("output", help="Path for the merged output PDF.")
    parser.add_argument("inputs", nargs="+", metavar="input", help="PDF files to merge (in order).")
    args = parser.parse_args()

    if len(args.inputs) < 2:
        parser.error("Provide at least 2 input PDF files.")

    try:
        pages = merge_pdfs(args.output, args.inputs, show_progress=True)
        print(f"Merged {len(args.inputs)} files into '{args.output}' ({pages} pages).")
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
