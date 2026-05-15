import json
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.storage import save_upload, upload_result
from pdf_reorder import reorder_pdf

router = APIRouter()


@router.post("/api/reorder")
async def reorder(
    file: UploadFile = File(...),
    page_order: str = Form(
        ..., description="JSON list of 1-based page numbers, e.g. [3,1,2]"
    ),
):
    try:
        parsed_order = json.loads(page_order)
    except json.JSONDecodeError:
        raise HTTPException(422, "Invalid JSON for page_order")

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        out = os.path.join(tmpdir, "reordered.pdf")
        pages = reorder_pdf(inp, out, parsed_order)
        stem = Path(file.filename or "result").stem
        return upload_result(out, f"{stem}_reordered.pdf") | {"pages": pages}
