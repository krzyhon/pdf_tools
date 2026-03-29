import pytest
import fitz
from pathlib import Path
from PIL import Image

from pdf_from_images import images_to_pdf


@pytest.fixture
def png_image(tmp_path):
    img = Image.new("RGB", (200, 300), color=(255, 0, 0))
    path = tmp_path / "red.png"
    img.save(str(path))
    return str(path)


@pytest.fixture
def jpg_image(tmp_path):
    img = Image.new("RGB", (200, 300), color=(0, 255, 0))
    path = tmp_path / "green.jpg"
    img.save(str(path))
    return str(path)


@pytest.fixture
def three_images(tmp_path):
    paths = []
    for i, color in enumerate([(255, 0, 0), (0, 255, 0), (0, 0, 255)]):
        img = Image.new("RGB", (100, 100), color=color)
        path = tmp_path / f"img_{i}.png"
        img.save(str(path))
        paths.append(str(path))
    return paths


def test_single_png_creates_one_page_pdf(png_image, tmp_path):
    out = str(tmp_path / "output.pdf")
    pages = images_to_pdf([png_image], out)
    assert pages == 1
    assert Path(out).exists()
    doc = fitz.open(out)
    assert doc.page_count == 1
    doc.close()


def test_multiple_images_creates_multipage_pdf(three_images, tmp_path):
    out = str(tmp_path / "output.pdf")
    pages = images_to_pdf(three_images, out)
    assert pages == 3
    doc = fitz.open(out)
    assert doc.page_count == 3
    doc.close()


def test_jpeg_image(jpg_image, tmp_path):
    out = str(tmp_path / "output.pdf")
    pages = images_to_pdf([jpg_image], out)
    assert pages == 1


def test_mixed_formats(png_image, jpg_image, tmp_path):
    out = str(tmp_path / "output.pdf")
    pages = images_to_pdf([png_image, jpg_image], out)
    assert pages == 2


def test_empty_list_raises():
    with pytest.raises(ValueError, match="At least one image"):
        images_to_pdf([], "output.pdf")


def test_nonexistent_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="not found"):
        images_to_pdf(["nonexistent.png"], str(tmp_path / "output.pdf"))


def test_unsupported_extension_raises(tmp_path):
    fake = tmp_path / "image.xyz"
    fake.write_bytes(b"fake data")
    with pytest.raises(ValueError, match="Unsupported image format"):
        images_to_pdf([str(fake)], str(tmp_path / "output.pdf"))


def test_output_file_is_valid_pdf(png_image, tmp_path):
    out = str(tmp_path / "output.pdf")
    images_to_pdf([png_image], out)
    doc = fitz.open(out)
    assert not doc.is_encrypted
    doc.close()
