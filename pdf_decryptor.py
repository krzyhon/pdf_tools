"""PDF decryptor — remove password protection from a PDF.

Requires the correct password to unlock the document. The output PDF
has no password and can be opened freely.

Library usage:
    from pdf_decryptor import decrypt_pdf

    decrypt_pdf("locked.pdf", "unlocked.pdf", password="secret")

CLI usage:
    python pdf_decryptor.py locked.pdf unlocked.pdf --password secret

    # Omit --password to be prompted securely:
    python pdf_decryptor.py locked.pdf unlocked.pdf
"""

import argparse
import getpass
import sys
import traceback
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def decrypt_pdf(input_path: str, output_path: str, password: str) -> None:
    """Remove password protection from a PDF.

    Args:
        input_path:  Path to the encrypted source PDF.
        output_path: Path to write the decrypted PDF.
        password:    Password used to encrypt the document.

    Raises:
        FileNotFoundError: If input_path does not exist.
        ValueError: If the document is not encrypted, or the password is wrong.
    """
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    reader = PdfReader(input_path)

    if not reader.is_encrypted:
        raise ValueError(f"'{input_path}' is not password-protected.")

    result = reader.decrypt(password)
    if result == 0:
        raise ValueError("Incorrect password.")

    writer = PdfWriter()
    writer.append(reader)

    with open(output_path, "wb") as f:
        writer.write(f)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove password protection from a PDF.",
        usage="%(prog)s input.pdf output.pdf [--password PASSWORD]",
    )
    parser.add_argument("input",  help="Encrypted source PDF file.")
    parser.add_argument("output", help="Path for the decrypted output PDF.")
    parser.add_argument(
        "--password",
        help="Password to unlock the PDF. Prompted securely if omitted.",
    )
    args = parser.parse_args()

    password = args.password or getpass.getpass("Enter password: ")

    try:
        decrypt_pdf(args.input, args.output, password)
        print(f"Decrypted PDF written to '{args.output}'.")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
