import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile

from app.storage import save_upload, upload_result
from pdf_ocr import ocr_to_pdf

router = APIRouter()


@router.post("/api/ocr")
async def ocr(
    file: UploadFile = File(...),
    language: str = Form(
        "eng", description='Tesseract language code, e.g. "eng", "pol", "eng+pol"'
    ),
    dpi: int = Form(300, description="Render resolution (default 300)"),
):
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        out = os.path.join(tmpdir, "ocr.pdf")
        pages = ocr_to_pdf(inp, out, language=language, dpi=dpi)
        stem = Path(file.filename or "result").stem
        return upload_result(out, f"{stem}_ocr.pdf") | {"pages": pages}
