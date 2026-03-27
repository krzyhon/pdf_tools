import pytest
from pathlib import Path
import fitz
from pdf_page_numbers import add_page_numbers


def _text(pdf_path: str, page: int) -> str:
    """Extract text from a 1-based page of a PDF."""
    doc = fitz.open(pdf_path)
    t = doc[page - 1].get_text()
    doc.close()
    return t


# --- basic functionality ---

def test_creates_output(multipage_pdf, out):
    add_page_numbers(multipage_pdf, out)
    assert Path(out).exists()
    assert Path(out).stat().st_size > 0


def test_returns_count_all_pages(multipage_pdf, out):
    count = add_page_numbers(multipage_pdf, out)
    assert count == 4


def test_stamps_number_on_each_page(multipage_pdf, out):
    add_page_numbers(multipage_pdf, out)
    for page_num in range(1, 5):
        assert str(page_num) in _text(out, page_num)


def test_default_format_is_number_only(simple_pdf, out):
    add_page_numbers(simple_pdf, out)
    assert "1" in _text(out, 1)


# --- format string ---

def test_format_page_n_of_N(multipage_pdf, out):
    add_page_numbers(multipage_pdf, out, fmt="Page {n} of {N}")
    assert "Page 1 of 4" in _text(out, 1)
    assert "Page 4 of 4" in _text(out, 4)


def test_format_n_slash_N(multipage_pdf, out):
    add_page_numbers(multipage_pdf, out, fmt="{n}/{N}")
    assert "1/4" in _text(out, 1)


def test_invalid_format_raises(simple_pdf, out):
    with pytest.raises(ValueError, match="format"):
        add_page_numbers(simple_pdf, out, fmt="{x}")


# --- start number ---

def test_start_offset(multipage_pdf, out):
    add_page_numbers(multipage_pdf, out, start=10)
    assert "10" in _text(out, 1)
    assert "13" in _text(out, 4)


def test_start_one_raises(simple_pdf, out):
    with pytest.raises(ValueError, match="Start"):
        add_page_numbers(simple_pdf, out, start=0)


# --- position ---

@pytest.mark.parametrize("position", [
    "bottom-left", "bottom-center", "bottom-right",
    "top-left",    "top-center",    "top-right",
])
def test_all_positions_work(simple_pdf, out, position):
    count = add_page_numbers(simple_pdf, out, position=position)
    assert count == 1
    assert Path(out).exists()


def test_invalid_position_raises(simple_pdf, out):
    with pytest.raises(ValueError, match="position"):
        add_page_numbers(simple_pdf, out, position="middle-center")


# --- pages subset ---

def test_specific_pages_only(multipage_pdf, out):
    count = add_page_numbers(multipage_pdf, out, pages=[1, 3])
    assert count == 2


def test_specific_pages_stamped_correctly(multipage_pdf, out):
    add_page_numbers(multipage_pdf, out, pages=[2, 4])
    assert "1" in _text(out, 2)
    assert "2" in _text(out, 4)


def test_invalid_page_raises(multipage_pdf, out):
    with pytest.raises(ValueError, match="out of range"):
        add_page_numbers(multipage_pdf, out, pages=[99])


def test_page_zero_raises(multipage_pdf, out):
    with pytest.raises(ValueError, match="out of range"):
        add_page_numbers(multipage_pdf, out, pages=[0])


# --- other validation ---

def test_invalid_fontsize_raises(simple_pdf, out):
    with pytest.raises(ValueError, match="Font size"):
        add_page_numbers(simple_pdf, out, fontsize=0)


def test_negative_margin_raises(simple_pdf, out):
    with pytest.raises(ValueError, match="Margin"):
        add_page_numbers(simple_pdf, out, margin=-1)


def test_missing_file_raises(out):
    with pytest.raises(FileNotFoundError):
        add_page_numbers("nonexistent.pdf", out)
