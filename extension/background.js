/**
 * Background Service Worker - Sarcasm Detector
 * Handles batch API calls to the local FastAPI backend
 * and caches results per tab.
 */

const API_BASE = 'http://127.0.0.1:8000';
const BATCH_ENDPOINT = `${API_BASE}/predict/batch`;

// Per-tab results cache: tabId -> { comments: [], results: [], stats: {}, timestamp }
const tabCache = new Map();

/**
 * Send a batch of comments to /predict/batch
 * comments: [{ text, platform, post_id, metadata }]
 * Returns array of PredictionResponse in the same order
 */
async function runBatchPrediction(comments) {
  const response = await fetch(BATCH_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(comments)
  });

  if (!response.ok) {
    throw new Error(`Backend returned ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Compute summary stats from an array of prediction results
 */
function computeStats(comments, predictions) {
  const total = predictions.length;
  const sarcasticCount = predictions.filter(p => p.is_sarcastic).length;
  const avgScore = predictions.reduce((s, p) => s + p.sarcasm_score, 0) / (total || 1);
  const labelCounts = predictions.reduce((counts, p) => {
    const label = p.tone_label || p.dominant_label || 'unknown';
    counts[label] = (counts[label] || 0) + 1;
    return counts;
  }, {});

  const dominantLabel = Object.entries(labelCounts).sort((a, b) => b[1] - a[1])[0]?.[0] || 'neutral';
  const dominantLabelCount = labelCounts[dominantLabel] || 0;
  const dominantLabelPct = total > 0 ? ((dominantLabelCount / total) * 100).toFixed(1) : '0.0';

  // Pair comments with predictions, sort by sarcasm_score descending
  const paired = comments.map((c, i) => ({
    text: c.text,
    author: c.metadata?.author || 'Unknown',
    sarcasm_score: predictions[i]?.sarcasm_score ?? 0,
    confidence: predictions[i]?.confidence ?? 0,
    is_sarcastic: predictions[i]?.is_sarcastic ?? false,
    dominant_label: predictions[i]?.dominant_label ?? 'unknown',
    dominant_label_score: predictions[i]?.dominant_label_score ?? 0,
    tone_label: predictions[i]?.tone_label ?? predictions[i]?.dominant_label ?? 'unknown',
    tone_label_score: predictions[i]?.tone_label_score ?? predictions[i]?.dominant_label_score ?? 0,
    fuzzy_degree: predictions[i]?.fuzzy_degree ?? 'none',
    fuzzy_score: predictions[i]?.fuzzy_score ?? 0,
    label_probabilities: predictions[i]?.label_probabilities ?? {}
  }));

  const topSarcastic = [...paired]
    .filter(p => p.tone_label && p.tone_label !== 'neutral')
    .sort((a, b) => b.tone_label_score - a.tone_label_score)
    .slice(0, 5);

  return {
    total,
    sarcasticCount,
    nonSarcasticCount: total - sarcasticCount,
    sarcasticPct: total > 0 ? ((sarcasticCount / total) * 100).toFixed(1) : '0.0',
    avgScore: (avgScore * 100).toFixed(1),
    dominantLabel,
    dominantLabelCount,
    dominantLabelPct,
    labelCounts,
    topSarcastic,
    allPaired: paired
  };
}

// Listen for messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'analyzeComments') {
    const tabId = sender.tab?.id;
    const { comments, platform } = request;

    runBatchPrediction(comments)
      .then(predictions => {
        // 1. Retrieve existing data for this tab
        const existingData = tabCache.get(tabId) || { 
          allComments: [], 
          allPredictions: [] 
        };

        // 2. Accumulate the results
        const updatedComments = [...existingData.allComments, ...comments];
        const updatedPredictions = [...existingData.allPredictions, ...predictions];

        // 3. Compute stats on the ENTIRE set, not just the new batch
        const stats = computeStats(updatedComments, updatedPredictions);

        tabCache.set(tabId, {
          stats,
          platform,
          timestamp: Date.now(),
          allComments: updatedComments, // Store full history for accumulation
          allPredictions: updatedPredictions
        });

        chrome.runtime.sendMessage({
          action: 'resultsReady',
          tabId,
          stats,
          platform
        }).catch(() => {});

        sendResponse({ success: true, stats, predictions });
      })
      // ... catch block remains the same
    return true; 
  }

  // Popup requests cached results for the active tab
  if (request.action === 'getResults') {
    const tabId = request.tabId;
    const cached = tabCache.get(tabId);
    if (cached) {
      sendResponse({ success: true, ...cached });
    } else {
      sendResponse({ success: false, error: 'No results yet for this tab' });
    }
    return true;
  }

  // Popup triggers a fresh scrape+analysis
  if (request.action === 'triggerScrape') {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) {
        sendResponse({ success: false, error: 'No active tab' });
        return;
      }
      chrome.tabs.sendMessage(tabs[0].id, { action: 'scrapeAndAnalyze' }, (response) => {
        if (chrome.runtime.lastError) {
          sendResponse({ success: false, error: chrome.runtime.lastError.message });
        } else {
          sendResponse(response || { success: true });
        }
      });
    });
    return true;
  }

  // Clear cache for a tab
  if (request.action === 'clearCache') {
    if (request.tabId) tabCache.delete(request.tabId);
    sendResponse({ success: true });
    return true;
  }
});

// Clean up cache when a tab is closed
chrome.tabs.onRemoved.addListener((tabId) => {
  tabCache.delete(tabId);
});
