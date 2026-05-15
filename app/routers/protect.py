import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile

from app.storage import save_upload, upload_result
from pdf_decryptor import decrypt_pdf
from pdf_protector import protect_pdf

router = APIRouter()


@router.post("/api/protect")
async def protect(
    file: UploadFile = File(...),
    password: str = Form(...),
):
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        out = os.path.join(tmpdir, "protected.pdf")
        protect_pdf(inp, out, password)
        stem = Path(file.filename or "result").stem
        return upload_result(out, f"{stem}_protected.pdf")


@router.post("/api/decrypt")
async def decrypt(
    file: UploadFile = File(...),
    password: str = Form(...),
):
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        out = os.path.join(tmpdir, "decrypted.pdf")
        decrypt_pdf(inp, out, password)
        stem = Path(file.filename or "result").stem
        return upload_result(out, f"{stem}_decrypted.pdf")
