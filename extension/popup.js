/**
 * Popup JS - Sarcasm Detector
 * Fixed: filter shows tone distribution, better bar chart, richer CSV export.
 */

// ─── State ───────────────────────────────────────────────────────────────────

let currentStats = null;
let currentPlatform = null;
let currentFilter = 'all';

// ─── DOM refs ────────────────────────────────────────────────────────────────

const btnScan         = document.getElementById('btn-scan');
const btnExport       = document.getElementById('btn-export');
const btnClearSession = document.getElementById('btn-clear-session');
const platformBadge   = document.getElementById('platform-badge');
const filterButtons   = document.querySelectorAll('.btn-filter');

const stateLoading  = document.getElementById('state-loading');
const stateEmpty    = document.getElementById('state-empty');
const stateError    = document.getElementById('state-error');
const stateResults  = document.getElementById('state-results');
const errorText     = document.getElementById('error-text');

const statTotal = document.getElementById('stat-total');
const statPct   = document.getElementById('stat-pct');
const statAvg   = document.getElementById('stat-avg');

const donutFill            = document.getElementById('donut-fill');
const donutPct             = document.getElementById('donut-pct');
const legendPrimaryLabel   = document.getElementById('legend-primary-label');
const legendSecondaryLabel = document.getElementById('legend-secondary-label');
const legendSarcasticN     = document.getElementById('legend-sarcastic-n');
const legendNormalN        = document.getElementById('legend-normal-n');

const barChart  = document.getElementById('bar-chart');
const topList   = document.getElementById('top-list');
const topLabel  = document.getElementById('top-label');
const exportHint = document.getElementById('export-hint');

// ─── Helpers ─────────────────────────────────────────────────────────────────

function showState(name) {
  stateLoading.style.display = name === 'loading' ? 'flex' : 'none';
  stateEmpty.style.display   = name === 'empty'   ? 'flex' : 'none';
  stateError.style.display   = name === 'error'   ? 'flex' : 'none';
  stateResults.style.display = name === 'results' ? 'block' : 'none';
}

function setPlatformBadge(platform) {
  const labels = { reddit: 'Reddit', youtube: 'YouTube' };
  platformBadge.textContent    = labels[platform] || platform || '—';
  platformBadge.dataset.platform = platform || '';
}

