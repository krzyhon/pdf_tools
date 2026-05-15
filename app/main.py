from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import (
    bookmarks,
    compress,
    convert,
    diff,
    health,
    inspect,
    merge,
    ocr,
    page_numbers,
    protect,
    redact,
    reorder,
    rotate,
    split,
    watermark,
)

app = FastAPI(
    title="PDF Tools",
    docs_url="/api/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://pdftools.flairops.cloud",
        "http://localhost:3000",
        "http://localhost:8000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in [
    health,
    merge,
    split,
    compress,
    protect,
    rotate,
    reorder,
    ocr,
    watermark,
    page_numbers,
    convert,
    redact,
    diff,
    inspect,
    bookmarks,
]:
    app.include_router(module.router)


@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"detail": str(exc)})
