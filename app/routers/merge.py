import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, UploadFile

from app.storage import upload_result
from pdf_merger import merge_pdfs

router = APIRouter()


@router.post("/api/merge")
async def merge(files: list[UploadFile] = File(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        input_paths = []
        for i, f in enumerate(files):
            path = os.path.join(tmpdir, f"input_{i:03d}_{f.filename or 'file.pdf'}")
            content = await f.read()
            with open(path, "wb") as fp:
                fp.write(content)
            input_paths.append(path)

        out = os.path.join(tmpdir, "merged.pdf")
        stem = Path(files[0].filename or "result").stem
        pages = merge_pdfs(out, input_paths)
        return upload_result(out, f"{stem}_merged.pdf") | {"pages": pages}
