// Service worker (background script) - handles detection, ingestion, and message routing

const BACKEND_URL = 'https://grounded-review-assistant.onrender.com';
const INGEST_ENDPOINT = '/api/v1/ingest';

/**
 * Store to track ingested products to avoid duplicate ingestions
 */
let ingestionState = {
  inProgress: {},
  completed: new Set()
};

/**
 * Auto-ingest product when detected
 */
async function autoIngestProduct(productName) {
  // Validate product name before ingesting
  if (!productName || productName.length < 5) {
    console.log(`[AutoIngest] Skipping invalid product name: "${productName}"`);
    return;
  }
  
  // Reject obvious non-products
  if (productName.includes('Amazon') || productName.includes('Flipkart') || 
      productName.includes('Great') || productName.includes('Sale') ||
      productName.includes('Buy') || productName.length > 150) {
    console.log(`[AutoIngest] Skipping suspicious product name: "${productName}"`);
    return;
  }

  // Prevent duplicate ingestions
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
      
      // Store in chrome storage
      chrome.storage.local.set({
        lastProduct: productName,
        lastIngestionTime: Date.now(),
        ingestionStatus: 'success'
      });

      // Broadcast ingestion success to side panel and popup
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

/**
 * Broadcast message to all extension contexts (side panel, popup, content scripts)
 */
function broadcastToAllContexts(message) {
  // Get all tabs and send message to each
  chrome.tabs.query({}, (tabs) => {
    tabs.forEach(tab => {
      chrome.tabs.sendMessage(tab.id, message).catch(() => {
        // Ignore errors for tabs that don't have content script
      });
    });
  });

  // Also store in sessionStorage for side panel to retrieve
  chrome.storage.session.set({
    lastBroadcast: message,
    broadcastTime: Date.now()
  });
}

/**
 * Handle tab activation - check for product on active tab
 */
chrome.tabs.onActivated.addListener((activeInfo) => {
  chrome.tabs.get(activeInfo.tabId, (tab) => {
    if (isShoppingPage(tab.url)) {
      console.log('[TabActivated] Shopping tab detected:', tab.url);
      
      // Request product info from content script
      chrome.tabs.sendMessage(
        activeInfo.tabId,
        { type: 'GET_PRODUCT_INFO' },
        (response) => {
          if (response && response.productName) {
            console.log('[TabActivated] Product detected:', response.productName);
            
            // Store current product
            chrome.storage.local.set({
              activeProduct: response.productName,
              activeProductPlatform: response.platform,
              activeProductUrl: response.url
            });

            // Auto-ingest (don't open side panel here - will be opened by popup/content script click)
            autoIngestProduct(response.productName);
          }
        }
      );
    }
  });
});

/**
 * Handle URL/title changes on active tab
 */
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && isShoppingPage(tab.url)) {
    console.log('[TabUpdated] Page loaded:', tab.url);
    
    // Wait for page to fully render
    setTimeout(() => {
      chrome.tabs.sendMessage(
        tabId,
        { type: 'GET_PRODUCT_INFO' },
        (response) => {
          if (response && response.productName) {
            console.log('[TabUpdated] Product detected:', response.productName);
            
            chrome.storage.local.set({
              activeProduct: response.productName,
              activeProductPlatform: response.platform,
              activeProductUrl: response.url
            });

            // Auto-ingest
            autoIngestProduct(response.productName);
          }
        }
      );
    }, 2000);
  }
});

/**
 * Check if URL is a shopping page
 */
function isShoppingPage(url) {
  if (!url) return false;
  return /amazon\.|flipkart\./.test(url);
}

/**
 * Listen for messages from content scripts, popup, and side panel
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('[MessageReceived]', request.type, 'from', sender.url);

  if (request.type === 'INGEST_RICH_REVIEWS') {
    const { productName, platform, url, reviews } = request;
    
    console.log(`[RichReviews] Received ${reviews.length} reviews for ${productName}`);
    
    // Validate product name
    if (!productName || productName.length < 5 || productName.includes('Amazon')) {
      sendResponse({ acknowledged: false });
      return;
    }
    
    chrome.storage.local.set({
      activeProduct: productName,
      activeProductPlatform: platform,
      activeProductUrl: url,
      productDetectionTime: request.timestamp
    });

    // Forward to FastAPI review ingestion endpoint
    fetch(`${BACKEND_URL}/api/v1/ingest/reviews`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        product_query: productName,
        platform: platform,
        url: url,
        reviews: reviews
      })
    }).then(r => r.json()).then(data => {
      console.log('[RichReviews] Sent to backend:', data);
    }).catch(e => {
      console.error('[RichReviews] Backend error:', e);
    });

    sendResponse({ acknowledged: true });
    return;
  }

  if (request.type === 'INGESTION_SUCCESS' && request.productName) {
    // Popup initiated ingestion
    const { productName } = request;
    
    chrome.storage.local.set({
      lastProduct: productName,
      lastIngestionTime: Date.now(),
      ingestionStatus: 'success'
    });

    // Broadcast to all contexts
    broadcastToAllContexts({
      type: 'PRODUCT_DETECTED',
      productName: productName
    });

    sendResponse({ acknowledged: true });
    return;
  }

  if (request.type === 'GET_CURRENT_PRODUCT') {
    // Popup/side panel requesting current product
    chrome.storage.local.get(['lastProduct', 'activeProduct'], (result) => {
      const productName = result.activeProduct || result.lastProduct || null;
      sendResponse({ productName });
    });
    return true; // Will respond asynchronously
  }

  if (request.type === 'GET_INGESTION_STATUS') {
    // Side panel requesting ingestion status
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
    // Explicit side panel open request (from popup or content script user click)
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


