import pytest
from pathlib import Path
import fitz
from PIL import Image, ImageDraw, ImageFont
from pdf_ocr import ocr_to_pdf


def _make_image(tmp_path, text="Hello World", suffix=".png") -> str:
    """Create a simple white image with black text."""
    img = Image.new("RGB", (400, 100), color="white")
    draw = ImageDraw.Draw(img)
    draw.text((20, 30), text, fill="black")
    path = str(tmp_path / f"test_image{suffix}")
    img.save(path)
    return path


def _make_scanned_pdf(tmp_path) -> str:
    """Create a PDF whose pages are pure images (simulates a scanned document)."""
    path = tmp_path / "scanned.pdf"
    out_doc = fitz.open()

    for word in ("FirstPage", "SecondPage"):
        img = Image.new("RGB", (595, 100), color="white")
        draw = ImageDraw.Draw(img)
        draw.text((20, 30), word, fill="black")

        import io
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        page = out_doc.new_page(width=595, height=100)
        page.insert_image(page.rect, stream=buf.read())

    out_doc.save(str(path))
    out_doc.close()
    return str(path)


# --- basic functionality ---

def test_ocr_image_creates_output(tmp_path, out):
    img_path = _make_image(tmp_path)
    ocr_to_pdf(img_path, out)
    assert Path(out).exists()
    assert Path(out).stat().st_size > 0


def test_ocr_image_returns_page_count(tmp_path, out):
    img_path = _make_image(tmp_path)
    count = ocr_to_pdf(img_path, out)
    assert count == 1


def test_ocr_image_output_is_valid_pdf(tmp_path, out):
    img_path = _make_image(tmp_path)
    ocr_to_pdf(img_path, out)
    doc = fitz.open(out)
    assert doc.page_count == 1
    doc.close()


def test_ocr_image_text_is_searchable(tmp_path, out):
    img_path = _make_image(tmp_path, text="Hello")
    ocr_to_pdf(img_path, out)
    doc = fitz.open(out)
    text = doc[0].get_text()
    doc.close()
    assert "Hello" in text


def test_ocr_jpg_image(tmp_path, out):
    img_path = _make_image(tmp_path, suffix=".jpg")
    count = ocr_to_pdf(img_path, out)
    assert count == 1
    assert Path(out).exists()


def test_ocr_tiff_image(tmp_path, out):
    img_path = _make_image(tmp_path, suffix=".tiff")
    count = ocr_to_pdf(img_path, out)
    assert count == 1
    assert Path(out).exists()


# --- PDF input ---

def test_ocr_pdf_creates_output(tmp_path, out):
    pdf_path = _make_scanned_pdf(tmp_path)
    ocr_to_pdf(pdf_path, out)
    assert Path(out).exists()


def test_ocr_pdf_page_count(tmp_path, out):
    pdf_path = _make_scanned_pdf(tmp_path)
    count = ocr_to_pdf(pdf_path, out)
    assert count == 2


def test_ocr_pdf_output_has_correct_pages(tmp_path, out):
    pdf_path = _make_scanned_pdf(tmp_path)
    ocr_to_pdf(pdf_path, out)
    doc = fitz.open(out)
    assert doc.page_count == 2
    doc.close()


# --- validation ---

def test_missing_file_raises(out):
    with pytest.raises(FileNotFoundError):
        ocr_to_pdf("nonexistent.pdf", out)


def test_unsupported_format_raises(tmp_path, out):
    p = tmp_path / "file.xyz"
    p.write_text("data")
    with pytest.raises(ValueError, match="Unsupported"):
        ocr_to_pdf(str(p), out)


def test_invalid_dpi_raises(tmp_path, out):
    img_path = _make_image(tmp_path)
    with pytest.raises(ValueError, match="DPI"):
        ocr_to_pdf(img_path, out, dpi=0)


def test_dpi_too_high_raises(tmp_path, out):
    img_path = _make_image(tmp_path)
    with pytest.raises(ValueError, match="DPI"):
        ocr_to_pdf(img_path, out, dpi=601)
