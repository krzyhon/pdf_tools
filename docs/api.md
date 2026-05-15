# API Reference

Base URL: `https://pdftools.flairops.cloud/api`

Interactive docs (Swagger UI): `/api/docs`

All endpoints accept `multipart/form-data`. File parameters are uploaded as form file fields; all other parameters are form text fields.

**Standard download response:**
```json
{ "download_url": "<presigned S3 URL, valid 1 hour>", "filename": "result.pdf" }
```

---

## Health

### `GET /api/health`
Returns `200 OK` when the service is running. Used by the ALB health check.

```json
{ "status": "ok" }
```

---

## Organize

### `POST /api/merge`
Combine multiple PDFs into one.

| Field | Type | Required | Description |
|---|---|---|---|
| `files` | file[] | ✅ | Two or more PDF files |

```json
{ "download_url": "...", "filename": "document_merged.pdf", "pages": 12 }
```

---

### `POST /api/split/pages`
Split every page into a separate PDF. Returns a ZIP archive.

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | ✅ | Source PDF |

```json
{ "download_url": "...", "filename": "document_pages.zip", "count": 8 }
```

---

### `POST /api/split/ranges`
Split into sections by page range. Returns a ZIP archive.

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | ✅ | Source PDF |
| `ranges` | string | ✅ | JSON list of `[start, end]` pairs, e.g. `[[1,3],[5,7]]` |
| `names` | string | | JSON list of output filenames (optional) |

```json
{ "download_url": "...", "filename": "document_split.zip", "count": 2 }
```

---

### `POST /api/rotate`
Rotate all or selected pages.

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | ✅ | Source PDF |
| `angle` | integer | ✅ | `90`, `180`, or `270` |
| `pages` | string | | JSON list of 1-based page numbers, e.g. `[1,3]`. Omit for all pages. |

```json
{ "download_url": "...", "filename": "document_rotated.pdf", "pages_rotated": 4 }
```

---

### `POST /api/reorder`
Rearrange pages. Pages may be repeated or omitted.

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | ✅ | Source PDF |
| `page_order` | string | ✅ | JSON list of 1-based page numbers, e.g. `[3,1,2]` |

```json
{ "download_url": "...", "filename": "document_reordered.pdf", "pages": 3 }
```

---

## Enhance

### `POST /api/page-numbers`
Stamp page numbers onto every page (or a subset).

| Field | Type | Default | Description |
|---|---|---|---|
| `file` | file | — | Source PDF |
| `position` | string | `bottom-center` | `bottom-left`, `bottom-center`, `bottom-right`, `top-left`, `top-center`, `top-right` |
| `fmt` | string | `{n}` | Format string. `{n}` = current page, `{N}` = total pages |
| `start` | integer | `1` | Number assigned to the first page |
| `fontsize` | float | `10.0` | Font size in points |
| `pages` | string | | JSON list of 1-based page numbers to stamp. Omit for all. |

```json
{ "download_url": "...", "filename": "document_numbered.pdf", "pages_stamped": 10 }
```

---

### `POST /api/watermark`
Stamp a semi-transparent diagonal text watermark on every page.

| Field | Type | Default | Description |
|---|---|---|---|
| `file` | file | — | Source PDF |
| `text` | string | — | Watermark text |
| `fontsize` | float | `60.0` | Font size in points |
| `opacity` | float | `0.15` | `0.0` (invisible) to `1.0` (opaque) |
| `angle` | float | `45.0` | Counter-clockwise degrees |

```json
{ "download_url": "...", "filename": "document_watermarked.pdf" }
```

---

### `POST /api/bookmarks/list`
List all bookmarks in a PDF.

| Field | Type | Required |
|---|---|---|
| `file` | file | ✅ |

```json
{
  "bookmarks": [
    { "level": 1, "title": "Chapter 1", "page": 1 },
    { "level": 2, "title": "Section 1.1", "page": 3 }
  ]
}
```

---

### `POST /api/bookmarks/add`
Add bookmarks to a PDF.

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | ✅ | Source PDF |
| `bookmarks` | string | ✅ | JSON array of `{level, title, page}` objects |

```json
{ "download_url": "...", "filename": "document_bookmarked.pdf", "added": 3 }
```

---

### `POST /api/bookmarks/remove`
Remove all bookmarks from a PDF.

| Field | Type | Required |
|---|---|---|
| `file` | file | ✅ |

```json
{ "download_url": "...", "filename": "document_no_bookmarks.pdf", "removed": 5 }
```

---

## Convert

### `POST /api/ocr`
Add a searchable text layer to a scanned PDF using Tesseract.

| Field | Type | Default | Description |
|---|---|---|---|
| `file` | file | — | Source PDF or image |
| `language` | string | `eng` | Tesseract language code, e.g. `pol`, `eng+pol` |
| `dpi` | integer | `300` | Render resolution — higher = better quality, slower |

```json
{ "download_url": "...", "filename": "document_ocr.pdf", "pages": 5 }
```

