'use strict';

// ── Tool definitions ──────────────────────────────────────────────────────────

const TOOLS = [
  // Organize
  {
    id: 'merge', category: 'Organize', icon: '⊕',
    title: 'Merge PDFs', desc: 'Combine multiple PDFs into one document',
    endpoint: '/api/merge', fileField: 'files', multiFile: true, accept: '.pdf',
    params: [], result: 'download',
  },
  {
    id: 'split-pages', category: 'Organize', icon: '✂',
    title: 'Split into Pages', desc: 'Extract each page as a separate PDF (ZIP)',
    endpoint: '/api/split/pages', accept: '.pdf',
    params: [], result: 'download',
  },
  {
    id: 'split-ranges', category: 'Organize', icon: '✂',
    title: 'Split by Ranges', desc: 'Cut into sections by page range (ZIP)',
    endpoint: '/api/split/ranges', accept: '.pdf',
    params: [
      { name: 'ranges', label: 'Page ranges', type: 'ranges', required: true,
        placeholder: '1-3, 5-7, 9-9', help: 'Comma-separated ranges, e.g. 1-3, 5-7' },
    ],
    result: 'download',
  },
  {
    id: 'rotate', category: 'Organize', icon: '↺',
    title: 'Rotate Pages', desc: 'Rotate all or selected pages',
    endpoint: '/api/rotate', accept: '.pdf',
    params: [
      { name: 'angle', label: 'Angle', type: 'select', options: ['90','180','270'], default: '90' },
      { name: 'pages', label: 'Pages (optional)', type: 'pages-list',
        placeholder: 'e.g. 1, 3, 5 — blank = all pages' },
    ],
    result: 'download',
  },
  {
    id: 'reorder', category: 'Organize', icon: '↕',
    title: 'Reorder Pages', desc: 'Rearrange pages in any order',
    endpoint: '/api/reorder', accept: '.pdf',
    params: [
      { name: 'page_order', label: 'New page order', type: 'pages-list', required: true,
        placeholder: 'e.g. 3, 1, 2', help: '1-based. Pages may be repeated or omitted.' },
    ],
    result: 'download',
  },
  // Enhance
  {
    id: 'page-numbers', category: 'Enhance', icon: '#',
    title: 'Add Page Numbers', desc: 'Stamp page numbers onto every page',
    endpoint: '/api/page-numbers', accept: '.pdf',
    params: [
      { name: 'position', label: 'Position', type: 'select', default: 'bottom-center',
        options: ['bottom-center','bottom-left','bottom-right','top-center','top-left','top-right'] },
      { name: 'fmt', label: 'Format', type: 'text', default: '{n}',
        placeholder: '{n} of {N}', help: '{n} = current page, {N} = total pages' },
      { name: 'start', label: 'Start number', type: 'number', default: '1' },
      { name: 'fontsize', label: 'Font size', type: 'number', default: '10' },
    ],
    result: 'download',
  },
  {
    id: 'watermark', category: 'Enhance', icon: '◈',
    title: 'Add Watermark', desc: 'Stamp diagonal text watermark on every page',
    endpoint: '/api/watermark', accept: '.pdf',
    params: [
      { name: 'text', label: 'Watermark text', type: 'text', required: true, placeholder: 'CONFIDENTIAL' },
      { name: 'fontsize', label: 'Font size', type: 'number', default: '60' },
      { name: 'opacity', label: 'Opacity (0–1)', type: 'number', default: '0.15', step: '0.05' },
      { name: 'angle', label: 'Angle °', type: 'number', default: '45' },
    ],
    result: 'download',
  },
  {
    id: 'bookmarks-add', category: 'Enhance', icon: '🔖',
    title: 'Add Bookmarks', desc: 'Add a table of contents to a PDF',
    endpoint: '/api/bookmarks/add', accept: '.pdf',
    params: [
      { name: 'bookmarks', label: 'Bookmarks (JSON)', type: 'textarea', required: true, rows: 6,
        placeholder: '[{"level":1,"title":"Chapter 1","page":1},\n {"level":2,"title":"Section 1.1","page":3}]',
        help: 'JSON array: level (1 = top), title, page (1-based)' },
    ],
    result: 'download',
  },
  {
    id: 'bookmarks-remove', category: 'Enhance', icon: '✖',
    title: 'Remove Bookmarks', desc: 'Strip all bookmarks from a PDF',
    endpoint: '/api/bookmarks/remove', accept: '.pdf',
    params: [], result: 'download',
  },
  {
    id: 'bookmarks-list', category: 'Enhance', icon: '📋',
    title: 'List Bookmarks', desc: 'View all bookmarks in a PDF',
    endpoint: '/api/bookmarks/list', accept: '.pdf',
    params: [], result: 'json', jsonField: 'bookmarks',
  },
  // Convert
  {
    id: 'ocr', category: 'Convert', icon: '🔍',
    title: 'OCR — Make Searchable', desc: 'Add a text layer to a scanned PDF',
    endpoint: '/api/ocr', accept: '.pdf',
    params: [
      { name: 'language', label: 'Language', type: 'select', default: 'eng',
        options: ['eng','pol','eng+pol','deu','fra','spa','ita'] },
      { name: 'dpi', label: 'Render DPI', type: 'number', default: '300',
        help: 'Higher = better quality, slower processing' },
    ],
    result: 'download',
  },
  {
    id: 'to-images', category: 'Convert', icon: '🖼',
    title: 'PDF to Images', desc: 'Render each page as PNG or JPEG (ZIP)',
    endpoint: '/api/to-images', accept: '.pdf',
    params: [
      { name: 'fmt', label: 'Format', type: 'select', options: ['png','jpeg'], default: 'png' },
      { name: 'dpi', label: 'DPI', type: 'number', default: '150' },
      { name: 'pages', label: 'Pages (optional)', type: 'pages-list',
        placeholder: 'e.g. 1, 3, 5 — blank = all pages' },
    ],
    result: 'download',
  },
  {
    id: 'to-docx', category: 'Convert', icon: '📝',
    title: 'PDF to DOCX', desc: 'Convert to an editable Word document',
    endpoint: '/api/to-docx', accept: '.pdf',
    params: [
      { name: 'start_page', label: 'Start page', type: 'number', default: '1' },
      { name: 'end_page', label: 'End page (optional)', type: 'number', placeholder: 'Default: last page' },
    ],
    result: 'download',
  },
  {
    id: 'from-images', category: 'Convert', icon: '📑',
    title: 'Images to PDF', desc: 'Combine images into a single PDF',
    endpoint: '/api/from-images', fileField: 'files', multiFile: true,
    accept: '.png,.jpg,.jpeg,.bmp,.tiff,.gif,.webp',
    params: [], result: 'download',
  },
  // Security
  {
    id: 'protect', category: 'Security', icon: '🔒',
    title: 'Protect (Encrypt)', desc: 'Password-protect a PDF with AES-256',
    endpoint: '/api/protect', accept: '.pdf',
    params: [
      { name: 'password', label: 'Password', type: 'password', required: true },
    ],
    result: 'download',
  },
  {
    id: 'decrypt', category: 'Security', icon: '🔓',
    title: 'Remove Password', desc: 'Unlock a password-protected PDF',
    endpoint: '/api/decrypt', accept: '.pdf',
    params: [
      { name: 'password', label: 'Current password', type: 'password', required: true },
    ],
    result: 'download',
  },
  {
    id: 'redact-text', category: 'Security', icon: '■',
    title: 'Redact Text', desc: 'Permanently black out text by keyword',
    endpoint: '/api/redact/text', accept: '.pdf',
    params: [
      { name: 'terms', label: 'Terms to redact', type: 'terms', required: true, rows: 5,
        placeholder: 'One term per line\nJohn Doe\n123-45-6789',
        help: 'One search term per line — redaction is permanent and irreversible' },
    ],
    result: 'download',
  },
  {
    id: 'redact-areas', category: 'Security', icon: '▪',
    title: 'Redact Areas', desc: 'Black out specific rectangular regions by coordinate',
    endpoint: '/api/redact/areas', accept: '.pdf',
    params: [
      { name: 'areas', label: 'Areas (JSON)', type: 'textarea', required: true, rows: 4,
        placeholder: '[[1, 10.0, 20.0, 100.0, 50.0]]',
        help: 'Use the Inspect tool to find coordinates. Format: [[page, x0, y0, x1, y1], ...]' },
      { name: 'terms', label: 'Also redact text (optional)', type: 'terms', rows: 3,
        placeholder: 'One term per line' },
    ],
    result: 'download',
  },
  // Inspect
  {
    id: 'inspect', category: 'Inspect', icon: '🔎',
    title: 'Inspect Text', desc: 'Find text blocks and coordinates (useful for redaction)',
    endpoint: '/api/inspect', accept: '.pdf',
    params: [
      { name: 'page_num', label: 'Page', type: 'number', default: '1' },
      { name: 'search', label: 'Filter by keyword (optional)', type: 'text', placeholder: '' },
    ],
    result: 'blocks',
  },
  {
    id: 'diff-report', category: 'Inspect', icon: '≠',
    title: 'Diff Report', desc: 'Compare two PDFs and list changed pages',
    endpoint: '/api/diff/report', twoFiles: true, accept: '.pdf',
    params: [], result: 'diff',
  },
  {
    id: 'diff-visual', category: 'Inspect', icon: '👁',
    title: 'Visual Diff', desc: 'Render a visual diff of two PDFs as a new PDF',
    endpoint: '/api/diff/visual', twoFiles: true, accept: '.pdf',
    params: [{ name: 'dpi', label: 'DPI', type: 'number', default: '150' }],
    result: 'download',
  },
  // Optimize
  {
    id: 'compress', category: 'Optimize', icon: '📦',
    title: 'Compress', desc: 'Reduce file size without visual quality loss',
    endpoint: '/api/compress', accept: '.pdf',
    params: [
      { name: 'image_dpi', label: 'Downsample images to DPI (optional)', type: 'number',
        placeholder: 'e.g. 150 for aggressive compression',
        help: 'Leave blank for lossless compression only' },
    ],
    result: 'download',
    resultMeta: (d) => `Saved ${d.savings_pct}% · ${fmtBytes(d.original_bytes)} → ${fmtBytes(d.compressed_bytes)}`,
  },
];

