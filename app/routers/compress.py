import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile

from app.storage import save_upload, upload_result
from pdf_compressor import compress_pdf

router = APIRouter()


@router.post("/api/compress")
async def compress(
    file: UploadFile = File(...),
    image_dpi: int | None = Form(
        None, description="Downsample images to this DPI (optional)"
    ),
):
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        out = os.path.join(tmpdir, "compressed.pdf")
        original_bytes, compressed_bytes = compress_pdf(inp, out, image_dpi=image_dpi)
        stem = Path(file.filename or "result").stem
        return upload_result(out, f"{stem}_compressed.pdf") | {
            "original_bytes": original_bytes,
            "compressed_bytes": compressed_bytes,
            "savings_pct": round((1 - compressed_bytes / original_bytes) * 100, 1),
        }
