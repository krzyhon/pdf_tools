# PDF Tools

A collection of command-line Python utilities for common PDF operations.

## Requirements

```
pip install -r requirements.txt
```

Dependencies: `pypdf`, `pymupdf`, `tqdm`, `cryptography`

---

## Tools

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
