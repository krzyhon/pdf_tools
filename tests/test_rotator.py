import pytest
from pathlib import Path
from pdf_rotator import rotate_pdf


def test_output_file_created(multipage_pdf, out):
    rotate_pdf(multipage_pdf, out, angle=90)
    assert Path(out).exists()


def test_rotate_all_pages(multipage_pdf, out):
    rotated = rotate_pdf(multipage_pdf, out, angle=90)
    assert rotated == 4


def test_rotate_specific_pages(multipage_pdf, out):
    rotated = rotate_pdf(multipage_pdf, out, angle=180, pages=[1, 3])
    assert rotated == 2


def test_rotate_180(multipage_pdf, out):
    rotated = rotate_pdf(multipage_pdf, out, angle=180)
    assert rotated == 4


def test_rotate_270(multipage_pdf, out):
    rotated = rotate_pdf(multipage_pdf, out, angle=270)
    assert rotated == 4


def test_invalid_angle_raises(multipage_pdf, out):
    with pytest.raises(ValueError, match="Angle must be"):
        rotate_pdf(multipage_pdf, out, angle=45)


def test_zero_angle_raises(multipage_pdf, out):
    with pytest.raises(ValueError):
        rotate_pdf(multipage_pdf, out, angle=0)


def test_360_angle_raises(multipage_pdf, out):
    with pytest.raises(ValueError):
        rotate_pdf(multipage_pdf, out, angle=360)


def test_out_of_range_page_raises(multipage_pdf, out):
    with pytest.raises(ValueError, match="out of range"):
        rotate_pdf(multipage_pdf, out, angle=90, pages=[99])


def test_missing_input_raises(out):
    with pytest.raises(FileNotFoundError):
        rotate_pdf("nonexistent.pdf", out, angle=90)
