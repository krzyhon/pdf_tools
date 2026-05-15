import json
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.storage import save_upload, upload_result
from pdf_redactor import redact_text, redact_areas

router = APIRouter()


@router.post("/api/redact/text")
async def redact_by_text(
    file: UploadFile = File(...),
    terms: str = Form(
        ..., description='JSON list of strings to redact, e.g. ["John Doe","SSN"]'
    ),
):
    try:
        parsed_terms = json.loads(terms)
    except json.JSONDecodeError:
        raise HTTPException(422, "Invalid JSON for terms")

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        out = os.path.join(tmpdir, "redacted.pdf")
        count = redact_text(inp, out, parsed_terms)
        stem = Path(file.filename or "result").stem
        return upload_result(out, f"{stem}_redacted.pdf") | {"redactions": count}


@router.post("/api/redact/areas")
async def redact_by_areas(
    file: UploadFile = File(...),
    areas: str = Form(
        ..., description="JSON list of [page, x0, y0, x1, y1], e.g. [[1,10,20,100,50]]"
    ),
    terms: str = Form(
        None, description="Optional JSON list of additional text terms to redact"
    ),
):
    try:
        parsed_areas = [tuple(a) for a in json.loads(areas)]
        parsed_terms = json.loads(terms) if terms else None
    except (json.JSONDecodeError, TypeError, ValueError):
        raise HTTPException(422, "Invalid JSON for areas or terms")

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        out = os.path.join(tmpdir, "redacted.pdf")
        count = redact_areas(inp, out, parsed_areas, terms=parsed_terms)
        stem = Path(file.filename or "result").stem
        return upload_result(out, f"{stem}_redacted.pdf") | {"redactions": count}
