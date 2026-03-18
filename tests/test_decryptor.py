import pytest
from pathlib import Path
from pypdf import PdfReader
from pdf_decryptor import decrypt_pdf


def test_decrypts_successfully(encrypted_pdf, out):
    decrypt_pdf(encrypted_pdf, out, password="testpass")
    assert Path(out).exists()


def test_output_is_not_encrypted(encrypted_pdf, out):
    decrypt_pdf(encrypted_pdf, out, password="testpass")
    reader = PdfReader(out)
    assert not reader.is_encrypted


def test_wrong_password_raises(encrypted_pdf, out):
    with pytest.raises(ValueError, match="Incorrect password"):
        decrypt_pdf(encrypted_pdf, out, password="wrongpass")


def test_unencrypted_input_raises(simple_pdf, out):
    with pytest.raises(ValueError, match="not password-protected"):
        decrypt_pdf(simple_pdf, out, password="any")


def test_missing_input_raises(out):
    with pytest.raises(FileNotFoundError):
        decrypt_pdf("nonexistent.pdf", out, password="x")
