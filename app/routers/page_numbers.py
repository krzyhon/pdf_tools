import json
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.storage import save_upload, upload_result
from pdf_page_numbers import add_page_numbers

router = APIRouter()

_VALID_POSITIONS = {
    "bottom-left",
    "bottom-center",
    "bottom-right",
    "top-left",
    "top-center",
    "top-right",
}


@router.post("/api/page-numbers")
async def page_numbers(
    file: UploadFile = File(...),
    position: str = Form("bottom-center"),
    fmt: str = Form(
        "{n}", description="Format string: {n} = current page, {N} = total pages"
    ),
    start: int = Form(1, description="Number assigned to the first page"),
    fontsize: float = Form(10.0),
    pages: str = Form(
        None, description="JSON list of 1-based page numbers to stamp. Omit for all."
    ),
):
    if position not in _VALID_POSITIONS:
        raise HTTPException(
            422, f"position must be one of: {', '.join(sorted(_VALID_POSITIONS))}"
        )

    parsed_pages = None
    if pages:
        try:
            parsed_pages = json.loads(pages)
        except json.JSONDecodeError:
            raise HTTPException(422, "Invalid JSON for pages")

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        out = os.path.join(tmpdir, "numbered.pdf")
        stamped = add_page_numbers(
            inp,
            out,
            position=position,
            fmt=fmt,
            start=start,
            fontsize=fontsize,
            pages=parsed_pages,
        )
        stem = Path(file.filename or "result").stem
        return upload_result(out, f"{stem}_numbered.pdf") | {"pages_stamped": stamped}