// ── Utilities ─────────────────────────────────────────────────────────────────

function fmtBytes(n) {
  if (n < 1024) return `${n} B`;
  if (n < 1048576) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1048576).toFixed(1)} MB`;
}

function byId(id) { return document.getElementById(id); }

function copyText(text) {
  navigator.clipboard.writeText(text).catch(() => {});
}

// ── Render tool cards ─────────────────────────────────────────────────────────

function renderApp() {
  const app = byId('app');
  const categories = [...new Set(TOOLS.map(t => t.category))];

  categories.forEach(cat => {
    const tools = TOOLS.filter(t => t.category === cat);
    const section = document.createElement('section');
    section.className = 'category';
    section.innerHTML = `<h2 class="category-title">${cat}</h2><div class="cards"></div>`;
    const grid = section.querySelector('.cards');

    tools.forEach(tool => {
      const card = document.createElement('div');
      card.className = 'card';
      card.dataset.id = tool.id;
      card.innerHTML = `
        <div class="card-icon">${tool.icon}</div>
        <div class="card-title">${tool.title}</div>
        <div class="card-desc">${tool.desc}</div>`;
      card.addEventListener('click', () => openModal(tool.id));
      grid.appendChild(card);
    });

    app.appendChild(section);
  });
}

// ── Modal ─────────────────────────────────────────────────────────────────────

function openModal(toolId) {
  const tool = TOOLS.find(t => t.id === toolId);
  if (!tool) return;

  byId('modal-icon').textContent = tool.icon;
  byId('modal-title').textContent = tool.title;
  byId('modal-desc').textContent = tool.desc;
  byId('modal-body').innerHTML = buildForm(tool);

  setupDropzones(tool);
  setupSubmit(tool);

  byId('overlay').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeModal() {
  byId('overlay').classList.add('hidden');
  document.body.style.overflow = '';
}

// ── Form builder ──────────────────────────────────────────────────────────────

function buildForm(tool) {
  let html = '';

  if (tool.twoFiles) {
    html += `
      <div class="two-files">
        <div>
          <p class="file-label">File A</p>
          ${dropzoneHtml('file_a', tool.accept, false)}
        </div>
        <div>
          <p class="file-label">File B</p>
          ${dropzoneHtml('file_b', tool.accept, false)}
        </div>
      </div>`;
  } else {
    html += dropzoneHtml(tool.fileField || 'file', tool.accept, !!tool.multiFile);
  }

  tool.params.forEach(p => { html += fieldHtml(p); });

  html += `<button class="btn btn-primary" id="submit-btn" type="button">Process</button>`;
  html += `<div id="result-area"></div>`;
  return html;
}

function dropzoneHtml(name, accept, multi) {
  const multiAttr = multi ? 'multiple' : '';
  const label = multi ? 'Click to upload files or drag & drop' : 'Click to upload or drag & drop';
  return `
    <div class="dropzone" id="dz-${name}">
      <input type="file" id="file-${name}" name="${name}" accept="${accept}" ${multiAttr} />
      <div class="dropzone-icon">📄</div>
      <div class="dropzone-label">${label}</div>
      <div class="dropzone-sub">${accept.replace(/\./g, '').toUpperCase().replace(/,/g, ' / ')}</div>
      <div class="dropzone-files" id="dz-files-${name}"></div>
    </div>`;
}

function fieldHtml(p) {
  const req = p.required ? 'required' : '';
  const val = p.default ? `value="${p.default}"` : '';
  const ph = p.placeholder ? `placeholder="${p.placeholder}"` : '';
  const step = p.step ? `step="${p.step}"` : '';
  let input = '';

  if (p.type === 'select') {
    const opts = p.options.map(o =>
      `<option value="${o}" ${o === (p.default || p.options[0]) ? 'selected' : ''}>${o}</option>`
    ).join('');
    input = `<select name="${p.name}" id="f-${p.name}">${opts}</select>`;
  } else if (p.type === 'textarea' || p.type === 'terms') {
    input = `<textarea name="${p.name}" id="f-${p.name}" rows="${p.rows || 4}" ${ph} ${req}></textarea>`;
  } else {
    const t = p.type === 'pages-list' || p.type === 'ranges' ? 'text' : p.type;
    input = `<input type="${t}" name="${p.name}" id="f-${p.name}" ${val} ${ph} ${step} ${req} />`;
  }

  const help = p.help ? `<div class="help">${p.help}</div>` : '';
  return `<div class="form-group"><label for="f-${p.name}">${p.label}</label>${input}${help}</div>`;
}

// ── Dropzone setup ────────────────────────────────────────────────────────────

function setupDropzones(tool) {
  const names = tool.twoFiles ? ['file_a', 'file_b'] : [tool.fileField || 'file'];

  names.forEach(name => {
    const dz = byId(`dz-${name}`);
    const input = byId(`file-${name}`);
    if (!dz || !input) return;

    dz.addEventListener('click', () => input.click());
    input.addEventListener('change', () => updateFileLabel(name, input.files));

    dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag-over'); });
    dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
    dz.addEventListener('drop', e => {
      e.preventDefault();
      dz.classList.remove('drag-over');
      const dt = new DataTransfer();
      Array.from(e.dataTransfer.files).forEach(f => dt.items.add(f));
      input.files = dt.files;
      updateFileLabel(name, input.files);
    });
  });
}

function updateFileLabel(name, files) {
  const el = byId(`dz-files-${name}`);
  if (!el) return;
  if (!files || files.length === 0) { el.textContent = ''; return; }
  if (files.length === 1) {
    el.textContent = `${files[0].name} (${fmtBytes(files[0].size)})`;
  } else {
    el.textContent = `${files.length} files selected`;
  }
}

// ── Form submission ───────────────────────────────────────────────────────────

function setupSubmit(tool) {
  byId('submit-btn').addEventListener('click', () => handleSubmit(tool));
}

async function handleSubmit(tool) {
  const btn = byId('submit-btn');
  const resultArea = byId('result-area');

  // Validate file(s)
  const fileNames = tool.twoFiles ? ['file_a', 'file_b'] : [tool.fileField || 'file'];
  for (const name of fileNames) {
    const input = byId(`file-${name}`);
    if (!input || input.files.length === 0) {
      resultArea.innerHTML = `<div class="error-box">Please select a file${tool.twoFiles ? ` for ${name === 'file_a' ? 'File A' : 'File B'}` : ''}.</div>`;
      return;
    }
  }

  btn.disabled = true;
  btn.innerHTML = `<span class="spinner"></span> Processing…`;
  resultArea.innerHTML = '';

  try {
    const fd = buildFormData(tool);
    const res = await fetch(tool.endpoint, { method: 'POST', body: fd });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || `Server error ${res.status}`);
    }

    showResult(tool, data, resultArea);
  } catch (err) {
    resultArea.innerHTML = `<div class="error-box">Error: ${err.message}</div>`;
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Process';
  }
}

function buildFormData(tool) {
  const fd = new FormData();

  // Files
  if (tool.twoFiles) {
    fd.append('file_a', byId('file-file_a').files[0]);
    fd.append('file_b', byId('file-file_b').files[0]);
  } else {
    const name = tool.fileField || 'file';
    const input = byId(`file-${name}`);
    if (tool.multiFile) {
      Array.from(input.files).forEach(f => fd.append(name, f));
    } else {
      fd.append(name, input.files[0]);
    }
  }

  // Parameters
  tool.params.forEach(p => {
    const el = byId(`f-${p.name}`);
    if (!el) return;
    const val = el.value.trim();

    if (!val) return; // skip empty optional fields

    if (p.type === 'pages-list') {
      const nums = val.split(',').map(s => parseInt(s.trim(), 10)).filter(n => !isNaN(n));
      if (nums.length) fd.append(p.name, JSON.stringify(nums));
    } else if (p.type === 'ranges') {
      const pairs = val.split(',').map(s => {
        const [a, b] = s.trim().split('-').map(n => parseInt(n.trim(), 10));
        return [a, b];
      }).filter(([a, b]) => !isNaN(a) && !isNaN(b));
      if (pairs.length) fd.append(p.name, JSON.stringify(pairs));
    } else if (p.type === 'terms') {
      const terms = val.split('\n').map(l => l.trim()).filter(l => l);
      if (terms.length) fd.append(p.name, JSON.stringify(terms));
    } else {
      fd.append(p.name, val);
    }
  });

  return fd;
}

// ── Result rendering ──────────────────────────────────────────────────────────

function showResult(tool, data, container) {
  let html = '<div class="result">';

  if (tool.result === 'download') {
    const meta = tool.resultMeta ? `<div class="result-meta">${tool.resultMeta(data)}</div>` : '';
    html += `
      ${meta}
      <a class="btn btn-download" href="${data.download_url}" download="${data.filename}">
        ⬇ Download ${data.filename}
      </a>
      <p class="result-notice">Link expires in 1 hour</p>`;

  } else if (tool.result === 'json') {
    const items = data[tool.jsonField] || data;
    if (!items || items.length === 0) {
      html += `<p class="result-meta">No ${tool.jsonField} found.</p>`;
    } else {
      html += `<div class="result-json">${JSON.stringify(items, null, 2)}</div>`;
    }

  } else if (tool.result === 'blocks') {
    const blocks = data.blocks || [];
    html += `<p class="result-meta">Page ${data.page} of ${data.total_pages} — ${blocks.length} block(s) found</p>`;
    if (blocks.length === 0) {
      html += `<p style="font-size:13px;color:#64748b;text-align:center">No text blocks found</p>`;
    } else {
      html += `
        <table class="blocks-table">
          <thead><tr><th>Coordinates</th><th>Text</th></tr></thead>
          <tbody>
            ${blocks.map(b => `
              <tr>
                <td>
                  <span class="area-code" title="Click to copy" onclick="copyText('${b.area}')">${b.area}</span>
                </td>
                <td><span class="text-preview" title="${escHtml(b.text)}">${escHtml(b.text)}</span></td>
              </tr>`).join('')}
          </tbody>
        </table>
        <p class="help" style="margin-top:8px">Click a coordinate to copy — paste it into Redact Areas</p>`;
    }

  } else if (tool.result === 'diff') {
    const added   = (data.added_pages   || []).join(', ') || 'none';
    const removed = (data.removed_pages || []).join(', ') || 'none';
    const changed = (data.changed_pages || []).join(', ') || 'none';
    html += `
      <div class="diff-summary">
        <div class="diff-stat"><div class="diff-stat-val">${data.pages_a}</div><div class="diff-stat-label">Pages in A</div></div>
        <div class="diff-stat"><div class="diff-stat-val">${data.pages_b}</div><div class="diff-stat-label">Pages in B</div></div>
      </div>
      <div class="diff-pages">Added pages: <span>${added}</span></div>
      <div class="diff-pages">Removed pages: <span>${removed}</span></div>
      <div class="diff-pages">Changed pages: <span>${changed}</span></div>`;
  }

  html += '</div>';
  container.innerHTML = html;
}

function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Init ──────────────────────────────────────────────────────────────────────

byId('overlay').addEventListener('click', e => { if (e.target === byId('overlay')) closeModal(); });
byId('modal-close').addEventListener('click', closeModal);
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });

renderApp();
