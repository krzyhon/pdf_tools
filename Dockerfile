FROM python:3.12-slim

# System packages:
#   tesseract-ocr     — required by pytesseract (OCR tool)
#   tesseract-ocr-eng — English language pack (add others as needed, e.g. tesseract-ocr-pol)
#   libgl1            — required by PyMuPDF / pdf2docx
#   libglib2.0-0      — required by PyMuPDF
#   curl              — used by the ECS health check
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        tesseract-ocr-pol \
        libgl1 \
        libglib2.0-0 \
        curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies in a separate layer so they are cached
# across rebuilds that only change application code.
COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt

# Copy only the tool modules — no tests, no GUI, no Terraform
COPY pdf_bookmarks.py \
     pdf_compressor.py \
     pdf_decryptor.py \
     pdf_diff.py \
     pdf_from_images.py \
     pdf_inspector.py \
     pdf_merger.py \
     pdf_ocr.py \
     pdf_page_numbers.py \
     pdf_protector.py \
     pdf_redactor.py \
     pdf_reorder.py \
     pdf_rotator.py \
     pdf_splitter.py \
     pdf_to_docx.py \
     pdf_to_images.py \
     pdf_watermark.py \
     ./

# Application code (FastAPI app — to be added)
# COPY app/ ./app/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -sf http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