function formatToneLabel(label) {
  if (!label) return '—';
  return label.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ─── Tone colour map ─────────────────────────────────────────────────────────

const TONE_COLORS = {
  humorous:    '#22c55e',
  mocking:     '#fb923c',
  insulting:   '#ef4444',
  sarcastic:   '#f97316',
  'light-hearted': '#a78bfa',
  'heavy-hearted': '#f472b6',
  neutral:     '#6b7280',
  unknown:     '#9ca3af',
};

function toneColor(label) {
  if (!label) return '#9ca3af';
  const key = label.toLowerCase().replace(/\s+/g, '-');
  return TONE_COLORS[key] || '#f97316';
}

// ─── Donut chart ─────────────────────────────────────────────────────────────

function updateDonut(pct, label) {
  const circumference = 2 * Math.PI * 46;
  const filled = (pct / 100) * circumference;
  donutFill.setAttribute('stroke-dasharray', `${filled.toFixed(1)} ${circumference.toFixed(1)}`);
  donutFill.style.stroke = toneColor(label);
  donutPct.textContent   = `${Math.round(pct)}`;

  const centerLabel = document.querySelector('.donut-center-label');
  if (centerLabel) centerLabel.textContent = formatToneLabel(label).toLowerCase();
}

// ─── Tone distribution bar chart (replaces score histogram) ──────────────────

/**
 * When filter === 'all'  → horizontal stacked bar showing all tone label counts.
 * When filter === 'sarcastic' → same but only non-neutral items.
 */
function buildBarChart(filteredData) {
  barChart.innerHTML = '';

  if (!filteredData || filteredData.length === 0) return;

  // Count by tone_label
  const counts = {};
  filteredData.forEach(c => {
    const lbl = (c.tone_label || c.dominant_label || 'unknown').toLowerCase();
    counts[lbl] = (counts[lbl] || 0) + 1;
  });

  const total = filteredData.length;
  const entries = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const maxCount = entries[0]?.[1] || 1;

  // Build vertical bar chart — one bar per tone label
  entries.forEach(([label, count]) => {
    const pct    = (count / maxCount) * 100;
    const sharePct = ((count / total) * 100).toFixed(0);
    const color  = toneColor(label);

    const col = document.createElement('div');
    col.className = 'bar-col';

    const bar = document.createElement('div');
    bar.className = 'bar-bar';
    bar.style.height     = `${Math.max(pct, count > 0 ? 6 : 0)}%`;
    bar.style.background = `linear-gradient(180deg, ${color} 0%, ${color}bb 100%)`;
    bar.style.boxShadow  = `0 0 8px ${color}44`;
    bar.title = `${formatToneLabel(label)}: ${count} (${sharePct}%)`;

    const lbl = document.createElement('div');
    lbl.className = 'bar-label';
    // Abbreviate long labels
    const shortMap = {
      'humorous': 'HUM', 'mocking': 'MOCK', 'insulting': 'INS',
      'sarcastic': 'SARC', 'neutral': 'NEU', 'unknown': '?',
      'light-hearted': 'LH', 'heavy-hearted': 'HH'
    };
    lbl.textContent = shortMap[label] || label.slice(0, 4).toUpperCase();
    lbl.title = formatToneLabel(label);

    const countLbl = document.createElement('div');
    countLbl.className = 'bar-count';
    countLbl.textContent = count;
    countLbl.style.color = color;

    col.appendChild(countLbl);
    col.appendChild(bar);
    col.appendChild(lbl);
    barChart.appendChild(col);
  });
}

// ─── Top comments list ────────────────────────────────────────────────────────

function buildTopList(filteredData) {
  topList.innerHTML = '';

  if (!filteredData || filteredData.length === 0) {
    topLabel.style.display = 'none';
    return;
  }

  topLabel.style.display = 'block';

  const topItems = [...filteredData]
    .sort((a, b) => b.sarcasm_score - a.sarcasm_score)
    .slice(0, 3);

  topItems.forEach((item, i) => {
    const card = document.createElement('div');
    card.className = 'top-card';

    const scorePct    = (item.sarcasm_score * 100).toFixed(0);
    const preview     = item.text.length > 120 ? item.text.slice(0, 117) + '…' : item.text;
    const fuzzyLabel  = formatToneLabel(item.fuzzy_degree || 'none');
    const toneLabel   = formatToneLabel(item.tone_label || item.dominant_label || 'unknown');
    const color       = toneColor(item.tone_label || item.dominant_label);

    card.innerHTML = `
      <div class="top-card-header">
        <span class="top-rank">#${i + 1}</span>
        <span class="top-author">${escapeHtml(item.author)}</span>
        <span class="top-tone-pill" style="--tone-color:${color}">${escapeHtml(toneLabel)}</span>
        <span class="top-fuzzy-badge fuzzy-${item.fuzzy_degree || 'none'}">${escapeHtml(fuzzyLabel)}</span>
        <span class="top-score-badge">${scorePct}</span>
      </div>
      <div class="top-text">${escapeHtml(preview)}</div>
      <div class="top-bar-wrap">
        <div class="top-bar-fill" style="width:${scorePct}%; background: linear-gradient(90deg, ${color} 0%, ${color}99 100%);"></div>
      </div>
    `;

    topList.appendChild(card);
  });
}

// ─── Render from a filtered data set ─────────────────────────────────────────

function renderFromData(data, filter) {
  if (!data || data.length === 0) {
    statTotal.textContent = '0';
    statPct.textContent   = '—';
    statAvg.textContent   = '0.0';
    legendSarcasticN.textContent = 0;
    legendNormalN.textContent    = 0;
    updateDonut(0, 'neutral');
    buildBarChart([]);
    buildTopList([]);
    return;
  }

  const total = data.length;

  // Count label occurrences
  const labelCounts = {};
  data.forEach(c => {
    const lbl = (c.tone_label || c.dominant_label || 'unknown').toLowerCase();
    labelCounts[lbl] = (labelCounts[lbl] || 0) + 1;
  });

  // Dominant label among this slice
  const [[dominantLabel, dominantCount]] = Object.entries(labelCounts)
    .sort((a, b) => b[1] - a[1]);
  const dominantPct = ((dominantCount / total) * 100).toFixed(1);

  // Average sarcasm score
  const avgScore = data.reduce((s, c) => s + (c.sarcasm_score || 0), 0) / total;

  // Stat cards
  statTotal.textContent = total;
  statPct.textContent   = formatToneLabel(dominantLabel);
  statAvg.textContent   = `${dominantPct}%`;

  // Fix the stat labels for this context
  statPct.parentElement.querySelector('.stat-label').textContent = 'Top Tone';
  statAvg.parentElement.querySelector('.stat-label').textContent = 'Tone Share';

  // Legend: dominant vs everything else
  const otherCount = total - dominantCount;
  if (legendPrimaryLabel)   legendPrimaryLabel.textContent   = formatToneLabel(dominantLabel).toLowerCase();
  if (legendSecondaryLabel) legendSecondaryLabel.textContent = 'other tones';
  legendSarcasticN.textContent = dominantCount;
  legendNormalN.textContent    = otherCount;

  // Donut shows dominant label share
  updateDonut(parseFloat(dominantPct), dominantLabel);

  // Charts
  buildBarChart(data);
  buildTopList(data);
}

// ─── Main render ─────────────────────────────────────────────────────────────

function renderResults(stats, platform) {
  currentStats    = stats;
  currentPlatform = platform;

  setPlatformBadge(platform);
  updateFilterButtons('all');
  currentFilter = 'all';

  renderFromData(stats.allPaired || [], 'all');
  showState('results');
}

// ─── Filter ───────────────────────────────────────────────────────────────────

function updateFilterButtons(activeFilter) {
  filterButtons.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.filter === activeFilter);
  });
}

