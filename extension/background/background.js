// Service worker (background script) - handles detection, ingestion, and message routing

const BACKEND_URL = 'https://grounded-review-assistant.onrender.com';
const INGEST_ENDPOINT = '/api/v1/ingest';

let ingestionState = {
  inProgress: {},
  completed: new Set()
};

const INVALID_SIGNALS = [
  'online shopping', 'shop online', 'sign in', 'mobiles, books',
  'great indian', 'sale', 'search results', 'deals of the day'
];

async function autoIngestProduct(productName) {
  if (!productName || productName.length < 5 || productName.length > 150) {
    console.log(`[AutoIngest] Skipping invalid length: "${productName}"`);
    return;
  }

  const lower = productName.toLowerCase();
  if (INVALID_SIGNALS.some(signal => lower.includes(signal))) {
    console.log(`[AutoIngest] Skipping generic title: "${productName}"`);
    return;
  }

  if (!/\d/.test(productName)) {
    console.log(`[AutoIngest] Skipping - no model number found: "${productName}"`);
    return;
  }

  if (ingestionState.inProgress[productName] || ingestionState.completed.has(productName)) {
    console.log(`[AutoIngest] Skipping ${productName} - already ingested or in progress`);
    return;
  }

  ingestionState.inProgress[productName] = true;

  try {
    console.log(`[AutoIngest] Starting ingestion for: ${productName}`);

    const response = await fetch(`${BACKEND_URL}${INGEST_ENDPOINT}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_query: productName })
    });

    if (response.ok) {
      const data = await response.json();
      console.log(`[AutoIngest] Success for ${productName}`, data);

      ingestionState.completed.add(productName);

      chrome.storage.local.set({
        lastProduct: productName,
        lastIngestionTime: Date.now(),
        ingestionStatus: 'success'
      });

      broadcastToAllContexts({
        type: 'INGESTION_STARTED',
        productName: productName,
        timestamp: Date.now()
      });
    } else {
      const errorData = await response.json();
      console.error(`[AutoIngest] Failed for ${productName}:`, errorData);

      chrome.storage.local.set({
        ingestionStatus: 'failed',
        ingestionError: errorData.detail || 'Unknown error'
      });
    }
  } catch (error) {
    console.error(`[AutoIngest] Network error for ${productName}:`, error.message);
    chrome.storage.local.set({
      ingestionStatus: 'error',
      ingestionError: error.message
    });
  } finally {
    delete ingestionState.inProgress[productName];
  }
}

function broadcastToAllContexts(message) {
  chrome.tabs.query({}, (tabs) => {
    tabs.forEach(tab => {
      chrome.tabs.sendMessage(tab.id, message).catch(() => {});
    });
  });

  chrome.storage.session.set({
    lastBroadcast: message,
    broadcastTime: Date.now()
  });
}

chrome.tabs.onActivated.addListener((activeInfo) => {
  chrome.tabs.get(activeInfo.tabId, (tab) => {
    if (isShoppingPage(tab.url)) {
      console.log('[TabActivated] Shopping tab detected:', tab.url);

      chrome.tabs.sendMessage(activeInfo.tabId, { type: 'GET_PRODUCT_INFO' }, (response) => {
        if (response && response.productName) {
          console.log('[TabActivated] Product detected:', response.productName);

          chrome.storage.local.set({
            activeProduct: response.productName,
            activeProductPlatform: response.platform,
            activeProductUrl: response.url
          });

          autoIngestProduct(response.productName);
        }
      });
    }
  });
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && isShoppingPage(tab.url)) {
    console.log('[TabUpdated] Page loaded:', tab.url);

    setTimeout(() => {
      chrome.tabs.sendMessage(tabId, { type: 'GET_PRODUCT_INFO' }, (response) => {
        if (response && response.productName) {
          console.log('[TabUpdated] Product detected:', response.productName);

          chrome.storage.local.set({
            activeProduct: response.productName,
            activeProductPlatform: response.platform,
            activeProductUrl: response.url
          });

          autoIngestProduct(response.productName);
        }
      });
    }, 2000);
  }
});

function isShoppingPage(url) {
  if (!url) return false;
  const isAmazonProduct = /amazon\.[a-z.]+\/.*\/dp\/[A-Z0-9]{10}/.test(url);
  const isFlipkartProduct = /flipkart\.com\/[^/]+\/p\/[a-z0-9]+/.test(url);
  return isAmazonProduct || isFlipkartProduct;
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('[MessageReceived]', request.type, 'from', sender.url);

  if (request.type === 'INGEST_RICH_REVIEWS') {
    const { productName, platform, url, reviews } = request;

    console.log(`[RichReviews] Received ${reviews.length} reviews for ${productName}`);

    // Validate product name
    if (!productName || productName.length < 5 ||
        productName.includes('Amazon') ||
        !/\d/.test(productName)) {
      sendResponse({ acknowledged: false });
      return;
    }

    chrome.storage.local.set({
      activeProduct: productName,
      activeProductPlatform: platform,
      activeProductUrl: url,
      productDetectionTime: request.timestamp
    });

    fetch(`${BACKEND_URL}/api/v1/ingest/reviews`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ product_query: productName, platform, url, reviews })
    }).then(r => r.json()).then(data => {
      console.log('[RichReviews] Sent to backend:', data);
    }).catch(e => {
      console.error('[RichReviews] Backend error:', e);
    });

    sendResponse({ acknowledged: true });
    return;
  }

  if (request.type === 'INGESTION_SUCCESS' && request.productName) {
    const { productName } = request;

    chrome.storage.local.set({
      lastProduct: productName,
      lastIngestionTime: Date.now(),
      ingestionStatus: 'success'
    });

    broadcastToAllContexts({ type: 'PRODUCT_DETECTED', productName });
    sendResponse({ acknowledged: true });
    return;
  }

  if (request.type === 'GET_CURRENT_PRODUCT') {
    chrome.storage.local.get(['lastProduct', 'activeProduct'], (result) => {
      const productName = result.activeProduct || result.lastProduct || null;
      sendResponse({ productName });
    });
    return true;
  }

  if (request.type === 'GET_INGESTION_STATUS') {
    chrome.storage.local.get(
      ['ingestionStatus', 'ingestionError', 'lastIngestionTime', 'activeProduct'],
      (result) => {
        sendResponse({
          status: result.ingestionStatus || 'idle',
          error: result.ingestionError || null,
          lastTime: result.lastIngestionTime || null,
          product: result.activeProduct || null
        });
      }
    );
    return true;
  }

  if (request.type === 'OPEN_SIDE_PANEL') {
    if (sender.tab) {
      try {
        chrome.sidePanel.open({ tabId: sender.tab.id });
        sendResponse({ opened: true });
      } catch (e) {
        console.error('[OPEN_SIDE_PANEL] Error:', e);
        sendResponse({ opened: false, error: e.message });
      }
    }
    return;
  }
});

console.log('[Background] Service worker initialized');