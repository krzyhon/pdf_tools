import pytest
from pathlib import Path
from pypdf import PdfReader
from pdf_merger import merge_pdfs


def test_merges_two_files(simple_pdf, multipage_pdf, out):
    pages = merge_pdfs(out, [simple_pdf, multipage_pdf])
    assert pages == 5  # 1 + 4


def test_output_file_created(simple_pdf, multipage_pdf, out):
    merge_pdfs(out, [simple_pdf, multipage_pdf])
    assert Path(out).exists()


def test_page_count_correct(simple_pdf, multipage_pdf, out):
    merge_pdfs(out, [simple_pdf, multipage_pdf])
    reader = PdfReader(out)
    assert len(reader.pages) == 5


def test_three_files(simple_pdf, multipage_pdf, out, tmp_path):
    extra = str(tmp_path / "extra.pdf")
    import fitz

    doc = fitz.open()
    doc.new_page()
    doc.save(extra)
    doc.close()
    pages = merge_pdfs(out, [simple_pdf, multipage_pdf, extra])
    assert pages == 6


def test_fewer_than_two_inputs_raises(simple_pdf, out):
    with pytest.raises(ValueError, match="At least 2"):
        merge_pdfs(out, [simple_pdf])


def test_missing_input_raises(simple_pdf, out):
    with pytest.raises(FileNotFoundError):
        merge_pdfs(out, [simple_pdf, "nonexistent.pdf"])
