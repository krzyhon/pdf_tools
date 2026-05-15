import tempfile

import fitz
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.storage import save_upload

router = APIRouter()


@router.post("/api/inspect")
async def inspect(
    file: UploadFile = File(...),
    page_num: int = Form(1),
    search: str | None = Form(None, description="Filter blocks containing this text"),
):
    with tempfile.TemporaryDirectory() as tmpdir:
        inp = await save_upload(file, tmpdir)
        doc = fitz.open(inp)
        total = doc.page_count

        if page_num < 1 or page_num > total:
            doc.close()
            raise HTTPException(
                422, f"Page {page_num} out of range (document has {total} pages)"
            )

        page = doc[page_num - 1]
        raw_blocks = page.get_text("blocks")
        doc.close()

        blocks = []
        for x0, y0, x1, y1, text, *_ in raw_blocks:
            text = text.strip()
            if not text:
                continue
            if search and search.lower() not in text.lower():
                continue
            blocks.append(
                {
                    "page": page_num,
                    "x0": round(x0, 1),
                    "y0": round(y0, 1),
                    "x1": round(x1, 1),
                    "y1": round(y1, 1),
                    "text": text,
                    # ready-to-use area string for the /api/redact/areas endpoint
                    "area": f"{page_num}:{round(x0, 1)},{round(y0, 1)},{round(x1, 1)},{round(y1, 1)}",
                }
            )

        return {"page": page_num, "total_pages": total, "blocks": blocks}
