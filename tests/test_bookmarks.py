import pytest
from pathlib import Path
import fitz
from pdf_bookmarks import list_bookmarks, add_bookmarks, remove_bookmarks


@pytest.fixture
def pdf_no_bookmarks(tmp_path):
    """3-page PDF with no bookmarks."""
    path = tmp_path / "no_bm.pdf"
    doc = fitz.open()
    for i in range(1, 4):
        p = doc.new_page(width=595, height=842)
        p.insert_text((50, 100), f"Page {i}", fontsize=14)
    doc.save(str(path))
    doc.close()
    return str(path)


@pytest.fixture
def pdf_with_bookmarks(tmp_path):
    """3-page PDF with two top-level and one nested bookmark."""
    path = tmp_path / "with_bm.pdf"
    doc = fitz.open()
    for i in range(1, 4):
        p = doc.new_page(width=595, height=842)
        p.insert_text((50, 100), f"Page {i}", fontsize=14)
    doc.set_toc([
        [1, "Chapter 1", 1],
        [2, "Section 1.1", 2],
        [1, "Chapter 2", 3],
    ])
    doc.save(str(path))
    doc.close()
    return str(path)


# --- list_bookmarks ---

def test_list_empty(pdf_no_bookmarks):
    assert list_bookmarks(pdf_no_bookmarks) == []


def test_list_returns_all(pdf_with_bookmarks):
    bms = list_bookmarks(pdf_with_bookmarks)
    assert len(bms) == 3


def test_list_structure(pdf_with_bookmarks):
    bms = list_bookmarks(pdf_with_bookmarks)
    assert bms[0] == {"level": 1, "title": "Chapter 1",   "page": 1}
    assert bms[1] == {"level": 2, "title": "Section 1.1", "page": 2}
    assert bms[2] == {"level": 1, "title": "Chapter 2",   "page": 3}


def test_list_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        list_bookmarks("nonexistent.pdf")


# --- add_bookmarks ---

def test_add_creates_output(pdf_no_bookmarks, out):
    add_bookmarks(pdf_no_bookmarks, out, [{"level": 1, "title": "Intro", "page": 1}])
    assert Path(out).exists()


def test_add_bookmarks_appear(pdf_no_bookmarks, out):
    bookmarks = [
        {"level": 1, "title": "Chapter 1", "page": 1},
        {"level": 2, "title": "Section",   "page": 2},
    ]
    count = add_bookmarks(pdf_no_bookmarks, out, bookmarks)
    assert count == 2
    result = list_bookmarks(out)
    assert len(result) == 2
    assert result[0]["title"] == "Chapter 1"
    assert result[1]["level"] == 2


def test_add_preserves_existing(pdf_with_bookmarks, out):
    add_bookmarks(pdf_with_bookmarks, out, [{"level": 1, "title": "Appendix", "page": 3}])
    result = list_bookmarks(out)
    assert len(result) == 4  # 3 existing + 1 new
    assert result[-1]["title"] == "Appendix"


def test_add_returns_count(pdf_no_bookmarks, out):
    bookmarks = [{"level": 1, "title": f"Ch {i}", "page": i} for i in range(1, 4)]
    assert add_bookmarks(pdf_no_bookmarks, out, bookmarks) == 3


def test_add_empty_list_raises(pdf_no_bookmarks, out):
    with pytest.raises(ValueError, match="at least one"):
        add_bookmarks(pdf_no_bookmarks, out, [])


def test_add_invalid_page_raises(pdf_no_bookmarks, out):
    with pytest.raises(ValueError, match="out of range"):
        add_bookmarks(pdf_no_bookmarks, out, [{"level": 1, "title": "X", "page": 99}])


def test_add_page_zero_raises(pdf_no_bookmarks, out):
    with pytest.raises(ValueError, match="out of range"):
        add_bookmarks(pdf_no_bookmarks, out, [{"level": 1, "title": "X", "page": 0}])


def test_add_invalid_level_raises(pdf_no_bookmarks, out):
    with pytest.raises(ValueError, match="level"):
        add_bookmarks(pdf_no_bookmarks, out, [{"level": 0, "title": "X", "page": 1}])


def test_add_empty_title_raises(pdf_no_bookmarks, out):
    with pytest.raises(ValueError, match="title"):
        add_bookmarks(pdf_no_bookmarks, out, [{"level": 1, "title": "   ", "page": 1}])


def test_add_missing_file_raises(out):
    with pytest.raises(FileNotFoundError):
        add_bookmarks("nonexistent.pdf", out, [{"level": 1, "title": "X", "page": 1}])


# --- remove_bookmarks ---

def test_remove_creates_output(pdf_with_bookmarks, out):
    remove_bookmarks(pdf_with_bookmarks, out)
    assert Path(out).exists()


def test_remove_clears_all(pdf_with_bookmarks, out):
    remove_bookmarks(pdf_with_bookmarks, out)
    assert list_bookmarks(out) == []


def test_remove_returns_count(pdf_with_bookmarks, out):
    assert remove_bookmarks(pdf_with_bookmarks, out) == 3


def test_remove_on_empty_returns_zero(pdf_no_bookmarks, out):
    assert remove_bookmarks(pdf_no_bookmarks, out) == 0


def test_remove_missing_file_raises(out):
    with pytest.raises(FileNotFoundError):
        remove_bookmarks("nonexistent.pdf", out)
