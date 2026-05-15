import json
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.storage import save_upload, upload_result, zip_files
from pdf_splitter import split_pdf_pages, split_pdf_ranges

router = APIRouter()


@router.post("/api/split/pages")
async def split_pages(file: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        out_dir = os.path.join(tmpdir, "pages")
        os.makedirs(out_dir)
        paths = split_pdf_pages(inp, out_dir)
        zip_path = os.path.join(tmpdir, "result.zip")
        zip_files(paths, zip_path)
        stem = Path(file.filename or "result").stem
        return upload_result(zip_path, f"{stem}_pages.zip") | {"count": len(paths)}


@router.post("/api/split/ranges")
async def split_ranges(
    file: UploadFile = File(...),
    ranges: str = Form(
        ..., description="JSON list of [start, end] pairs, e.g. [[1,3],[5,7]]"
    ),
    names: str = Form(None, description="Optional JSON list of output filenames"),
):
    try:
        parsed_ranges = [tuple(r) for r in json.loads(ranges)]
        parsed_names = json.loads(names) if names else None
    except (json.JSONDecodeError, TypeError, ValueError):
        raise HTTPException(422, "Invalid JSON for ranges or names")

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        out_dir = os.path.join(tmpdir, "ranges")
        os.makedirs(out_dir)
        paths = split_pdf_ranges(inp, out_dir, parsed_ranges, parsed_names)
        zip_path = os.path.join(tmpdir, "result.zip")
        zip_files(paths, zip_path)
        stem = Path(file.filename or "result").stem
        return upload_result(zip_path, f"{stem}_split.zip") | {"count": len(paths)}
