import pytest
from pathlib import Path
from pdf_to_docx import convert_pdf_to_docx


def test_output_file_created(simple_pdf, tmp_path):
    out = str(tmp_path / "output.docx")
    convert_pdf_to_docx(simple_pdf, out)
    assert Path(out).exists()


def test_extension_added_when_missing(simple_pdf, tmp_path):
    out = str(tmp_path / "output")
    convert_pdf_to_docx(simple_pdf, out)
    assert Path(out + ".docx").exists()


def test_extension_not_doubled_when_provided(simple_pdf, tmp_path):
    out = str(tmp_path / "output.docx")
    convert_pdf_to_docx(simple_pdf, out)
    assert not Path(out + ".docx").exists()
    assert Path(out).exists()


def test_output_is_valid_docx(simple_pdf, tmp_path):
    out = str(tmp_path / "output.docx")
    convert_pdf_to_docx(simple_pdf, out)
    # DOCX files are ZIP archives — check the magic bytes
    with open(out, "rb") as f:
        assert f.read(2) == b"PK"


def test_multipage_conversion(multipage_pdf, tmp_path):
    out = str(tmp_path / "output.docx")
    convert_pdf_to_docx(multipage_pdf, out)
    assert Path(out).exists()


def test_page_range(multipage_pdf, tmp_path):
    out = str(tmp_path / "output.docx")
    convert_pdf_to_docx(multipage_pdf, out, start_page=2, end_page=3)
    assert Path(out).exists()


def test_single_page(multipage_pdf, tmp_path):
    out = str(tmp_path / "output.docx")
    convert_pdf_to_docx(multipage_pdf, out, start_page=2, end_page=2)
    assert Path(out).exists()


def test_missing_input_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        convert_pdf_to_docx("nonexistent.pdf", str(tmp_path / "out.docx"))


def test_invalid_start_page_raises(simple_pdf, tmp_path):
    with pytest.raises(ValueError, match="start_page"):
        convert_pdf_to_docx(simple_pdf, str(tmp_path / "out.docx"), start_page=0)


def test_invalid_end_page_raises(simple_pdf, tmp_path):
    with pytest.raises(ValueError, match="end_page"):
        convert_pdf_to_docx(simple_pdf, str(tmp_path / "out.docx"), end_page=0)


def test_start_greater_than_end_raises(multipage_pdf, tmp_path):
    with pytest.raises(ValueError, match="must be <="):
        convert_pdf_to_docx(multipage_pdf, str(tmp_path / "out.docx"), start_page=3, end_page=1)
