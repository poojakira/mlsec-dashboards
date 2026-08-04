/**
 * mlsec-dashboards — Shared Nav + Interaction Utilities v2.0
 * Include once per page. No dependencies required.
 */

/* ── Animated counters ─────────────────────────────────── */
function animateCounter(el, target, duration = 1200, suffix = '') {
  const start = performance.now();
  const isFloat = String(target).includes('.');
  const decimals = isFloat ? (String(target).split('.')[1] || '').length : 0;
  const from = 0;

  function update(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const ease = 1 - Math.pow(1 - progress, 4); // easeOutQuart
    const current = from + (target - from) * ease;
    el.textContent = current.toFixed(decimals) + suffix;
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

function initCounters() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !entry.target.dataset.animated) {
        entry.target.dataset.animated = '1';
        const raw = entry.target.dataset.target || entry.target.textContent;
        const suffix = entry.target.dataset.suffix || '';
        const val = parseFloat(raw.replace(/[^0-9.]/g, ''));
        if (!isNaN(val)) animateCounter(entry.target, val, 1100, suffix);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.3 });

  document.querySelectorAll('.ds-counter').forEach(el => observer.observe(el));
}

/* ── Bar chart animation ────────────────────────────────── */
function initBars() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.querySelectorAll('.ds-bar-fill').forEach(bar => {
          const target = bar.dataset.width || '0';
          setTimeout(() => { bar.style.width = target; }, 100);
        });
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.2 });

  document.querySelectorAll('.ds-bar-group').forEach(g => observer.observe(g));
}

/* ── Filterable table ───────────────────────────────────── */
function initFilterTable(tableId, inputId, selectId) {
  const table  = document.getElementById(tableId);
  const input  = document.getElementById(inputId);
  const select = document.getElementById(selectId);
  if (!table) return;

  function filter() {
    const q   = (input  ? input.value.toLowerCase()  : '');
    const cat = (select ? select.value.toLowerCase() : '');
    const rows = table.querySelectorAll('tbody tr');
    let visible = 0;

    rows.forEach(row => {
      const text = row.textContent.toLowerCase();
      const matchQ   = !q   || text.includes(q);
      const matchCat = !cat || row.dataset.category === cat || cat === 'all';
      const show = matchQ && matchCat;
      row.classList.toggle('hidden', !show);
      if (show) visible++;
    });

    const counter = document.getElementById(tableId + '-count');
    if (counter) counter.textContent = visible;
  }

  if (input)  input.addEventListener('input', filter);
  if (select) select.addEventListener('change', filter);
}

/* ── Column sort ────────────────────────────────────────── */
function initSortableTable(tableId) {
  const table = document.getElementById(tableId);
  if (!table) return;

  table.querySelectorAll('thead th[data-sort]').forEach((th, colIdx) => {
    th.addEventListener('click', () => {
      const dir = th.dataset.sortDir === 'asc' ? 'desc' : 'asc';
      table.querySelectorAll('thead th').forEach(t => {
        t.classList.remove('sorted-asc','sorted-desc');
        delete t.dataset.sortDir;
      });
      th.dataset.sortDir = dir;
      th.classList.add(dir === 'asc' ? 'sorted-asc' : 'sorted-desc');

      const tbody = table.querySelector('tbody');
      const rows  = Array.from(tbody.querySelectorAll('tr'));
      const type  = th.dataset.sort;

      rows.sort((a, b) => {
        const aVal = a.cells[colIdx]?.textContent.trim() ?? '';
        const bVal = b.cells[colIdx]?.textContent.trim() ?? '';
        let cmp = 0;
        if (type === 'num') {
          cmp = (parseFloat(aVal) || 0) - (parseFloat(bVal) || 0);
        } else {
          cmp = aVal.localeCompare(bVal);
        }
        return dir === 'asc' ? cmp : -cmp;
      });

      rows.forEach(r => tbody.appendChild(r));
    });
  });
}

