/**
 * Popup JS - Sarcasm Detector
 * Handles: scan trigger, result rendering, donut chart,
 * score distribution bar chart, top comments list, CSV export.
 */

// ─── State ───────────────────────────────────────────────────────────────────

let currentStats = null;
let currentPlatform = null;

// ─── DOM refs ────────────────────────────────────────────────────────────────

const btnScan       = document.getElementById('btn-scan');
const btnExport     = document.getElementById('btn-export');
const btnClearSession = document.getElementById('btn-clear-session');
const platformBadge = document.getElementById('platform-badge');

const stateLoading  = document.getElementById('state-loading');
const stateEmpty    = document.getElementById('state-empty');
const stateError    = document.getElementById('state-error');
const stateResults  = document.getElementById('state-results');
const errorText     = document.getElementById('error-text');

const statTotal     = document.getElementById('stat-total');
const statPct       = document.getElementById('stat-pct');
const statAvg       = document.getElementById('stat-avg');

const donutFill     = document.getElementById('donut-fill');
const donutPct      = document.getElementById('donut-pct');
const legendPrimaryLabel   = document.getElementById('legend-primary-label');
const legendSecondaryLabel = document.getElementById('legend-secondary-label');
const legendSarcasticN = document.getElementById('legend-sarcastic-n');
const legendNormalN    = document.getElementById('legend-normal-n');

const barChart      = document.getElementById('bar-chart');
const topList       = document.getElementById('top-list');
const topLabel      = document.getElementById('top-label');
const exportHint    = document.getElementById('export-hint');

// ─── State helpers ───────────────────────────────────────────────────────────

function showState(name) {
  stateLoading.style.display = name === 'loading' ? 'flex' : 'none';
  stateEmpty.style.display   = name === 'empty'   ? 'flex' : 'none';
  stateError.style.display   = name === 'error'   ? 'flex' : 'none';
  stateResults.style.display = name === 'results' ? 'block' : 'none';
}

function setPlatformBadge(platform) {
  const labels = { reddit: 'Reddit', youtube: 'YouTube' };
  platformBadge.textContent = labels[platform] || platform || '—';
  platformBadge.dataset.platform = platform || '';
}

function formatToneLabel(label) {
  if (!label) return '—';
  return label.replace(/[-_]/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase());
}

// ─── Donut chart ─────────────────────────────────────────────────────────────

function updateDonut(pct) {
  const circumference = 2 * Math.PI * 46; // r=46 → ~289
  const filled = (pct / 100) * circumference;
  donutFill.setAttribute('stroke-dasharray', `${filled.toFixed(1)} ${circumference.toFixed(1)}`);
  donutPct.textContent = `${pct}`;
}

// ─── Score distribution bar chart ────────────────────────────────────────────

function buildBarChart(allPaired) {
  // Bucket scores into 10 bins: [0-10), [10-20), …, [90-100]
  const bins = Array(10).fill(0);
  allPaired.forEach(c => {
    const idx = Math.min(Math.floor(c.sarcasm_score * 10), 9);
    bins[idx]++;
  });

  const max = Math.max(...bins, 1);
  barChart.innerHTML = '';

  bins.forEach((count, i) => {
    const pct = (count / max) * 100;
    const isSarcastic = i >= 5;

    const col = document.createElement('div');
    col.className = 'bar-col';

    const bar = document.createElement('div');
    bar.className = `bar-bar ${isSarcastic ? 'bar-sarcastic' : 'bar-normal'}`;
    bar.style.height = `${Math.max(pct, count > 0 ? 4 : 0)}%`;
    bar.title = `${i * 10}–${i * 10 + 10}%: ${count} comment${count !== 1 ? 's' : ''}`;

    const lbl = document.createElement('div');
    lbl.className = 'bar-label';
    lbl.textContent = `${i * 10}`;

    col.appendChild(bar);
    col.appendChild(lbl);
    barChart.appendChild(col);
  });
}

// ─── Top sarcastic comments ───────────────────────────────────────────────────

