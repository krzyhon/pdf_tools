import pytest
from pathlib import Path
from pdf_splitter import split_pdf_pages, split_pdf_ranges


def test_split_pages_creates_files(multipage_pdf, tmp_path):
    out_dir = str(tmp_path / "pages")
    paths = split_pdf_pages(multipage_pdf, out_dir)
    assert len(paths) == 4


def test_split_pages_files_exist(multipage_pdf, tmp_path):
    out_dir = str(tmp_path / "pages")
    paths = split_pdf_pages(multipage_pdf, out_dir)
    for p in paths:
        assert Path(p).exists()


def test_split_pages_naming(multipage_pdf, tmp_path):
    out_dir = str(tmp_path / "pages")
    paths = split_pdf_pages(multipage_pdf, out_dir)
    names = [Path(p).name for p in paths]
    assert "page_001.pdf" in names
    assert "page_004.pdf" in names


def test_split_ranges_creates_files(multipage_pdf, tmp_path):
    out_dir = str(tmp_path / "ranges")
    paths = split_pdf_ranges(multipage_pdf, out_dir, [(1, 2), (3, 4)])
    assert len(paths) == 2


def test_split_ranges_files_exist(multipage_pdf, tmp_path):
    out_dir = str(tmp_path / "ranges")
    paths = split_pdf_ranges(multipage_pdf, out_dir, [(1, 2), (3, 4)])
    for p in paths:
        assert Path(p).exists()


def test_split_ranges_default_naming(multipage_pdf, tmp_path):
    out_dir = str(tmp_path / "ranges")
    paths = split_pdf_ranges(multipage_pdf, out_dir, [(1, 2), (3, 4)])
    names = [Path(p).name for p in paths]
    assert "part_01.pdf" in names
    assert "part_02.pdf" in names


def test_split_ranges_custom_names(multipage_pdf, tmp_path):
    out_dir = str(tmp_path / "ranges")
    paths = split_pdf_ranges(multipage_pdf, out_dir, [(1, 2), (3, 4)], names=["first", "second"])
    names = [Path(p).name for p in paths]
    assert "first.pdf" in names
    assert "second.pdf" in names


def test_split_ranges_empty_raises(multipage_pdf, tmp_path):
    with pytest.raises(ValueError, match="At least one range"):
        split_pdf_ranges(multipage_pdf, str(tmp_path), [])


def test_split_ranges_out_of_bounds_raises(multipage_pdf, tmp_path):
    with pytest.raises(ValueError, match="exceeds document"):
        split_pdf_ranges(multipage_pdf, str(tmp_path), [(1, 99)])


def test_split_ranges_inverted_range_raises(multipage_pdf, tmp_path):
    with pytest.raises(ValueError, match="start must be <= end"):
        split_pdf_ranges(multipage_pdf, str(tmp_path), [(3, 1)])


def test_split_pages_missing_input_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        split_pdf_pages("nonexistent.pdf", str(tmp_path))


def test_split_ranges_missing_input_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        split_pdf_ranges("nonexistent.pdf", str(tmp_path), [(1, 1)])