/* ── Tab switching ──────────────────────────────────────── */
function initTabs(containerSelector) {
  document.querySelectorAll(containerSelector || '.ds-tabs').forEach(tabGroup => {
    tabGroup.querySelectorAll('.ds-tab').forEach(tab => {
      tab.addEventListener('click', () => {
        const paneId = tab.dataset.pane;
        const parent = tab.closest('.ds-tab-container') || document;

        tabGroup.querySelectorAll('.ds-tab').forEach(t => t.classList.remove('active'));
        tab.classList.add('active');

        parent.querySelectorAll('.ds-tab-pane').forEach(p => p.classList.remove('active'));
        const pane = document.getElementById(paneId);
        if (pane) pane.classList.add('active');
      });
    });
  });
}

/* ── Live scan input (HF scanner) ──────────────────────── */
function initLiveScanner(inputId, outputId) {
  const input  = document.getElementById(inputId);
  const output = document.getElementById(outputId);
  if (!input || !output) return;

  const PATTERNS = [
    { re: /pickle\.load/i,       name: 'Unsafe pickle.load',        sev: 'CRITICAL', cve: 'CVE-2023-35828' },
    { re: /exec\s*\(/i,          name: 'Arbitrary exec()',           sev: 'CRITICAL', cve: 'CWE-78' },
    { re: /eval\s*\(/i,          name: 'Code eval()',                sev: 'HIGH',     cve: 'CWE-95' },
    { re: /os\.system\s*\(/i,    name: 'os.system() call',          sev: 'HIGH',     cve: 'CWE-78' },
    { re: /subprocess/i,         name: 'subprocess usage',           sev: 'HIGH',     cve: 'CWE-88' },
    { re: /requests\.get/i,      name: 'Outbound HTTP request',      sev: 'MEDIUM',   cve: '' },
    { re: /open\s*\(.*['"]\s*w/, name: 'File write attempt',         sev: 'MEDIUM',   cve: '' },
    { re: /__reduce__/i,         name: 'Pickle __reduce__ override', sev: 'CRITICAL', cve: 'CVE-2023-48022' },
    { re: /socket\./i,           name: 'Raw socket usage',           sev: 'HIGH',     cve: '' },
    { re: /base64\.b64decode/i,  name: 'Base64 decode (evasion?)',   sev: 'MEDIUM',   cve: '' },
  ];

  const SEV_ORDER = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };

  function scan(code) {
    const findings = PATTERNS
      .filter(p => p.re.test(code))
      .sort((a, b) => SEV_ORDER[a.sev] - SEV_ORDER[b.sev]);

    if (findings.length === 0) {
      output.innerHTML = `<div style="color:var(--green);font-size:.85rem;padding:8px 0">
        ✓ No patterns matched. (Note: full scan requires CLI — AST engine only runs server-side.)
      </div>`;
      return;
    }

    const rows = findings.map(f => `
      <tr>
        <td class="mono">${escHtml(f.name)}</td>
        <td><span class="badge badge-${f.sev.toLowerCase()}">${f.sev}</span></td>
        <td class="mono muted">${f.cve || '—'}</td>
      </tr>`).join('');

    output.innerHTML = `
      <p style="font-size:.78rem;color:var(--muted);margin-bottom:8px">
        ${findings.length} pattern${findings.length>1?'s':''} matched
        <span style="color:var(--dim);font-size:.72rem">(client-side AST patterns only — not full scan)</span>
      </p>
      <div class="ds-table-wrap">
        <table class="ds-table">
          <thead><tr>
            <th>Finding</th><th>Severity</th><th>Reference</th>
          </tr></thead>
          <tbody>${rows}</tbody>
        </table>
      </div>`;
  }

  let timer;
  input.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => scan(input.value), 400);
  });
}

/* ── Escape HTML ────────────────────────────────────────── */
function escHtml(str) {
  return String(str)
    .replace(/&/g,'&amp;')
    .replace(/</g,'&lt;')
    .replace(/>/g,'&gt;')
    .replace(/"/g,'&quot;');
}

/* ── Auto-init on DOMContentLoaded ─────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initCounters();
  initBars();
  initTabs();
});
