import json
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.storage import save_upload, upload_result, zip_files
from pdf_from_images import images_to_pdf
from pdf_to_docx import convert_pdf_to_docx
from pdf_to_images import pdf_to_images

router = APIRouter()


@router.post("/api/to-images")
async def to_images(
    file: UploadFile = File(...),
    fmt: str = Form("png", description='"png" or "jpeg"'),
    dpi: int = Form(150),
    pages: str = Form(
        None, description="JSON list of 1-based page numbers. Omit for all."
    ),
):
    if fmt not in ("png", "jpeg"):
        raise HTTPException(422, 'fmt must be "png" or "jpeg"')

    parsed_pages = None
    if pages:
        try:
            parsed_pages = json.loads(pages)
        except json.JSONDecodeError:
            raise HTTPException(422, "Invalid JSON for pages")

    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        out_dir = os.path.join(tmpdir, "images")
        os.makedirs(out_dir)
        paths = pdf_to_images(inp, out_dir, fmt=fmt, dpi=dpi, pages=parsed_pages)
        zip_path = os.path.join(tmpdir, "result.zip")
        zip_files(paths, zip_path)
        stem = Path(file.filename or "result").stem
        return upload_result(zip_path, f"{stem}_images.zip") | {"count": len(paths)}


@router.post("/api/to-docx")
async def to_docx(
    file: UploadFile = File(...),
    start_page: int = Form(1),
    end_page: int | None = Form(None),
):
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        out = os.path.join(tmpdir, "output.docx")
        convert_pdf_to_docx(inp, out, start_page=start_page, end_page=end_page)
        stem = Path(file.filename or "result").stem
        return upload_result(out, f"{stem}.docx")


@router.post("/api/from-images")
async def from_images(files: list[UploadFile] = File(...)):
    with tempfile.TemporaryDirectory() as tmpdir:
        image_paths = []
        for i, f in enumerate(files):
            path = os.path.join(tmpdir, f"img_{i:03d}_{f.filename or 'image'}")
            content = await f.read()
            with open(path, "wb") as fp:
                fp.write(content)
            image_paths.append(path)

        out = os.path.join(tmpdir, "output.pdf")
        pages = images_to_pdf(image_paths, out)
        return upload_result(out, "images_to_pdf.pdf") | {"pages": pages}
