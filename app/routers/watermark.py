import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile

from app.storage import save_upload, upload_result
from pdf_watermark import watermark_pdf

router = APIRouter()


@router.post("/api/watermark")
async def watermark(
    file: UploadFile = File(...),
    text: str = Form(...),
    fontsize: float = Form(60.0),
    opacity: float = Form(0.15, description="0.0 (invisible) to 1.0 (opaque)"),
    angle: float = Form(45.0, description="Counter-clockwise degrees"),
):
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        out = os.path.join(tmpdir, "watermarked.pdf")
        watermark_pdf(inp, out, text, fontsize=fontsize, opacity=opacity, angle=angle)
        stem = Path(file.filename or "result").stem
        return upload_result(out, f"{stem}_watermarked.pdf")