---

### `POST /api/to-images`
Render each page as a PNG or JPEG. Returns a ZIP archive.

| Field | Type | Default | Description |
|---|---|---|---|
| `file` | file | — | Source PDF |
| `fmt` | string | `png` | `png` or `jpeg` |
| `dpi` | integer | `150` | Render resolution |
| `pages` | string | | JSON list of 1-based page numbers. Omit for all. |

```json
{ "download_url": "...", "filename": "document_images.zip", "count": 6 }
```

---

### `POST /api/to-docx`
Convert a PDF to an editable Word document.

| Field | Type | Default | Description |
|---|---|---|---|
| `file` | file | — | Source PDF |
| `start_page` | integer | `1` | First page to convert |
| `end_page` | integer | last | Last page to convert |

```json
{ "download_url": "...", "filename": "document.docx" }
```

---

### `POST /api/from-images`
Combine image files into a single PDF.

| Field | Type | Required | Description |
|---|---|---|---|
| `files` | file[] | ✅ | Images (PNG, JPEG, BMP, TIFF, GIF, WebP) in order |

```json
{ "download_url": "...", "filename": "images_to_pdf.pdf", "pages": 4 }
```

---

## Security

### `POST /api/protect`
Encrypt a PDF with AES-256.

| Field | Type | Required |
|---|---|---|
| `file` | file | ✅ |
| `password` | string | ✅ |

```json
{ "download_url": "...", "filename": "document_protected.pdf" }
```

---

### `POST /api/decrypt`
Remove password protection from a PDF.

| Field | Type | Required |
|---|---|---|
| `file` | file | ✅ |
| `password` | string | ✅ |

```json
{ "download_url": "...", "filename": "document_decrypted.pdf" }
```

---

### `POST /api/redact/text`
Permanently black out all occurrences of specified text terms.

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | ✅ | Source PDF |
| `terms` | string | ✅ | JSON list of strings, e.g. `["John Doe","SSN"]` |

```json
{ "download_url": "...", "filename": "document_redacted.pdf", "redactions": 7 }
```

---

### `POST /api/redact/areas`
Permanently black out rectangular regions by coordinate.

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | ✅ | Source PDF |
| `areas` | string | ✅ | JSON list of `[page, x0, y0, x1, y1]`, e.g. `[[1,10.0,20.0,100.0,50.0]]` |
| `terms` | string | | Optional JSON list of additional text terms to redact |

```json
{ "download_url": "...", "filename": "document_redacted.pdf", "redactions": 3 }
```

> Tip: use `POST /api/inspect` to find coordinates. Copy the `area` field from the response directly into `areas`.

---

## Inspect & Compare

### `POST /api/inspect`
Extract text blocks with bounding box coordinates from a PDF page. Useful for identifying areas to redact.

| Field | Type | Default | Description |
|---|---|---|---|
| `file` | file | — | Source PDF |
| `page_num` | integer | `1` | Page to inspect |
| `search` | string | | Filter blocks containing this keyword |

```json
{
  "page": 1,
  "total_pages": 10,
  "blocks": [
    {
      "page": 1,
      "x0": 72.0, "y0": 100.5, "x1": 400.0, "y1": 120.0,
      "text": "John Doe",
      "area": "1:72.0,100.5,400.0,120.0"
    }
  ]
}
```

---

### `POST /api/diff/report`
Compare two PDFs and return a structured report of differences.

| Field | Type | Required |
|---|---|---|
| `file_a` | file | ✅ |
| `file_b` | file | ✅ |

```json
{
  "pages_a": 5,
  "pages_b": 6,
  "added_pages": [6],
  "removed_pages": [],
  "changed_pages": [2, 4]
}
```

---

### `POST /api/diff/visual`
Produce a visual side-by-side PDF highlighting differences between two PDFs.

| Field | Type | Default | Description |
|---|---|---|---|
| `file_a` | file | — | First PDF |
| `file_b` | file | — | Second PDF |
| `dpi` | integer | `150` | Render resolution |

```json
{ "download_url": "...", "filename": "diff_visual.pdf", "pages_a": 5, "pages_b": 6, ... }
```

---

## Optimize

### `POST /api/compress`
Reduce PDF file size using lossless compression. Optionally downsample embedded images.

| Field | Type | Default | Description |
|---|---|---|---|
| `file` | file | — | Source PDF |
| `image_dpi` | integer | | Downsample images to this DPI. Omit for lossless only. |

```json
{
  "download_url": "...",
  "filename": "document_compressed.pdf",
  "original_bytes": 5242880,
  "compressed_bytes": 2097152,
  "savings_pct": 60.0
}
```

---

## Error responses

All errors return a JSON body with a `detail` field:

```json
{ "detail": "angle must be 90, 180, or 270" }
```

| Status | Meaning |
|---|---|
| `422` | Validation error — invalid parameter value or format |
| `500` | Unexpected server error — check CloudWatch logs |
