import pytest
from pathlib import Path

from pdf_to_images import pdf_to_images


def test_all_pages_exported_as_png(multipage_pdf, tmp_path):
    out_dir = str(tmp_path / "images")
    paths = pdf_to_images(multipage_pdf, out_dir)
    assert len(paths) == 4
    for p in paths:
        assert Path(p).exists()
        assert p.endswith(".png")


def test_single_page_pdf(simple_pdf, tmp_path):
    out_dir = str(tmp_path / "images")
    paths = pdf_to_images(simple_pdf, out_dir)
    assert len(paths) == 1
    assert Path(paths[0]).exists()


def test_jpeg_format(simple_pdf, tmp_path):
    out_dir = str(tmp_path / "images")
    paths = pdf_to_images(simple_pdf, out_dir, fmt="jpeg")
    assert len(paths) == 1
    assert paths[0].endswith(".jpg")
    assert Path(paths[0]).exists()


def test_specific_pages(multipage_pdf, tmp_path):
    out_dir = str(tmp_path / "images")
    paths = pdf_to_images(multipage_pdf, out_dir, pages=[1, 3])
    assert len(paths) == 2


def test_output_dir_created_if_missing(simple_pdf, tmp_path):
    out_dir = str(tmp_path / "new" / "nested" / "dir")
    paths = pdf_to_images(simple_pdf, out_dir)
    assert Path(out_dir).exists()
    assert len(paths) == 1


def test_custom_dpi(simple_pdf, tmp_path):
    out_dir = str(tmp_path / "images")
    paths = pdf_to_images(simple_pdf, out_dir, dpi=72)
    assert len(paths) == 1
    assert Path(paths[0]).exists()


def test_nonexistent_input_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        pdf_to_images("nonexistent.pdf", str(tmp_path))


def test_invalid_format_raises(simple_pdf, tmp_path):
    with pytest.raises(ValueError, match="Unsupported format"):
        pdf_to_images(simple_pdf, str(tmp_path), fmt="bmp")


def test_page_out_of_range_raises(simple_pdf, tmp_path):
    with pytest.raises(ValueError, match="out of range"):
        pdf_to_images(simple_pdf, str(tmp_path), pages=[999])


def test_returned_paths_are_strings(multipage_pdf, tmp_path):
    paths = pdf_to_images(multipage_pdf, str(tmp_path / "images"))
    assert all(isinstance(p, str) for p in paths)