function buildTopList(topSarcastic) {
  topList.innerHTML = '';

  if (!topSarcastic || topSarcastic.length === 0) {
    topLabel.style.display = 'none';
    return;
  }

  topLabel.style.display = 'block';

  topSarcastic.forEach((item, i) => {
    const card = document.createElement('div');
    card.className = 'top-card';

    const scorePct = (item.sarcasm_score * 100).toFixed(0);
    const preview = item.text.length > 120
      ? item.text.slice(0, 117) + '…'
      : item.text;
    const toneLabel = formatToneLabel(item.tone_label || item.dominant_label);
    const fuzzyDegree = formatToneLabel(item.fuzzy_degree || 'none');

    card.innerHTML = `
      <div class="top-card-header">
        <span class="top-rank">#${i + 1}</span>
        <span class="top-author">${escapeHtml(item.author)}</span>
        <span class="top-tone-badge">${escapeHtml(toneLabel)}</span>
        <span class="top-fuzzy-badge fuzzy-${item.fuzzy_degree || 'none'}">${escapeHtml(fuzzyDegree)}</span>
        <span class="top-score-badge">${scorePct}</span>
      </div>
      <div class="top-text">${escapeHtml(preview)}</div>
      <div class="top-bar-wrap">
        <div class="top-bar-fill" style="width:${scorePct}%"></div>
      </div>
    `;

    topList.appendChild(card);
  });
}

// ─── Render results ───────────────────────────────────────────────────────────

function renderResults(stats, platform) {
  currentStats = stats;
  currentPlatform = platform;

  setPlatformBadge(platform);

  statTotal.textContent = stats.total;
  statPct.textContent   = formatToneLabel(stats.dominantLabel);
  statAvg.textContent   = `${stats.dominantLabelPct ?? stats.avgScore}`;

  statPct.parentElement.querySelector('.stat-label').textContent = 'Dominant tone';
  statAvg.parentElement.querySelector('.stat-label').textContent = 'Tone share';

  legendSarcasticN.textContent = stats.labelCounts?.[stats.dominantLabel] ?? stats.sarcasticCount;
  legendNormalN.textContent    = stats.total - (stats.labelCounts?.[stats.dominantLabel] ?? stats.sarcasticCount);
  if (legendPrimaryLabel) legendPrimaryLabel.textContent = formatToneLabel(stats.dominantLabel).toLowerCase();
  if (legendSecondaryLabel) legendSecondaryLabel.textContent = 'other tones';

  updateDonut(parseFloat(stats.dominantLabelPct ?? stats.sarcasticPct));
  buildBarChart(stats.allPaired || []);
  buildTopList(stats.topSarcastic || []);

  const donutCenterLabel = document.querySelector('.donut-center-label');
  if (donutCenterLabel) {
    donutCenterLabel.textContent = formatToneLabel(stats.dominantLabel).toLowerCase();
  }

  const topLabelText = document.getElementById('top-label');
  if (topLabelText) {
    topLabelText.textContent = `Top ${formatToneLabel(stats.dominantLabel).toLowerCase()} comments`;
  }

  showState('results');
}

// ─── CSV Export ──────────────────────────────────────────────────────────────

function exportCSV() {
  if (!currentStats?.allPaired?.length) return;

  const rows = [
    ['author', 'text', 'is_sarcastic', 'sarcasm_score', 'confidence']
  ];

  currentStats.allPaired.forEach(c => {
    rows.push([
      c.author,
      `"${c.text.replace(/"/g, '""')}"`,
      c.is_sarcastic ? '1' : '0',
      c.sarcasm_score.toFixed(4),
      c.confidence.toFixed(4)
    ]);
  });

  const csv = rows.map(r => r.join(',')).join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const url  = URL.createObjectURL(blob);

  const a = document.createElement('a');
  a.href = url;
  a.download = `sarcasm_${currentPlatform}_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);

  exportHint.textContent = 'Downloaded!';
  setTimeout(() => { exportHint.textContent = ''; }, 2500);
}

// ─── Scan ────────────────────────────────────────────────────────────────────

async function triggerScan() {
  btnScan.disabled = true;
  showState('loading');

  // Ask background to tell content script to scrape+analyze
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

    // Poll for results from background cache
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
    const isSupported = url.includes('reddit.com') || url.includes('youtube.com');

    if (!isSupported) {
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

// ─── Listen for live updates from background ─────────────────────────────────

chrome.runtime.onMessage.addListener((request) => {
  if (request.action === 'resultsReady') {
    renderResults(request.stats, request.platform);
    btnScan.disabled = false;
  }
});

// ─── Helpers ─────────────────────────────────────────────────────────────────

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ─── Bind events ─────────────────────────────────────────────────────────────

btnScan.addEventListener('click', triggerScan);
btnExport.addEventListener('click', exportCSV);
if (btnClearSession) {
  btnClearSession.addEventListener('click', () => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) return;
      chrome.runtime.sendMessage({ action: 'clearCache', tabId: tabs[0].id }, () => {
        // Clear local UI state
        showState('empty');
        // Also notify content script to clear processedIds
        chrome.tabs.sendMessage(tabs[0].id, { action: 'clearCache' });
      });
    });
  });
}

// ─── Init ─────────────────────────────────────────────────────────────────────

loadCachedResults();
