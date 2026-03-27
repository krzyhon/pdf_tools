"""PDF protector — encrypt a PDF with a password.

Library usage:
    from pdf_protector import protect_pdf
    protect_pdf("input.pdf", "output.pdf", password="secret")

CLI usage:
    python pdf_protector.py input.pdf output.pdf --password mypassword

    # Omit --password to be prompted securely (recommended):
    python pdf_protector.py input.pdf output.pdf
"""

import argparse
import getpass
import sys
import traceback
from pathlib import Path

from pypdf import PdfWriter


def protect_pdf(input_path: str, output_path: str, password: str) -> None:
    """Encrypt a PDF with AES-256 password protection.

    Args:
        input_path: Path to the source PDF.
        output_path: Path to write the encrypted PDF.
        password: Password required to open the document.

    Raises:
        FileNotFoundError: If input_path does not exist.
        ValueError: If password is empty.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not password:
        raise ValueError("Password must not be empty.")

    writer = PdfWriter()
    try:
        writer.append(input_path)
        writer.encrypt(user_password=password, algorithm="AES-256")
        writer.write(output_path)
    finally:
        writer.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Encrypt a PDF with a password (AES-256).",
        usage="%(prog)s input.pdf output.pdf [--password PASSWORD]",
    )
    parser.add_argument("input", help="Source PDF file.")
    parser.add_argument("output", help="Path for the encrypted output PDF.")
    parser.add_argument(
        "--password",
        help="Password to protect the PDF. Prompted securely if omitted.",
    )
    args = parser.parse_args()

    password = args.password
    if not password:
        password = getpass.getpass("Enter password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Error: Passwords do not match.", file=sys.stderr)
            sys.exit(1)

    try:
        protect_pdf(args.input, args.output, password)
        print(f"Protected PDF written to '{args.output}'.")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
