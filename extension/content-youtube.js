/**
 * Content Script - YouTube
 * Scrapes comments from youtube.com/watch pages,
 * sends batch to background for prediction,
 * and injects inline sarcasm labels.
 *
 * Confirmed DOM structure (May 2026):
 *   ytd-comment-thread-renderer
 *     └─ ytd-comment-view-model
 *          ├─ yt-attributed-string  (comment text)
 *          └─ #author-text / h3 a   (author)
 */

const PLATFORM = 'youtube';
const SARCASM_THRESHOLD = 0.5;
const processedIds = new Set();

// ─── Helpers ─────────────────────────────────────────────────────────────────

function hashText(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = Math.imul(31, h) + str.charCodeAt(i) | 0;
  }
  return Math.abs(h).toString(36);
}

function formatToneLabel(label) {
  return String(label || 'unknown')
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase());
}

// ─── DOM Scrapers ────────────────────────────────────────────────────────────

function findComments() {
  return Array.from(document.querySelectorAll([
    'ytd-comment-thread-renderer',
    'ytd-comment-renderer'
  ].join(',')));
}

function extractCommentText(el) {
  const vm = el.querySelector('ytd-comment-view-model') || el;

  // Text can live in several slightly different comment layouts.
  const selectors = [
    'yt-attributed-string',
    '#content-text',
    'yt-formatted-string#content-text',
    'yt-formatted-string',
    '[id="content-text"]'
  ];

  for (const selector of selectors) {
    const node = vm.querySelector(selector);
    const text = node?.innerText?.trim();
    if (text) return text;
  }

  return vm.innerText?.trim() || null;
}

function extractAuthor(el) {
  const vm = el.querySelector('ytd-comment-view-model') || el;
  if (!vm) return 'unknown';
  const a = vm.querySelector('#author-text, h3 a, ytd-channel-name a');
  return a ? a.innerText.trim().replace(/^@/, '') : 'unknown';
}

function getCommentId(el) {
  // Prefer native IDs if present, otherwise derive a stable hash from text.
  return el.getAttribute('id') ||
         el.getAttribute('data-comment-id') ||
         el.getAttribute('data-id') ||
         (() => {
           const text = extractCommentText(el);
           return text ? 'yt_' + hashText(text) : null;
         })();
}

// ─── Inline Label Injection ──────────────────────────────────────────────────

function injectLabel(el, tone, score, fuzzyDegree) {
  if (el.querySelector('.sd-label')) return;

  const label = document.createElement('div');
  label.className = 'sd-label';
  label.dataset.tone = tone || 'unknown';
  label.dataset.fuzzyDegree = fuzzyDegree || 'none';
  label.innerHTML = `
    <span class="sd-fuzzy fuzzy-${fuzzyDegree || 'none'}">${formatToneLabel(fuzzyDegree)}</span>
    <span class="sd-score">${(score * 100).toFixed(0)}</span>
  `;

  el.style.borderLeft = '3px solid #f97316';
  el.style.paddingLeft = '8px';
  el.style.transition = 'border-color 0.3s';

  // Inject just before the comment text inside the view model
  const vm = el.querySelector('ytd-comment-view-model');
  const anchor = vm?.querySelector('yt-attributed-string')?.parentElement || vm || el;
  anchor.insertBefore(label, anchor.firstChild);
}

// ─── Core Analysis Flow ──────────────────────────────────────────────────────

async function scrapeAndAnalyze() {
  const isWatchPage = window.location.pathname.startsWith('/watch');
  const isShortsPage = window.location.pathname.startsWith('/shorts/');

  if (!isWatchPage && !isShortsPage) {
    return { success: true, count: 0 };
  }

  const commentEls = findComments();
  const toProcess = [];

  for (const el of commentEls) {
    const id = getCommentId(el);
    if (id && processedIds.has(id)) continue;

    const text = extractCommentText(el);
    if (!text || text.length < 5) continue;

    const videoId = isWatchPage
      ? new URLSearchParams(window.location.search).get('v') || undefined
      : (window.location.pathname.split('/shorts/')[1] || '').split(/[/?#]/)[0] || undefined;

    toProcess.push({
      el,
      payload: {
        text,
        platform: PLATFORM,
        post_id: videoId,
        metadata: {
          author: extractAuthor(el),
          comment_id: id,
          url: window.location.href,
          timestamp: new Date().toISOString()
        }
      }
    });

    if (id) processedIds.add(id);
  }

  if (toProcess.length === 0) return { success: true, count: 0 };

  return new Promise((resolve) => {
    chrome.runtime.sendMessage(
      {
        action: 'analyzeComments',
        comments: toProcess.map(t => t.payload),
        platform: PLATFORM
      },
      (response) => {
        if (!response?.success || !response.predictions) {
          resolve({ success: false, error: response?.error });
          return;
        }

        toProcess.forEach(({ el }, i) => {
          const pred = response.predictions[i];
          const tone = pred?.tone_label || pred?.dominant_label;
          const fuzzyDegree = pred?.fuzzy_degree || 'none';
          if (tone && tone !== 'neutral') {
            injectLabel(el, tone, pred?.tone_label_score ?? pred?.dominant_label_score ?? pred.sarcasm_score, fuzzyDegree);
          }
        });

        resolve({ success: true, count: toProcess.length });
      }
    );
  });
}

// ─── MutationObserver ────────────────────────────────────────────────────────

let debounceTimer;
function onMutation(mutations) {
  const relevant = mutations.some(m =>
    Array.from(m.addedNodes).some(n =>
      n.nodeType === Node.ELEMENT_NODE &&
      (n.tagName === 'YTD-COMMENT-THREAD-RENDERER' ||
       n.tagName === 'YTD-COMMENT-VIEW-MODEL' ||
       n.querySelector?.('ytd-comment-thread-renderer'))
    )
  );
  if (!relevant) return;
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(scrapeAndAnalyze, 800);
}

function initObserver() {
  const root = document.querySelector('ytd-comments, #comments') || document.body || document.documentElement;
  new MutationObserver(onMutation).observe(root, { childList: true, subtree: true });
}

// ─── Navigation handling (YouTube is a SPA) ─────────────────────────────────

// YouTube navigates without full page reloads — watch for URL changes
let lastUrl = location.href;
new MutationObserver(() => {
  if (location.href !== lastUrl) {
    lastUrl = location.href;
    processedIds.clear();
    // Wait for comments section to render after navigation
    setTimeout(scrapeAndAnalyze, 2500);
  }
}).observe(document.body, { subtree: true, childList: true });

// ─── Message Listener ────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'scrapeAndAnalyze') {
    scrapeAndAnalyze().then(sendResponse);
    return true;
  }
  if (request.action === 'clearCache') {
    processedIds.clear();
    sendResponse({ success: true });
  }
});

// ─── Init ────────────────────────────────────────────────────────────────────

function init() {
  // YouTube comments load lazily — wait a bit before first scrape
  setTimeout(scrapeAndAnalyze, 2000);
  initObserver();

  let scrollTimer;
  window.addEventListener('scroll', () => {
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(scrapeAndAnalyze, 700);
  }, { passive: true });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
