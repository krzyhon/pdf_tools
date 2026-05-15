"""FastAPI router tests — all endpoints with mocked S3."""

import io
import json
import os
from unittest.mock import MagicMock, patch

import fitz
import pytest
from PIL import Image

os.environ.setdefault("TEMP_BUCKET", "test-bucket")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

client = TestClient(app)

FAKE_URL = "https://s3.example.com/result.pdf"
FAKE_UPLOAD = {"download_url": FAKE_URL, "filename": "result.pdf"}

_mock_s3 = MagicMock()
_mock_s3.generate_presigned_url.return_value = FAKE_URL
_mock_s3.upload_file.return_value = None


@pytest.fixture(autouse=True)
def mock_boto(monkeypatch):
    with patch("boto3.client", return_value=_mock_s3):
        yield


@pytest.fixture
def pdf_bytes(tmp_path):
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 100), "Hello World", fontsize=14)
    page.insert_text((50, 200), "Secret phrase", fontsize=12)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


@pytest.fixture
def multipage_pdf_bytes(tmp_path):
    doc = fitz.open()
    for i in range(1, 5):
        page = doc.new_page(width=595, height=842)
        page.insert_text((50, 100), f"Page {i} content", fontsize=14)
    buf = io.BytesIO()
    doc.save(buf)
    doc.close()
    return buf.getvalue()


@pytest.fixture
def png_bytes():
    img = Image.new("RGB", (100, 100), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------


def test_merge(pdf_bytes):
    files = [
        ("files", ("a.pdf", pdf_bytes, "application/pdf")),
        ("files", ("b.pdf", pdf_bytes, "application/pdf")),
    ]
    r = client.post("/api/merge", files=files)
    assert r.status_code == 200
    body = r.json()
    assert "pages" in body
    assert "download_url" in body


# ---------------------------------------------------------------------------
# Split
# ---------------------------------------------------------------------------


def test_split_pages(pdf_bytes):
    r = client.post(
        "/api/split/pages", files={"file": ("test.pdf", pdf_bytes, "application/pdf")}
    )
    assert r.status_code == 200
    assert r.json()["count"] == 1


def test_split_ranges(multipage_pdf_bytes):
    r = client.post(
        "/api/split/ranges",
        files={"file": ("test.pdf", multipage_pdf_bytes, "application/pdf")},
        data={"ranges": "[[1,2],[3,4]]"},
    )
    assert r.status_code == 200
    assert r.json()["count"] == 2


def test_split_ranges_with_names(multipage_pdf_bytes):
    r = client.post(
        "/api/split/ranges",
        files={"file": ("test.pdf", multipage_pdf_bytes, "application/pdf")},
        data={"ranges": "[[1,2]]", "names": '["part1.pdf"]'},
    )
    assert r.status_code == 200


def test_split_ranges_invalid_json(pdf_bytes):
    r = client.post(
        "/api/split/ranges",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"ranges": "not-json"},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Compress
# ---------------------------------------------------------------------------


def test_compress(pdf_bytes):
    r = client.post(
        "/api/compress", files={"file": ("test.pdf", pdf_bytes, "application/pdf")}
    )
    assert r.status_code == 200
    body = r.json()
    assert "original_bytes" in body
    assert "compressed_bytes" in body
    assert "savings_pct" in body


def test_compress_with_dpi(pdf_bytes):
    r = client.post(
        "/api/compress",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"image_dpi": "72"},
    )
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# Protect / Decrypt
# ---------------------------------------------------------------------------


def test_protect(pdf_bytes):
    r = client.post(
        "/api/protect",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"password": "s3cret"},
    )
    assert r.status_code == 200
    assert "download_url" in r.json()


def test_decrypt(pdf_bytes):
    # First protect, then decrypt using real bytes
    protected = _protect_pdf_bytes(pdf_bytes, "pass123")
    r = client.post(
        "/api/decrypt",
        files={"file": ("protected.pdf", protected, "application/pdf")},
        data={"password": "pass123"},
    )
    assert r.status_code == 200
    assert "download_url" in r.json()


def _protect_pdf_bytes(pdf_bytes: bytes, password: str) -> bytes:
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Rotate
# ---------------------------------------------------------------------------


def test_rotate_all_pages(pdf_bytes):
    r = client.post(
        "/api/rotate",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"angle": "90"},
    )
    assert r.status_code == 200
    assert "pages_rotated" in r.json()


def test_rotate_specific_pages(multipage_pdf_bytes):
    r = client.post(
        "/api/rotate",
        files={"file": ("test.pdf", multipage_pdf_bytes, "application/pdf")},
        data={"angle": "180", "pages": "[1,3]"},
    )
    assert r.status_code == 200


def test_rotate_invalid_angle(pdf_bytes):
    r = client.post(
        "/api/rotate",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"angle": "45"},
    )
    assert r.status_code == 422


def test_rotate_invalid_pages_json(pdf_bytes):
    r = client.post(
        "/api/rotate",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"angle": "90", "pages": "bad"},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Reorder
# ---------------------------------------------------------------------------


def test_reorder(multipage_pdf_bytes):
    r = client.post(
        "/api/reorder",
        files={"file": ("test.pdf", multipage_pdf_bytes, "application/pdf")},
        data={"page_order": "[4,3,2,1]"},
    )
    assert r.status_code == 200
    assert "pages" in r.json()


def test_reorder_invalid_json(pdf_bytes):
    r = client.post(
        "/api/reorder",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"page_order": "not-json"},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Watermark
# ---------------------------------------------------------------------------


def test_watermark(pdf_bytes):
    r = client.post(
        "/api/watermark",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"text": "CONFIDENTIAL"},
    )
    assert r.status_code == 200
    assert "download_url" in r.json()


