/**
 * Content Script for Twitter/X - Sarcasm Detection
 * Monitors tweets using MutationObserver and sends them for sarcasm detection
 */

const API_ENDPOINT = 'http://localhost:8000/predict';
const SARCASM_THRESHOLD = 0.5;

// Cache to avoid re-processing tweets
const processedTweets = new Set();

// Configuration
const config = {
  enabled: true,
  highlightColor: '#fff3cd',
  labelColor: '#856404'
};

/**
 * Extract tweet text from tweet element
 */
function extractTweetText(tweetElement) {
  // Twitter/X uses data-testid for tweet text
  const textElement = tweetElement.querySelector('[data-testid="tweetText"]');
  if (textElement) {
    return textElement.innerText.trim();
  }
  
  // Fallback: look for tweet text in various possible selectors
  const fallbackSelectors = [
    '[lang] > span',
    '.css-1qaijid', // Twitter's dynamic class for text
    '[dir="auto"] > span'
  ];
  
  for (const selector of fallbackSelectors) {
    const element = tweetElement.querySelector(selector);
    if (element && element.innerText.length > 10) {
      return element.innerText.trim();
    }
  }
  
  return null;
}

/**
 * Get unique identifier for tweet
 */
function getTweetId(tweetElement) {
  // Try to get tweet link which contains the tweet ID
  const tweetLink = tweetElement.querySelector('a[href*="/status/"]');
  if (tweetLink) {
    const match = tweetLink.href.match(/\/status\/(\d+)/);
    if (match) return match[1];
  }
  
  // Fallback to a hash of the text
  const text = extractTweetText(tweetElement);
  return text ? hashCode(text).toString() : null;
}

/**
 * Simple hash function for text
 */
function hashCode(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash;
  }
  return Math.abs(hash);
}

/**
 * Send text to API for sarcasm detection
 */
async function detectSarcasm(text, postId) {
  try {
    const response = await fetch(API_ENDPOINT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text: text,
        platform: 'twitter',
        post_id: postId,
        metadata: {
          url: window.location.href,
          timestamp: new Date().toISOString()
        }
      })
    });

    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }

    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Sarcasm detection error:', error);
    return null;
  }
}

/**
 * Inject sarcasm label into tweet
 */
function injectSarcasmLabel(tweetElement, prediction) {
  // Check if label already exists
  if (tweetElement.querySelector('.sarcasm-label')) {
    return;
  }

  // Create sarcasm label
  const label = document.createElement('div');
  label.className = 'sarcasm-label';
  label.innerHTML = `
    <span class="sarcasm-icon">??</span>
    <span class="sarcasm-text">Sarcasm Detected</span>
    <span class="sarcasm-confidence">${(prediction.sarcasm_score * 100).toFixed(1)}</span>
  `;

  // Highlight tweet background
  const article = tweetElement.closest('article');
  if (article) {
    article.style.backgroundColor = config.highlightColor;
    article.style.borderLeft = '4px solid #ffc107';
    article.style.transition = 'background-color 0.3s ease';
    
    // Insert label after tweet text
    const textElement = article.querySelector('[data-testid="tweetText"]');
    if (textElement) {
      const container = textElement.closest('[data-testid="tweetText"]').parentElement;
      container.style.position = 'relative';
      container.appendChild(label);
    }
  }
}

/**
 * Process a single tweet
 */
async function processTweet(tweetElement) {
  if (!config.enabled) return;

  const tweetId = getTweetId(tweetElement);
  if (!tweetId || processedTweets.has(tweetId)) {
    return;
  }

  const text = extractTweetText(tweetElement);
  if (!text || text.length < 5) {
    return;
  }

  // Mark as processed
  processedTweets.add(tweetId);

  // Detect sarcasm
  const prediction = await detectSarcasm(text, tweetId);
  
  if (prediction && prediction.is_sarcastic && prediction.sarcasm_score >= SARCASM_THRESHOLD) {
    injectSarcasmLabel(tweetElement, prediction);
  }
}

/**
 * Find all tweet elements in the current view
 */
function findTweets() {
  // Twitter/X uses article elements for tweets
  return document.querySelectorAll('article[data-testid="tweet"]');
}

/**
 * Process all visible tweets
 */
async function processVisibleTweets() {
  const tweets = findTweets();
  for (const tweet of tweets) {
    await processTweet(tweet);
  }
}

/**
 * Initialize MutationObserver to watch for new tweets
 */
function initializeObserver() {
  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.addedNodes.length) {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            // Check if the node itself is a tweet
            if (node.matches && node.matches('article[data-testid="tweet"]')) {
              processTweet(node);
            }
            // Check if the node contains tweets
            else if (node.querySelectorAll) {
              const tweets = node.querySelectorAll('article[data-testid="tweet"]');
              tweets.forEach(processTweet);
            }
          }
        });
      }
    }
  });

  // Observe the timeline container
  const timelineContainer = document.querySelector('[data-testid="primaryColumn"]') || document.body;
  
  observer.observe(timelineContainer, {
    childList: true,
    subtree: true
  });

  console.log('Sarcasm Detector: Observer initialized for Twitter/X');
}

/**
 * Initialize the extension
 */
function initialize() {
  console.log('Sarcasm Detector: Initializing for Twitter/X');
  
  // Load config from storage
  chrome.storage.sync.get(['enabled', 'highlightColor'], (result) => {
    if (result.enabled !== undefined) {
      config.enabled = result.enabled;
    }
    if (result.highlightColor) {
      config.highlightColor = result.highlightColor;
    }
  });

  // Process existing tweets
  processVisibleTweets();

  // Start observing for new tweets
  initializeObserver();

  // Re-process on scroll (debounced)
  let scrollTimeout;
  window.addEventListener('scroll', () => {
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(processVisibleTweets, 500);
  });
}

// Listen for messages from popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'toggle') {
    config.enabled = request.enabled;
    if (config.enabled) {
      processVisibleTweets();
    }
  } else if (request.action === 'clearCache') {
    processedTweets.clear();
    console.log('Sarcasm Detector: Cache cleared');
  }
  sendResponse({ success: true });
});

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
}
