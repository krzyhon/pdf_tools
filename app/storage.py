import os
import uuid
import zipfile

import boto3
from fastapi import UploadFile

from app.config import AWS_REGION, TEMP_BUCKET


async def save_upload(file: UploadFile, directory: str) -> str:
    """Write an uploaded file to directory and return its local path."""
    filename = file.filename or "input.pdf"
    path = os.path.join(directory, filename)
    content = await file.read()
    with open(path, "wb") as f:
        f.write(content)
    return path


def zip_files(paths: list[str], zip_path: str) -> None:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in paths:
            zf.write(p, arcname=os.path.basename(p))


def upload_result(local_path: str, filename: str, expires: int = 3600) -> dict:
    """Upload a file to the temp S3 bucket and return a signed download URL."""
    key = f"results/{uuid.uuid4()}/{filename}"
    client = boto3.client("s3", region_name=AWS_REGION)
    client.upload_file(local_path, TEMP_BUCKET, key)
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": TEMP_BUCKET, "Key": key},
        ExpiresIn=expires,
    )
    return {"download_url": url, "filename": filename}
