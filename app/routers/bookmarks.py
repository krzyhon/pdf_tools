import json
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.storage import save_upload, upload_result
from pdf_bookmarks import add_bookmarks, list_bookmarks, remove_bookmarks

router = APIRouter()


@router.post("/api/bookmarks/list")
async def bookmarks_list(file: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        return {"bookmarks": list_bookmarks(inp)}


@router.post("/api/bookmarks/add")
async def bookmarks_add(
    file: UploadFile = File(...),
    bookmarks: str = Form(
        ...,
        description='JSON list of {level, title, page}, e.g. [{"level":1,"title":"Intro","page":1}]',
    ),
):
    try:
        parsed = json.loads(bookmarks)
    except json.JSONDecodeError:
        raise HTTPException(422, "Invalid JSON for bookmarks")

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        out = os.path.join(tmpdir, "bookmarked.pdf")
        count = add_bookmarks(inp, out, parsed)
        stem = Path(file.filename or "result").stem
        return upload_result(out, f"{stem}_bookmarked.pdf") | {"added": count}


@router.post("/api/bookmarks/remove")
async def bookmarks_remove(file: UploadFile = File(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        out = os.path.join(tmpdir, "no_bookmarks.pdf")
        count = remove_bookmarks(inp, out)
        stem = Path(file.filename or "result").stem
        return upload_result(out, f"{stem}_no_bookmarks.pdf") | {"removed": count}
