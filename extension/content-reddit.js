/**
 * Content Script - Reddit
 * Scrapes comments, sends batch to background for prediction,
 * and injects inline sarcasm labels on detected comments.
 */

const PLATFORM = 'reddit';
const SARCASM_THRESHOLD = 0.5;
const processedIds = new Set();

// ─── DOM Scrapers ────────────────────────────────────────────────────────────

function extractCommentText(el) {
  // New Reddit (shreddit)
  const newBody = el.querySelector('[slot="comment"] p, div[id^="comment-body"] p');
  if (newBody) {
    return Array.from(el.querySelectorAll('[slot="comment"] p, div[id^="comment-body"] p'))
      .map(p => p.innerText.trim())
      .filter(Boolean)
      .join(' ');
  }

  // Old Reddit / hybrid
  const selectors = [
    '.md p',
    '[data-click-id="text"] p',
    '.Comment__body p',
    'div[data-test-id="comment"] p'
  ];
  for (const sel of selectors) {
    const els = el.querySelectorAll(sel);
    if (els.length) {
      return Array.from(els).map(p => p.innerText.trim()).filter(Boolean).join(' ');
    }
  }

  return null;
}

function extractAuthor(el) {
  const a = el.querySelector('a[href*="/user/"], faceplate-tracker[noun="author"] a');
  return a ? a.innerText.replace('u/', '').trim() : 'unknown';
}

function getCommentId(el) {
  // shreddit-comment uses thingid attribute
  return el.getAttribute('thingid') ||
         el.getAttribute('id') ||
         el.getAttribute('data-fullname') ||
         null;
}

function findComments() {
  const selectors = [
    'shreddit-comment',
    '[id^="t1_"]',
    'div[data-test-id="comment"]',
    '.Comment'
  ];
  const seen = new Set();
  const results = [];
  for (const sel of selectors) {
    document.querySelectorAll(sel).forEach(el => {
      if (!seen.has(el)) {
        seen.add(el);
        results.push(el);
      }
    });
  }
  return results;
}

// ─── Inline Label Injection ──────────────────────────────────────────────────

function formatToneLabel(label) {
  return String(label || 'unknown')
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase());
}

function injectLabel(el, tone, score, fuzzyDegree) {
  if (el.querySelector('.sd-label')) return;

  const label = document.createElement('div');
  label.className = 'sd-label';
  label.dataset.tone = tone || 'unknown';
  label.dataset.fuzzyDegree = fuzzyDegree || 'none';
  label.innerHTML = `
    <span class="sd-icon">⚡</span>
    <span class="sd-fuzzy fuzzy-${fuzzyDegree || 'none'}">${formatToneLabel(fuzzyDegree)}</span>
    <span class="sd-score">${(score * 100).toFixed(0)}</span>
  `;

  el.style.borderLeft = '3px solid #f97316';
  el.style.paddingLeft = '6px';
  el.style.transition = 'border-color 0.3s';

  const anchor = el.querySelector('[slot="comment"], .Comment__body, .md') || el;
  anchor.insertBefore(label, anchor.firstChild);
}

// ─── Core Analysis Flow ──────────────────────────────────────────────────────

async function scrapeAndAnalyze() {
  const commentEls = findComments();
  const toProcess = [];

  for (const el of commentEls) {
    const id = getCommentId(el);
    if (id && processedIds.has(id)) continue;

    const text = extractCommentText(el);
    if (!text || text.length < 5) continue;

    toProcess.push({
      el,
      payload: {
        text,
        platform: PLATFORM,
        post_id: id || undefined,
        metadata: {
          author: extractAuthor(el),
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

        // Inject inline labels for sarcastic comments
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

// ─── MutationObserver for dynamic content ───────────────────────────────────

let debounceTimer;
function onMutation(mutations) {
  const relevant = mutations.some(m =>
    Array.from(m.addedNodes).some(n =>
      n.nodeType === Node.ELEMENT_NODE &&
      (n.tagName === 'SHREDDIT-COMMENT' ||
       n.matches?.('[id^="t1_"]') ||
       n.querySelector?.('shreddit-comment, [id^="t1_"]'))
    )
  );
  if (!relevant) return;
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(scrapeAndAnalyze, 800);
}

function initObserver() {
  const root = document.querySelector('shreddit-app, #AppRouter-main-content') || document.body;
  new MutationObserver(onMutation).observe(root, { childList: true, subtree: true });
}

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
  scrapeAndAnalyze();
  initObserver();

  let scrollTimer;
  window.addEventListener('scroll', () => {
    clearTimeout(scrollTimer);
    scrollTimer = setTimeout(scrapeAndAnalyze, 600);
  }, { passive: true });
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  init();
}
