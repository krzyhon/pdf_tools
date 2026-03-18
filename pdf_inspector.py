"""PDF inspector — find rectangle coordinates for redaction.

Two modes:

  text   List text blocks on a page with their bounding box coordinates.
         Optionally filter by a search term.

  view   Open an interactive viewer for a page. Move the mouse to see live
         PDF-point coordinates. Click and drag to draw a rectangle — the
         ready-to-use --areas string is printed to the terminal.

Coordinates are in PDF points (1 pt = 1/72 inch) from the top-left corner,
matching the format expected by pdf_redactor.py.

CLI usage:
    # Text mode — all blocks on page 1
    python pdf_inspector.py text input.pdf

    # Text mode — page 3, filter by keyword
    python pdf_inspector.py text input.pdf --page 3 --search "John"

    # View mode — interactive viewer for page 1
    python pdf_inspector.py view input.pdf

    # View mode — jump straight to page 2
    python pdf_inspector.py view input.pdf --page 2
"""

import argparse
import base64
import sys
from pathlib import Path

import fitz  # PyMuPDF


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _open_page(input_path: str, page_num: int) -> tuple[fitz.Document, fitz.Page]:
    if not Path(input_path).exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    doc = fitz.open(input_path)
    total = doc.page_count
    if page_num < 1 or page_num > total:
        raise ValueError(f"Page {page_num} is out of range (document has {total} pages).")
    return doc, doc[page_num - 1]


# ---------------------------------------------------------------------------
# Text mode
# ---------------------------------------------------------------------------

def inspect_text(input_path: str, page_num: int = 1, search: str | None = None) -> None:
    """Print text blocks and their bounding boxes for a given page."""
    doc, page = _open_page(input_path, page_num)
    total = doc.page_count

    print(f"Page {page_num}/{total}  —  size: {page.rect.width:.0f} x {page.rect.height:.0f} pt\n")

    # get_text("blocks") → (x0, y0, x1, y1, text, block_no, block_type)
    blocks = page.get_text("blocks")
    doc.close()

    areas = []
    for x0, y0, x1, y1, text, *_ in blocks:
        text = text.strip()
        if not text:
            continue
        if search and search.lower() not in text.lower():
            continue
        coord = f"{page_num}:{x0:.1f},{y0:.1f},{x1:.1f},{y1:.1f}"
        areas.append(coord)
        preview = text.replace("\n", " ")[:60]
        print(f"  {coord}  # {preview}")

    if not areas:
        msg = "No text blocks found" + (f" matching '{search}'" if search else "")
        print(f"  ({msg})")
        return

    out_stem = Path(input_path).stem
    areas_args = " ".join(f'"{a}"' for a in areas)
    print(f"\npython pdf_redactor.py \"{input_path}\" \"{out_stem}_redacted.pdf\" --areas {areas_args}")


# ---------------------------------------------------------------------------
# View mode
# ---------------------------------------------------------------------------

_ZOOM = 2.0          # render scale: 2× means 144 DPI — crisp on Retina
_RECT_COLOR = "red"
_RECT_WIDTH = 2


def _render_page_png(page: fitz.Page, zoom: float) -> bytes:
    """Render a page to PNG bytes at the given zoom level."""
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    return pix.tobytes("png")


