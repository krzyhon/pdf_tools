import pytest
from pathlib import Path
from pypdf import PdfReader
from pdf_reorder import reorder_pdf


def test_output_file_created(multipage_pdf, out):
    reorder_pdf(multipage_pdf, out, [4, 3, 2, 1])
    assert Path(out).exists()


def test_reversed_page_count(multipage_pdf, out):
    count = reorder_pdf(multipage_pdf, out, [4, 3, 2, 1])
    assert count == 4


def test_output_has_correct_page_count(multipage_pdf, out):
    reorder_pdf(multipage_pdf, out, [4, 3, 2, 1])
    reader = PdfReader(out)
    assert len(reader.pages) == 4


def test_extract_subset(multipage_pdf, out):
    count = reorder_pdf(multipage_pdf, out, [2, 4])
    assert count == 2
    reader = PdfReader(out)
    assert len(reader.pages) == 2


def test_duplicate_pages(multipage_pdf, out):
    count = reorder_pdf(multipage_pdf, out, [1, 1, 2])
    assert count == 3
    reader = PdfReader(out)
    assert len(reader.pages) == 3


def test_empty_order_raises(multipage_pdf, out):
    with pytest.raises(ValueError, match="empty"):
        reorder_pdf(multipage_pdf, out, [])


def test_out_of_range_page_raises(multipage_pdf, out):
    with pytest.raises(ValueError, match="out of range"):
        reorder_pdf(multipage_pdf, out, [1, 99])


def test_missing_input_raises(out):
    with pytest.raises(FileNotFoundError):
        reorder_pdf("nonexistent.pdf", out, [1])
