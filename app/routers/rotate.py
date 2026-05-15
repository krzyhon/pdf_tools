import json
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.storage import save_upload, upload_result
from pdf_rotator import rotate_pdf

router = APIRouter()


@router.post("/api/rotate")
async def rotate(
    file: UploadFile = File(...),
    angle: int = Form(..., description="Degrees to rotate: 90, 180, or 270"),
    pages: str = Form(
        None,
        description="JSON list of 1-based page numbers, e.g. [1,3]. Omit for all pages.",
    ),
):
    if angle not in (90, 180, 270):
        raise HTTPException(422, "angle must be 90, 180, or 270")

    parsed_pages = None
    if pages:
        try:
            parsed_pages = json.loads(pages)
        except json.JSONDecodeError:
            raise HTTPException(422, "Invalid JSON for pages")

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        out = os.path.join(tmpdir, "rotated.pdf")
        pages_rotated = rotate_pdf(inp, out, angle, pages=parsed_pages)
        stem = Path(file.filename or "result").stem
        return upload_result(out, f"{stem}_rotated.pdf") | {
            "pages_rotated": pages_rotated
        }