function applyFilter(filterType) {
  currentFilter = filterType;
  updateFilterButtons(filterType);
  if (!currentStats) return;

  let data = currentStats.allPaired || [];

  if (filterType === 'sarcastic') {
    // Show only non-neutral comments
    data = data.filter(c => {
      const lbl = (c.tone_label || c.dominant_label || '').toLowerCase();
      return c.is_sarcastic || (lbl && lbl !== 'neutral' && lbl !== 'unknown');
    });
  }

  renderFromData(data, filterType);
}

// ─── CSV Export ──────────────────────────────────────────────────────────────

function exportCSV() {
  if (!currentStats?.allPaired?.length) return;

  const rows = [[
    'author',
    'text',
    'is_sarcastic',
    'sarcasm_score',
    'confidence',
    'tone_label',
    'tone_label_score',
    'dominant_label',
    'dominant_label_score',
    'fuzzy_degree',
    'fuzzy_score'
  ]];

  currentStats.allPaired.forEach(c => {
    rows.push([
      `"${String(c.author || '').replace(/"/g, '""')}"`,
      `"${String(c.text   || '').replace(/"/g, '""')}"`,
      c.is_sarcastic ? '1' : '0',
      (c.sarcasm_score        || 0).toFixed(4),
      (c.confidence           || 0).toFixed(4),
      `"${c.tone_label         || ''}"`,
      (c.tone_label_score     || 0).toFixed(4),
      `"${c.dominant_label     || ''}"`,
      (c.dominant_label_score || 0).toFixed(4),
      `"${c.fuzzy_degree       || ''}"`,
      (c.fuzzy_score          || 0).toFixed(4),
    ]);
  });

  const csv  = rows.map(r => r.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url  = URL.createObjectURL(blob);

  const a    = document.createElement('a');
  a.href     = url;
  a.download = `sarcasm_${currentPlatform}_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);

  exportHint.textContent = '✓ Downloaded!';
  setTimeout(() => { exportHint.textContent = ''; }, 2500);
}

// ─── Scan ─────────────────────────────────────────────────────────────────────

async function triggerScan() {
  btnScan.disabled = true;
  showState('loading');

  chrome.runtime.sendMessage({ action: 'triggerScrape' }, (response) => {
    if (chrome.runtime.lastError || !response?.success) {
      const msg = chrome.runtime.lastError?.message || response?.error || 'Unknown error';
      errorText.textContent = msg.includes('Cannot access') || msg.includes('No active tab')
        ? 'Navigate to a Reddit or YouTube page first.'
        : `Error: ${msg}`;
      showState('error');
      btnScan.disabled = false;
      return;
    }
    pollForResults();
  });
}

function pollForResults(attempts = 0) {
  if (attempts > 20) {
    errorText.textContent = 'Timed out waiting for results.';
    showState('error');
    btnScan.disabled = false;
    return;
  }

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs[0]) return;

    chrome.runtime.sendMessage({ action: 'getResults', tabId: tabs[0].id }, (response) => {
      if (response?.success && response.stats) {
        renderResults(response.stats, response.platform);
        btnScan.disabled = false;
      } else {
        setTimeout(() => pollForResults(attempts + 1), 300);
      }
    });
  });
}

// ─── Load cached results on popup open ───────────────────────────────────────

function loadCachedResults() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (!tabs[0]) { showState('empty'); return; }

    const url = tabs[0].url || '';
    if (!url.includes('reddit.com') && !url.includes('youtube.com')) {
      showState('empty');
      return;
    }

    chrome.runtime.sendMessage({ action: 'getResults', tabId: tabs[0].id }, (response) => {
      if (response?.success && response.stats) {
        renderResults(response.stats, response.platform);
      } else {
        showState('empty');
      }
    });
  });
}

// ─── Live updates from background ────────────────────────────────────────────

chrome.runtime.onMessage.addListener((request) => {
  if (request.action === 'resultsReady') {
    renderResults(request.stats, request.platform);
    btnScan.disabled = false;
  }
});

// ─── Event bindings ───────────────────────────────────────────────────────────

btnScan.addEventListener('click', triggerScan);
btnExport.addEventListener('click', exportCSV);

filterButtons.forEach(btn => {
  btn.addEventListener('click', () => applyFilter(btn.dataset.filter));
});

if (btnClearSession) {
  btnClearSession.addEventListener('click', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) return;
      chrome.runtime.sendMessage({ action: 'clearCache', tabId: tabs[0].id }, () => {
        currentFilter = 'all';
        updateFilterButtons('all');
        showState('empty');
        chrome.tabs.sendMessage(tabs[0].id, { action: 'clearCache' });
      });
    });
  });
}

// ─── Init ─────────────────────────────────────────────────────────────────────

loadCachedResults();
