import pytest
from pathlib import Path
import fitz
from pdf_diff import diff_report, diff_visual


@pytest.fixture
def pdf_a(tmp_path):
    """Original 2-page PDF."""
    path = tmp_path / "a.pdf"
    doc = fitz.open()
    for text in ("Page 1 original text", "Page 2 content"):
        p = doc.new_page(width=595, height=842)
        p.insert_text((50, 100), text, fontsize=14)
    doc.save(str(path))
    doc.close()
    return str(path)


@pytest.fixture
def pdf_b_changed(tmp_path):
    """2-page PDF with page 1 text changed."""
    path = tmp_path / "b_changed.pdf"
    doc = fitz.open()
    for text in ("Page 1 modified text", "Page 2 content"):
        p = doc.new_page(width=595, height=842)
        p.insert_text((50, 100), text, fontsize=14)
    doc.save(str(path))
    doc.close()
    return str(path)


@pytest.fixture
def pdf_b_identical(tmp_path):
    """Identical copy of pdf_a."""
    path = tmp_path / "b_identical.pdf"
    doc = fitz.open()
    for text in ("Page 1 original text", "Page 2 content"):
        p = doc.new_page(width=595, height=842)
        p.insert_text((50, 100), text, fontsize=14)
    doc.save(str(path))
    doc.close()
    return str(path)


@pytest.fixture
def pdf_b_extra_page(tmp_path):
    """3-page PDF — one page appended."""
    path = tmp_path / "b_extra.pdf"
    doc = fitz.open()
    for text in ("Page 1 original text", "Page 2 content", "Page 3 new"):
        p = doc.new_page(width=595, height=842)
        p.insert_text((50, 100), text, fontsize=14)
    doc.save(str(path))
    doc.close()
    return str(path)


@pytest.fixture
def pdf_b_fewer_pages(tmp_path):
    """1-page PDF — one page removed."""
    path = tmp_path / "b_fewer.pdf"
    doc = fitz.open()
    p = doc.new_page(width=595, height=842)
    p.insert_text((50, 100), "Page 1 original text", fontsize=14)
    doc.save(str(path))
    doc.close()
    return str(path)


# --- diff_report ---

def test_report_no_differences(pdf_a, pdf_b_identical):
    report = diff_report(pdf_a, pdf_b_identical)
    assert report["changed_pages"] == []
    assert report["added_pages"] == []
    assert report["removed_pages"] == []


def test_report_detects_changed_page(pdf_a, pdf_b_changed):
    report = diff_report(pdf_a, pdf_b_changed)
    assert len(report["changed_pages"]) == 1
    assert report["changed_pages"][0]["page"] == 1
    assert "original" in report["changed_pages"][0]["diff"]
    assert "modified" in report["changed_pages"][0]["diff"]


def test_report_detects_added_page(pdf_a, pdf_b_extra_page):
    report = diff_report(pdf_a, pdf_b_extra_page)
    assert report["added_pages"] == [3]
    assert report["removed_pages"] == []


def test_report_detects_removed_page(pdf_a, pdf_b_fewer_pages):
    report = diff_report(pdf_a, pdf_b_fewer_pages)
    assert report["removed_pages"] == [2]
    assert report["added_pages"] == []


def test_report_page_counts(pdf_a, pdf_b_extra_page):
    report = diff_report(pdf_a, pdf_b_extra_page)
    assert report["pages_a"] == 2
    assert report["pages_b"] == 3


def test_report_missing_a_raises(pdf_a):
    with pytest.raises(FileNotFoundError):
        diff_report("nonexistent.pdf", pdf_a)


def test_report_missing_b_raises(pdf_a):
    with pytest.raises(FileNotFoundError):
        diff_report(pdf_a, "nonexistent.pdf")


# --- diff_visual ---

def test_visual_creates_output(pdf_a, pdf_b_changed, out):
    diff_visual(pdf_a, pdf_b_changed, out)
    assert Path(out).exists()
    assert Path(out).stat().st_size > 0


def test_visual_identical_no_changed_pages(pdf_a, pdf_b_identical, out):
    report = diff_visual(pdf_a, pdf_b_identical, out)
    assert report["changed_pages"] == []
    assert Path(out).exists()


def test_visual_changed_page_in_report(pdf_a, pdf_b_changed, out):
    report = diff_visual(pdf_a, pdf_b_changed, out)
    assert len(report["changed_pages"]) >= 1
    assert report["changed_pages"][0]["page"] == 1


def test_visual_added_page_output_has_correct_count(pdf_a, pdf_b_extra_page, out):
    report = diff_visual(pdf_a, pdf_b_extra_page, out)
    assert report["added_pages"] == [3]
    doc = fitz.open(out)
    assert doc.page_count == 3
    doc.close()


def test_visual_removed_page_output_has_placeholder(pdf_a, pdf_b_fewer_pages, out):
    report = diff_visual(pdf_a, pdf_b_fewer_pages, out)
    assert report["removed_pages"] == [2]
    doc = fitz.open(out)
    # 1 page from B + 1 placeholder for removed page
    assert doc.page_count == 2
    doc.close()


def test_visual_invalid_dpi_raises(pdf_a, pdf_b_changed, out):
    with pytest.raises(ValueError, match="DPI"):
        diff_visual(pdf_a, pdf_b_changed, out, dpi=0)


def test_visual_dpi_too_high_raises(pdf_a, pdf_b_changed, out):
    with pytest.raises(ValueError, match="DPI"):
        diff_visual(pdf_a, pdf_b_changed, out, dpi=601)


def test_visual_missing_file_raises(pdf_a, out):
    with pytest.raises(FileNotFoundError):
        diff_visual("nonexistent.pdf", pdf_a, out)
