import pytest
from pathlib import Path
from pdf_watermark import watermark_pdf


def test_output_file_created(simple_pdf, out):
    watermark_pdf(simple_pdf, out, text="DRAFT")
    assert Path(out).exists()


def test_multipage_watermark(multipage_pdf, out):
    watermark_pdf(multipage_pdf, out, text="CONFIDENTIAL")
    assert Path(out).exists()


def test_custom_fontsize(simple_pdf, out):
    watermark_pdf(simple_pdf, out, text="TEST", fontsize=80)
    assert Path(out).exists()


def test_custom_opacity(simple_pdf, out):
    watermark_pdf(simple_pdf, out, text="TEST", opacity=0.5)
    assert Path(out).exists()


def test_custom_angle(simple_pdf, out):
    watermark_pdf(simple_pdf, out, text="TEST", angle=30)
    assert Path(out).exists()


def test_custom_color(simple_pdf, out):
    watermark_pdf(simple_pdf, out, text="TEST", color=(1.0, 0.0, 0.0))
    assert Path(out).exists()


def test_empty_text_raises(simple_pdf, out):
    with pytest.raises(ValueError, match="empty"):
        watermark_pdf(simple_pdf, out, text="")


def test_whitespace_text_raises(simple_pdf, out):
    with pytest.raises(ValueError, match="empty"):
        watermark_pdf(simple_pdf, out, text="   ")


def test_opacity_too_high_raises(simple_pdf, out):
    with pytest.raises(ValueError, match="Opacity"):
        watermark_pdf(simple_pdf, out, text="TEST", opacity=1.5)


def test_opacity_negative_raises(simple_pdf, out):
    with pytest.raises(ValueError, match="Opacity"):
        watermark_pdf(simple_pdf, out, text="TEST", opacity=-0.1)


def test_missing_input_raises(out):
    with pytest.raises(FileNotFoundError):
        watermark_pdf("nonexistent.pdf", out, text="TEST")
