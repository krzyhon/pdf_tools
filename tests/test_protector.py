import pytest
from pathlib import Path
from pypdf import PdfReader
from pdf_protector import protect_pdf


def test_output_file_created(simple_pdf, out):
    protect_pdf(simple_pdf, out, password="secret")
    assert Path(out).exists()


def test_output_is_encrypted(simple_pdf, out):
    protect_pdf(simple_pdf, out, password="secret")
    reader = PdfReader(out)
    assert reader.is_encrypted


def test_correct_password_opens(simple_pdf, out):
    protect_pdf(simple_pdf, out, password="secret")
    reader = PdfReader(out)
    result = reader.decrypt("secret")
    assert result != 0  # 0 means failure


def test_wrong_password_fails(simple_pdf, out):
    protect_pdf(simple_pdf, out, password="secret")
    reader = PdfReader(out)
    result = reader.decrypt("wrong")
    assert result == 0


def test_empty_password_raises(simple_pdf, out):
    with pytest.raises(ValueError, match="empty"):
        protect_pdf(simple_pdf, out, password="")


def test_missing_input_raises(out):
    with pytest.raises(FileNotFoundError):
        protect_pdf("nonexistent.pdf", out, password="x")