# ---------------------------------------------------------------------------
# Page numbers
# ---------------------------------------------------------------------------


def test_page_numbers(pdf_bytes):
    r = client.post(
        "/api/page-numbers",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    assert r.status_code == 200
    assert "pages_stamped" in r.json()


def test_page_numbers_invalid_position(pdf_bytes):
    r = client.post(
        "/api/page-numbers",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"position": "middle"},
    )
    assert r.status_code == 422


def test_page_numbers_specific_pages(multipage_pdf_bytes):
    r = client.post(
        "/api/page-numbers",
        files={"file": ("test.pdf", multipage_pdf_bytes, "application/pdf")},
        data={"pages": "[1,2]", "position": "top-right"},
    )
    assert r.status_code == 200


def test_page_numbers_invalid_pages_json(pdf_bytes):
    r = client.post(
        "/api/page-numbers",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"pages": "bad"},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Inspect
# ---------------------------------------------------------------------------


def test_inspect(pdf_bytes):
    r = client.post(
        "/api/inspect",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["page"] == 1
    assert body["total_pages"] == 1
    assert isinstance(body["blocks"], list)


def test_inspect_with_search(pdf_bytes):
    r = client.post(
        "/api/inspect",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"search": "Hello"},
    )
    assert r.status_code == 200
    blocks = r.json()["blocks"]
    assert all("Hello" in b["text"] for b in blocks)


def test_inspect_out_of_range(pdf_bytes):
    r = client.post(
        "/api/inspect",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"page_num": "99"},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Redact
# ---------------------------------------------------------------------------


def test_redact_text(pdf_bytes):
    r = client.post(
        "/api/redact/text",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"terms": '["Hello World"]'},
    )
    assert r.status_code == 200
    assert "redactions" in r.json()


def test_redact_text_invalid_json(pdf_bytes):
    r = client.post(
        "/api/redact/text",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"terms": "not-json"},
    )
    assert r.status_code == 422


def test_redact_areas(pdf_bytes):
    r = client.post(
        "/api/redact/areas",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"areas": "[[1,0,0,100,50]]"},
    )
    assert r.status_code == 200
    assert "redactions" in r.json()


def test_redact_areas_with_terms(pdf_bytes):
    r = client.post(
        "/api/redact/areas",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"areas": "[[1,0,0,100,50]]", "terms": '["Secret"]'},
    )
    assert r.status_code == 200


def test_redact_areas_invalid_json(pdf_bytes):
    r = client.post(
        "/api/redact/areas",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"areas": "bad"},
    )
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Bookmarks
# ---------------------------------------------------------------------------


def test_bookmarks_list(pdf_bytes):
    r = client.post(
        "/api/bookmarks/list",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    assert r.status_code == 200
    assert "bookmarks" in r.json()


def test_bookmarks_add(pdf_bytes):
    bm = json.dumps([{"level": 1, "title": "Chapter 1", "page": 1}])
    r = client.post(
        "/api/bookmarks/add",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"bookmarks": bm},
    )
    assert r.status_code == 200
    assert r.json()["added"] == 1


def test_bookmarks_add_invalid_json(pdf_bytes):
    r = client.post(
        "/api/bookmarks/add",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"bookmarks": "bad"},
    )
    assert r.status_code == 422


def test_bookmarks_remove(pdf_bytes):
    r = client.post(
        "/api/bookmarks/remove",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    assert r.status_code == 200
    assert "removed" in r.json()


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------


def test_diff_report(pdf_bytes):
    files = [
        ("file_a", ("a.pdf", pdf_bytes, "application/pdf")),
        ("file_b", ("b.pdf", pdf_bytes, "application/pdf")),
    ]
    r = client.post("/api/diff/report", files=files)
    assert r.status_code == 200
    body = r.json()
    assert (
        "pages_a" in body
        or "changed_pages" in body
        or "summary" in body
        or isinstance(body, dict)
    )


def test_diff_visual(pdf_bytes):
    files = [
        ("file_a", ("a.pdf", pdf_bytes, "application/pdf")),
        ("file_b", ("b.pdf", pdf_bytes, "application/pdf")),
    ]
    r = client.post("/api/diff/visual", files=files)
    assert r.status_code == 200
    assert "download_url" in r.json()


# ---------------------------------------------------------------------------
# Convert: to-images, to-docx, from-images
# ---------------------------------------------------------------------------


def test_to_images(pdf_bytes):
    r = client.post(
        "/api/to-images",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    assert r.status_code == 200
    body = r.json()
    assert "count" in body
    assert body["count"] >= 1


def test_to_images_invalid_fmt(pdf_bytes):
    r = client.post(
        "/api/to-images",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"fmt": "bmp"},
    )
    assert r.status_code == 422


def test_to_images_specific_pages(multipage_pdf_bytes):
    r = client.post(
        "/api/to-images",
        files={"file": ("test.pdf", multipage_pdf_bytes, "application/pdf")},
        data={"pages": "[1,2]"},
    )
    assert r.status_code == 200
    assert r.json()["count"] == 2


def test_to_images_invalid_pages_json(pdf_bytes):
    r = client.post(
        "/api/to-images",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
        data={"pages": "bad"},
    )
    assert r.status_code == 422


def test_to_docx(pdf_bytes):
    r = client.post(
        "/api/to-docx",
        files={"file": ("test.pdf", pdf_bytes, "application/pdf")},
    )
    assert r.status_code == 200
    assert "download_url" in r.json()


def test_from_images(png_bytes):
    files = [
        ("files", ("a.png", png_bytes, "image/png")),
        ("files", ("b.png", png_bytes, "image/png")),
    ]
    r = client.post("/api/from-images", files=files)
    assert r.status_code == 200
    assert r.json()["pages"] == 2