def view_page(input_path: str, page_num: int = 1) -> None:
    """Open an interactive tkinter viewer for the given page."""
    import tkinter as tk

    doc, page = _open_page(input_path, page_num)
    total_pages = doc.page_count
    page_width = page.rect.width
    page_height = page.rect.height

    # State shared across callbacks
    state = {
        "page_num": page_num,
        "drag_start": None,
        "rect_id": None,
        "areas": [],        # accumulated list of "PAGE:x0,y0,x1,y1" strings
    }

    # --- Build UI --------------------------------------------------------
    root = tk.Tk()
    root.title(f"PDF Inspector — {Path(input_path).name}")

    # Top info bar
    info_var = tk.StringVar(value=f"Page {page_num}/{total_pages}  |  {page_width:.0f}×{page_height:.0f} pt  |  Move mouse over page")
    info_label = tk.Label(root, textvariable=info_var, anchor="w",
                          font=("Menlo", 11), bg="#1e1e1e", fg="#d4d4d4", padx=8, pady=4)
    info_label.pack(fill="x")

    # Scrollable canvas
    frame = tk.Frame(root)
    frame.pack(fill="both", expand=True)

    h_scroll = tk.Scrollbar(frame, orient="horizontal")
    v_scroll = tk.Scrollbar(frame, orient="vertical")
    canvas = tk.Canvas(frame, bg="#404040",
                       xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set,
                       cursor="crosshair")
    h_scroll.config(command=canvas.xview)
    v_scroll.config(command=canvas.yview)
    h_scroll.pack(side="bottom", fill="x")
    v_scroll.pack(side="right",  fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    # Bottom output bar
    output_var = tk.StringVar(value="Drag to select an area — the full pdf_redactor.py command will appear here")
    output_label = tk.Label(root, textvariable=output_var, anchor="w",
                            font=("Menlo", 11), bg="#252526", fg="#9cdcfe", padx=8, pady=4)
    output_label.pack(fill="x")

    # --- Page rendering --------------------------------------------------
    img_ref = {}   # keep PhotoImage reference alive

    def load_page(pnum: int) -> None:
        nonlocal page
        doc_page = doc[pnum - 1]
        page = doc_page
        state["page_num"] = pnum

        png_bytes = _render_page_png(doc_page, _ZOOM)
        img = tk.PhotoImage(data=base64.b64encode(png_bytes).decode())
        img_ref["img"] = img  # prevent GC

        canvas.delete("all")
        state["rect_id"] = None
        state["drag_start"] = None

        img_w = img.width()
        img_h = img.height()
        canvas.config(scrollregion=(0, 0, img_w, img_h))
        canvas.create_image(0, 0, anchor="nw", image=img, tags="page")

        root.title(f"PDF Inspector — {Path(input_path).name}  [page {pnum}/{total_pages}]")
        info_var.set(
            f"Page {pnum}/{total_pages}  |  {doc_page.rect.width:.0f}×{doc_page.rect.height:.0f} pt  |  "
            f"Use ← → arrow keys to navigate pages"
        )

    load_page(page_num)

    # --- Coordinate helpers ----------------------------------------------
    def canvas_to_pdf(cx: float, cy: float) -> tuple[float, float]:
        """Convert canvas pixel coords to PDF point coords."""
        return round(cx / _ZOOM, 1), round(cy / _ZOOM, 1)

    def canvas_xy(event) -> tuple[float, float]:
        """Canvas coords accounting for scroll offset."""
        return canvas.canvasx(event.x), canvas.canvasy(event.y)

    # --- Mouse callbacks -------------------------------------------------
    def on_motion(event):
        cx, cy = canvas_xy(event)
        px, py = canvas_to_pdf(cx, cy)
        info_var.set(
            f"Page {state['page_num']}/{total_pages}  |  "
            f"x={px:.1f}  y={py:.1f} pt  |  "
            f"Drag to draw rectangle  |  ← → to navigate"
        )

    def on_press(event):
        state["drag_start"] = canvas_xy(event)
        if state["rect_id"]:
            canvas.delete(state["rect_id"])
            state["rect_id"] = None

    def on_drag(event):
        if not state["drag_start"]:
            return
        x0, y0 = state["drag_start"]
        x1, y1 = canvas_xy(event)
        if state["rect_id"]:
            canvas.delete(state["rect_id"])
        state["rect_id"] = canvas.create_rectangle(
            x0, y0, x1, y1,
            outline=_RECT_COLOR, width=_RECT_WIDTH, tags="rect"
        )

    def on_release(event):
        if not state["drag_start"]:
            return
        cx0, cy0 = state["drag_start"]
        cx1, cy1 = canvas_xy(event)
        state["drag_start"] = None

        # Normalise so x0<x1, y0<y1
        px0, py0 = canvas_to_pdf(min(cx0, cx1), min(cy0, cy1))
        px1, py1 = canvas_to_pdf(max(cx0, cx1), max(cy0, cy1))

        if abs(px1 - px0) < 2 and abs(py1 - py0) < 2:
            # Tiny click, not a real drag — ignore
            return

        pnum = state["page_num"]
        state["areas"].append(f"{pnum}:{px0},{py0},{px1},{py1}")

        out_stem = Path(input_path).stem
        areas_args = " ".join(f'"{a}"' for a in state["areas"])
        command = f'python pdf_redactor.py "{input_path}" "{out_stem}_redacted.pdf" --areas {areas_args}'
        output_var.set(command)
        print(command)

    canvas.bind("<Motion>",         on_motion)
    canvas.bind("<ButtonPress-1>",  on_press)
    canvas.bind("<B1-Motion>",      on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)

    # --- Keyboard navigation ---------------------------------------------
    def on_key(event):
        pnum = state["page_num"]
        if event.keysym in ("Right", "Next") and pnum < total_pages:
            load_page(pnum + 1)
        elif event.keysym in ("Left", "Prior") and pnum > 1:
            load_page(pnum - 1)

    root.bind("<Key>", on_key)
    root.focus_set()

    root.mainloop()
    doc.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect a PDF to find rectangle coordinates for redaction.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python pdf_inspector.py text input.pdf\n"
            "  python pdf_inspector.py text input.pdf --page 2 --search 'John'\n"
            "  python pdf_inspector.py view input.pdf\n"
            "  python pdf_inspector.py view input.pdf --page 3"
        ),
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    # text subcommand
    t = sub.add_parser("text", help="List text blocks with bounding box coordinates.")
    t.add_argument("input", help="Source PDF file.")
    t.add_argument("--page", type=int, default=1, metavar="N", help="Page number (default: 1).")
    t.add_argument("--search", metavar="TERM", help="Filter blocks containing this text.")

    # view subcommand
    v = sub.add_parser("view", help="Interactive viewer — drag to get rectangle coordinates.")
    v.add_argument("input", help="Source PDF file.")
    v.add_argument("--page", type=int, default=1, metavar="N", help="Starting page (default: 1).")

    args = parser.parse_args()

    try:
        if args.mode == "text":
            inspect_text(args.input, page_num=args.page, search=args.search)
        else:
            view_page(args.input, page_num=args.page)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
