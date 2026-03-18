"""Shared fixtures for pdf_tools tests."""

import pytest
import fitz  # PyMuPDF


@pytest.fixture
def simple_pdf(tmp_path):
    """Single-page PDF with some text."""
    path = tmp_path / "simple.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 100), "Hello World", fontsize=14)
    page.insert_text((50, 130), "Secret phrase", fontsize=12)
    doc.save(str(path))
    doc.close()
    return str(path)


@pytest.fixture
def multipage_pdf(tmp_path):
    """Four-page PDF, each page labelled."""
    path = tmp_path / "multipage.pdf"
    doc = fitz.open()
    for i in range(1, 5):
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 100), f"Page {i} content", fontsize=14)
    doc.save(str(path))
    doc.close()
    return str(path)


@pytest.fixture
def encrypted_pdf(tmp_path, simple_pdf):
    """Password-protected PDF (password: 'testpass')."""
    from pdf_protector import protect_pdf
    out = str(tmp_path / "encrypted.pdf")
    protect_pdf(simple_pdf, out, password="testpass")
    return out


@pytest.fixture
def out(tmp_path):
    """Convenience: a path string for a single output file."""
    return str(tmp_path / "output.pdf")
