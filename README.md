# PDF Tools

A collection of command-line Python utilities for common PDF operations.

## Requirements

```bash
pip install -r requirements.txt
```

Python dependencies: `pypdf`, `pymupdf`, `tqdm`, `cryptography`, `pdf2docx`, `pytesseract`, `Pillow`

**System dependency for OCR only:** [Tesseract](https://github.com/tesseract-ocr/tesseract)

```bash
# macOS
brew install tesseract

# Ubuntu / Debian
sudo apt install tesseract-ocr

# Windows
winget install UB-Mannheim.TesseractOCR
```

---

## Tools

### pdf_bookmarks.py — Manage bookmarks (table of contents)

List, add, or remove PDF bookmarks (also called the document outline or table of contents). Bookmark levels are 1-based (1 = top-level chapter, 2 = sub-section, etc.).

```bash
# List all bookmarks
python pdf_bookmarks.py list input.pdf

# Add bookmarks (format: LEVEL:TITLE:PAGE)
python pdf_bookmarks.py add input.pdf output.pdf "1:Introduction:1" "2:Overview:2" "1:Chapter 1:3"

# Remove all bookmarks
python pdf_bookmarks.py remove input.pdf output.pdf
```

| Subcommand | Arguments | Description |
|---|---|---|
| `list` | `input` | Print all bookmarks with level and page |
| `add` | `input` `output` `BOOKMARK...` | Append bookmarks; format `LEVEL:TITLE:PAGE` |
| `remove` | `input` `output` | Strip all bookmarks from the document |

> Note: bookmark visibility depends on the PDF viewer. Chrome and Firefox show them reliably; macOS Preview may not display them.

---

### pdf_compressor.py — Reduce file size

Applies lossless compression (removes unused objects, deduplicates resources, re-compresses streams). Optionally downsamples images for more aggressive reduction.

```bash
# Lossless only
python pdf_compressor.py input.pdf output.pdf

# Also downsample images to 150 DPI
python pdf_compressor.py input.pdf output.pdf --image-dpi 150
```

| Argument | Description |
|---|---|
| `input` | Source PDF |
| `output` | Compressed output PDF |
| `--image-dpi DPI` | Downsample images to this DPI (optional) |

---

### pdf_decryptor.py — Remove password protection

Unlocks a password-protected PDF. Requires the correct password.

```bash
python pdf_decryptor.py locked.pdf unlocked.pdf --password secret

# Prompted securely if omitted
python pdf_decryptor.py locked.pdf unlocked.pdf
```

| Argument | Description |
|---|---|
| `input` | Encrypted source PDF |
| `output` | Decrypted output PDF |
| `--password` | Password (prompted if omitted) |

---

### pdf_diff.py — Compare two PDFs

Compares two PDF files and reports text-level and visual differences. The text report lists changed, added, and removed pages. The visual output is a side-by-side PDF with word-level red/green highlights.

```bash
# Print text diff report only
python pdf_diff.py v1.pdf v2.pdf

# Also produce a visual diff PDF
python pdf_diff.py v1.pdf v2.pdf --output diff.pdf

# Lower DPI for faster comparison (default: 150)
python pdf_diff.py v1.pdf v2.pdf --output diff.pdf --dpi 100
```

| Argument | Description |
|---|---|
| `pdf_a` | First (original) PDF |
| `pdf_b` | Second (modified) PDF |
| `--output FILE` | Write a visual diff PDF (optional) |
| `--dpi N` | Render resolution for pixel comparison, 1–600 (default: 150) |

The text report contains:
- `changed_pages` — pages whose text differs (with unified diff)
- `added_pages` — pages present in B but not A (1-based)
- `removed_pages` — pages present in A but not B (1-based)
- `pages_a` / `pages_b` — total page counts

---

### pdf_inspector.py — Find coordinates for redaction

Two modes to help locate areas to redact:

**Text mode** — lists text blocks with their bounding box coordinates.

```bash
# All blocks on page 1
python pdf_inspector.py text input.pdf

# Page 3, filter by keyword
python pdf_inspector.py text input.pdf --page 3 --search "John"
```

**View mode** — interactive GUI. Move the mouse to see live coordinates; drag to draw a rectangle and get a ready-to-use `pdf_redactor.py` command.

```bash
python pdf_inspector.py view input.pdf
python pdf_inspector.py view input.pdf --page 2
```

Coordinates are in PDF points (1 pt = 1/72 inch), top-left origin.

---

### pdf_merger.py — Merge multiple PDFs

Concatenates two or more PDF files into one, in the order given.

```bash
python pdf_merger.py output.pdf file1.pdf file2.pdf file3.pdf
```

| Argument | Description |
|---|---|
| `output` | Merged output PDF |
| `inputs` | Two or more source PDFs (in order) |

---

### pdf_ocr.py — Make scanned PDFs searchable

Converts a scanned PDF or image into a searchable PDF using Tesseract OCR. Each page is rendered to an image, OCR'd, and saved as a PDF with a hidden text layer — the result looks identical but is fully searchable and copy-pasteable.

Requires Tesseract installed on the system (see [Requirements](#requirements)).

```bash
# Scanned PDF → searchable PDF
python pdf_ocr.py scan.pdf searchable.pdf

# Image → PDF
python pdf_ocr.py scan.png searchable.pdf

# Non-English document
python pdf_ocr.py scan.pdf searchable.pdf --lang pol

# Higher DPI for better accuracy
python pdf_ocr.py scan.pdf searchable.pdf --dpi 400
```

| Argument | Description |
|---|---|
| `input` | Source file: scanned PDF or image (PNG, JPG, TIFF, BMP, WebP) |
| `output` | Path for the searchable output PDF |
| `--lang CODE` | Tesseract language code (default: `eng`). Examples: `pol`, `deu`, `fra`. Combine with `+`: `eng+pol` |
| `--dpi N` | Render resolution for PDF pages, 1–600 (default: 300). Higher = better accuracy, slower |

For additional language packs:
```bash
# macOS
brew install tesseract-lang

# Ubuntu / Debian
sudo apt install tesseract-ocr-pol   # e.g. Polish
```

---

### pdf_page_numbers.py — Stamp page numbers

Adds page numbers to every page (or a selected subset). The format string supports `{n}` for the current page number and `{N}` for total pages.

```bash
# Default: "1", "2", … centred at the bottom
python pdf_page_numbers.py input.pdf output.pdf

# "Page 1 of 10" at the bottom-right
python pdf_page_numbers.py input.pdf output.pdf --format "Page {n} of {N}" --position bottom-right

# Start numbering from 5, larger font
python pdf_page_numbers.py input.pdf output.pdf --start 5 --fontsize 12

# Stamp only pages 1, 2, and 3
python pdf_page_numbers.py input.pdf output.pdf --pages 1 2 3
```

| Argument | Description |
|---|---|
| `input` | Source PDF |
| `output` | Output PDF with page numbers |
| `--position POS` | Where to place numbers: `bottom-left`, `bottom-center` (default), `bottom-right`, `top-left`, `top-center`, `top-right` |
| `--format STR` | Number format string (default: `{n}`). Use `{n}` = current page, `{N}` = total pages |
| `--start N` | First page number to print (default: 1) |
| `--fontsize PT` | Font size in points (default: 10) |
| `--pages N ...` | 1-based page numbers to stamp (default: all) |

---

### pdf_protector.py — Encrypt with a password

Applies AES-256 password encryption to a PDF.

```bash
python pdf_protector.py input.pdf output.pdf --password mypassword

# Prompted securely (with confirmation) if omitted
python pdf_protector.py input.pdf output.pdf
```

| Argument | Description |
|---|---|
| `input` | Source PDF |
| `output` | Encrypted output PDF |
| `--password` | Password (prompted if omitted) |

---

### pdf_redactor.py — Permanently redact content

Removes both the visual content and the underlying data from specified areas. **Irreversible.**

Coordinates format: `PAGE:x0,y0,x1,y1` (1-based page, PDF points from top-left).

```bash
# By rectangle coordinates
python pdf_redactor.py input.pdf output.pdf --areas "1:100,50,400,80"

# By text search (all pages)
python pdf_redactor.py input.pdf output.pdf --text "John Doe" "secret"

# Combined
python pdf_redactor.py input.pdf output.pdf --text "secret" --areas "1:100,50,400,80"
```

| Argument | Description |
|---|---|
| `input` | Source PDF |
| `output` | Redacted output PDF |
| `--areas PAGE:x0,y0,x1,y1` | One or more rectangles to redact |
| `--text TERM ...` | One or more text phrases to find and redact |

> Tip: use `pdf_inspector.py` to find the exact coordinates.

---

### pdf_reorder.py — Rearrange pages

Outputs a PDF with pages in a new order. Pages may be repeated or omitted.

```bash
# Reverse a 3-page PDF
python pdf_reorder.py input.pdf output.pdf 3 2 1

# Duplicate page 1
python pdf_reorder.py input.pdf output.pdf 1 1 2 3

# Extract only pages 2 and 4
python pdf_reorder.py input.pdf output.pdf 2 4
```

| Argument | Description |
|---|---|
| `input` | Source PDF |
| `output` | Reordered output PDF |
| `PAGE ...` | 1-based page numbers in desired output order |

---

### pdf_rotator.py — Rotate pages

Rotates all pages or specific pages by 90, 180, or 270 degrees clockwise.

```bash
# Rotate all pages 90° clockwise
python pdf_rotator.py input.pdf output.pdf 90

# Rotate only pages 1, 3, and 5 by 180°
python pdf_rotator.py input.pdf output.pdf 180 --pages 1 3 5
```

| Argument | Description |
|---|---|
| `input` | Source PDF |
| `output` | Rotated output PDF |
| `ANGLE` | Clockwise rotation: `90`, `180`, or `270` |
| `--pages N ...` | 1-based page numbers to rotate (default: all) |

---

### pdf_splitter.py — Split into multiple files

Split every page into a separate file, or split by page ranges.

```bash
# One file per page → output_dir/page_001.pdf, page_002.pdf, ...
python pdf_splitter.py input.pdf output_dir/

# Split by ranges → output_dir/part_01.pdf, part_02.pdf
python pdf_splitter.py input.pdf output_dir/ --ranges 1-3 4-6
```

| Argument | Description |
|---|---|
| `input` | Source PDF |
| `output_dir` | Directory for output files (created if needed) |
| `--ranges START-END ...` | Page ranges to extract, 1-based inclusive |

---

### pdf_to_docx.py — Convert PDF to Word document

Converts a PDF to a `.docx` file. Text, images, and simple tables are handled well. Complex layouts (multi-column, overlapping elements) may not be reproduced exactly since PDF is fixed-layout and DOCX is flow-based.

```bash
# Convert entire document
python pdf_to_docx.py input.pdf output.docx

# Convert only pages 2 to 4
python pdf_to_docx.py input.pdf output.docx --start 2 --end 4
```

| Argument | Description |
|---|---|
| `input` | Source PDF |
| `output` | Output .docx file |
| `--start N` | First page to convert, 1-based (default: 1) |
| `--end N` | Last page to convert, 1-based inclusive (default: last page) |

---

### pdf_to_images.py — Convert pages to images

Renders each PDF page as a PNG or JPEG file. Output files are named `page_001.png`, `page_002.png`, etc.

```bash
# All pages as PNG at 150 DPI → output_dir/page_001.png, ...
python pdf_to_images.py input.pdf output_dir/

# Pages 1 and 3 as JPEG at 200 DPI
python pdf_to_images.py input.pdf output_dir/ --format jpeg --dpi 200 --pages 1 3
```

| Argument | Description |
|---|---|
| `input` | Source PDF |
| `output_dir` | Directory for output images (created if needed) |
| `--format png\|jpeg` | Image format (default: png) |
| `--dpi DPI` | Resolution in dots per inch (default: 150) |
| `--pages N ...` | 1-based page numbers to export (default: all) |

---

### pdf_from_images.py — Create PDF from images

Combines image files (PNG, JPEG, BMP, TIFF, WebP, etc.) into a single PDF. Each image becomes one page sized to match the image dimensions.

```bash
python pdf_from_images.py output.pdf image1.png image2.jpg image3.png
```

| Argument | Description |
|---|---|
| `output` | Output PDF file |
| `images` | Image files to include, in order |

> Tip: use `pdf_to_images.py` and `pdf_from_images.py` together to edit individual pages as images and reassemble them.

---

### pdf_watermark.py — Stamp text watermark

Adds a semi-transparent text watermark to every page.

```bash
python pdf_watermark.py input.pdf output.pdf "DRAFT"

# Custom appearance
python pdf_watermark.py input.pdf output.pdf "CONFIDENTIAL" \
  --opacity 0.1 --angle 45 --fontsize 72
```

| Argument | Description |
|---|---|
| `input` | Source PDF |
| `output` | Watermarked output PDF |
| `TEXT` | Watermark text |
| `--fontsize PT` | Font size in points (default: 60) |
| `--opacity N` | Opacity 0.0–1.0 (default: 0.15) |
| `--angle DEG` | Counter-clockwise rotation in degrees (default: 45) |
| `--color R G B` | RGB color, each 0.0–1.0 (default: 0.5 0.5 0.5 = gray) |
