import os
import tempfile

from fastapi import APIRouter, File, Form, UploadFile

from app.storage import upload_result
from pdf_diff import diff_report, diff_visual

router = APIRouter()


async def _save_two(file_a: UploadFile, file_b: UploadFile, directory: str):
    paths = []
    for f in (file_a, file_b):
        path = os.path.join(directory, f.filename or "input.pdf")
        content = await f.read()
        with open(path, "wb") as fp:
            fp.write(content)
        paths.append(path)
    return paths


@router.post("/api/diff/report")
async def diff_report_endpoint(
    file_a: UploadFile = File(...),
    file_b: UploadFile = File(...),
):
    with tempfile.TemporaryDirectory() as tmpdir:
        path_a, path_b = await _save_two(file_a, file_b, tmpdir)
        return diff_report(path_a, path_b)


@router.post("/api/diff/visual")
async def diff_visual_endpoint(
    file_a: UploadFile = File(...),
    file_b: UploadFile = File(...),
    dpi: int = Form(150),
):
    with tempfile.TemporaryDirectory() as tmpdir:
        path_a = os.path.join(tmpdir, f"a_{file_a.filename or 'a.pdf'}")
        path_b = os.path.join(tmpdir, f"b_{file_b.filename or 'b.pdf'}")
        for path, f in ((path_a, file_a), (path_b, file_b)):
            content = await f.read()
            with open(path, "wb") as fp:
                fp.write(content)
        out = os.path.join(tmpdir, "diff.pdf")
        report = diff_visual(path_a, path_b, out, dpi=dpi)
        return upload_result(out, "diff_visual.pdf") | report
