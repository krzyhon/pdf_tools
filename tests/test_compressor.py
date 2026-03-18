import pytest
from pathlib import Path
from pdf_compressor import compress_pdf


def test_returns_size_tuple(simple_pdf, out):
    original, compressed = compress_pdf(simple_pdf, out)
    assert isinstance(original, int)
    assert isinstance(compressed, int)
    assert original > 0
    assert compressed > 0


def test_output_file_created(simple_pdf, out):
    compress_pdf(simple_pdf, out)
    assert Path(out).exists()


def test_missing_input_raises(out):
    with pytest.raises(FileNotFoundError):
        compress_pdf("nonexistent.pdf", out)


def test_invalid_dpi_raises(simple_pdf, out):
    with pytest.raises(ValueError):
        compress_pdf(simple_pdf, out, image_dpi=0)


def test_negative_dpi_raises(simple_pdf, out):
    with pytest.raises(ValueError):
        compress_pdf(simple_pdf, out, image_dpi=-100)


def test_with_image_dpi(simple_pdf, out):
    original, compressed = compress_pdf(simple_pdf, out, image_dpi=150)
    assert Path(out).exists()
    assert compressed > 0
