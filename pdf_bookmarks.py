"""PDF bookmarks - list, add, or remove bookmarks (table of contents).

Bookmarks are also known as the document outline or table of contents.
Levels are 1-based: 1 = top-level chapter, 2 = sub-section, etc.
Page numbers are 1-based throughout.

Library usage:
    from pdf_bookmarks import list_bookmarks, add_bookmarks, remove_bookmarks

    # List all bookmarks
    for bm in list_bookmarks("input.pdf"):
        indent = "  " * (bm["level"] - 1)
        print(f"{indent}{bm['title']} — page {bm['page']}")

    # Add bookmarks (appends to any existing ones)
    added = add_bookmarks(
        "input.pdf", "output.pdf",
        bookmarks=[
            {"level": 1, "title": "Introduction", "page": 1},
            {"level": 1, "title": "Chapter 1",    "page": 3},
            {"level": 2, "title": "Section 1.1",  "page": 4},
        ],
    )

    # Remove all bookmarks
    removed = remove_bookmarks("input.pdf", "output.pdf")

CLI usage:
    # List bookmarks
    python pdf_bookmarks.py list input.pdf

    # Add bookmarks  (format: LEVEL:TITLE:PAGE)
    python pdf_bookmarks.py add input.pdf output.pdf "1:Introduction:1" "2:Overview:2"

    # Remove all bookmarks
    python pdf_bookmarks.py remove input.pdf output.pdf
"""

import argparse
import sys
import traceback
from pathlib import Path

import fitz  # PyMuPDF


def list_bookmarks(pdf_path: str) -> list[dict]:
    """Return all bookmarks in a PDF.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        A list of dicts with keys:
            - level (int): Nesting level, 1 = top-level.
            - title (str): Bookmark label.
            - page  (int): 1-based destination page number.

    Raises:
        FileNotFoundError: If pdf_path does not exist.
    """
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    toc = doc.get_toc(simple=True)
    doc.close()

    return [{"level": lvl, "title": title, "page": page}
            for lvl, title, page in toc]


def add_bookmarks(
    input_path: str,
    output_path: str,
    bookmarks: list[dict],
) -> int:
    """Add bookmarks to a PDF, preserving any existing ones.

    Args:
        input_path:  Path to the source PDF.
        output_path: Path to write the updated PDF.
        bookmarks:   List of bookmark dicts, each with:
                         - level (int): Nesting level >= 1.
                         - title (str): Non-empty label text.
                         - page  (int): 1-based destination page number.

    Returns:
        Number of bookmarks added.

    Raises:
        FileNotFoundError: If input_path does not exist.
        ValueError: If bookmarks is empty, any page is out of range,
                    any level is < 1, or any title is empty.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"File not found: {input_path}")
    if not bookmarks:
        raise ValueError("Provide at least one bookmark.")

    doc = fitz.open(input_path)
    total_pages = doc.page_count

    for bm in bookmarks:
        if bm["level"] < 1:
            raise ValueError(
                f"Bookmark level must be >= 1, got {bm['level']} for '{bm['title']}'."
            )
        if not bm["title"].strip():
            raise ValueError("Bookmark title must not be empty.")
        if bm["page"] < 1 or bm["page"] > total_pages:
            raise ValueError(
                f"Page {bm['page']} is out of range "
                f"(document has {total_pages} page(s))."
            )

    toc = doc.get_toc(simple=True)
    for bm in bookmarks:
        toc.append([bm["level"], bm["title"], bm["page"]])

    doc.set_toc(toc)
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

    return len(bookmarks)


def remove_bookmarks(input_path: str, output_path: str) -> int:
    """Remove all bookmarks from a PDF.

    Args:
        input_path:  Path to the source PDF.
        output_path: Path to write the updated PDF.

    Returns:
        Number of bookmarks that were removed.

    Raises:
        FileNotFoundError: If input_path does not exist.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    doc = fitz.open(input_path)
    count = len(doc.get_toc(simple=True))
    doc.set_toc([])
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()

    return count


def _parse_bookmark(value: str) -> dict:
    """Parse 'LEVEL:TITLE:PAGE' into a bookmark dict."""
    parts = value.split(":")
    if len(parts) < 3:
        raise argparse.ArgumentTypeError(
            f"Invalid bookmark '{value}'. "
            "Expected format: LEVEL:TITLE:PAGE  (e.g. 1:Introduction:1)"
        )
    try:
        level = int(parts[0])
        page  = int(parts[-1])
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid bookmark '{value}': LEVEL and PAGE must be integers."
        )
    title = ":".join(parts[1:-1])
    return {"level": level, "title": title, "page": page}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List, add, or remove PDF bookmarks.",
        usage=(
            "%(prog)s list   input.pdf\n"
            "       %(prog)s add    input.pdf output.pdf \"LEVEL:TITLE:PAGE\" ...\n"
            "       %(prog)s remove input.pdf output.pdf"
        ),
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    # list
    p_list = sub.add_parser("list", help="Print all bookmarks.")
    p_list.add_argument("input", help="Source PDF file.")

    # add
    p_add = sub.add_parser("add", help="Add bookmarks to a PDF.")
    p_add.add_argument("input",  help="Source PDF file.")
    p_add.add_argument("output", help="Path for the updated PDF.")
    p_add.add_argument(
        "bookmarks",
        nargs="+",
        metavar="LEVEL:TITLE:PAGE",
        type=_parse_bookmark,
        help="Bookmark to add. LEVEL >= 1, PAGE is 1-based. "
             "Example: \"1:Chapter 1:3\"",
    )

    # remove
    p_remove = sub.add_parser("remove", help="Remove all bookmarks from a PDF.")
    p_remove.add_argument("input",  help="Source PDF file.")
    p_remove.add_argument("output", help="Path for the updated PDF.")

    args = parser.parse_args()

    try:
        if args.command == "list":
            bookmarks = list_bookmarks(args.input)
            if not bookmarks:
                print("No bookmarks found.")
            else:
                for bm in bookmarks:
                    indent = "  " * (bm["level"] - 1)
                    print(f"{indent}{bm['title']}  (page {bm['page']})")

        elif args.command == "add":
            count = add_bookmarks(args.input, args.output, args.bookmarks)
            print(f"Added {count} bookmark(s). Written to '{args.output}'.")

        elif args.command == "remove":
            count = remove_bookmarks(args.input, args.output)
            print(f"Removed {count} bookmark(s). Written to '{args.output}'.")

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
