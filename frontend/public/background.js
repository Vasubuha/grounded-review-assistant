// Initialize the side panel to open on extension icon click
chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch((error) => console.error(error));

let lastDetectedProduct = "";

// Function injected into the page to extract product name
function getProductName() {
  const url = window.location.href;
  const title = document.title;
  
  if (url.includes('amazon.')) {
    const productTitleEl = document.getElementById('productTitle');
    if (productTitleEl) return productTitleEl.innerText.trim();
  }
  
  if (url.includes('flipkart.')) {
    const titleEl = document.querySelector('.B_NuCI') || document.querySelector('.VU-Tns');
    if (titleEl) return titleEl.innerText.trim();
  }
  
  // Fallback to title parsing
  return title.split('-')[0].split('|')[0].trim();
}

// Helper to detect product and notify
async function detectAndSend(tabId, url) {
  if (!url || (!url.includes('amazon.') && !url.includes('flipkart.'))) return;
  
  try {
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tabId },
      func: getProductName,
    });
    
    if (result) {
      lastDetectedProduct = result;
      // Send to the React app (Side Panel)
      chrome.runtime.sendMessage({
        type: "PRODUCT_DETECTED",
        productName: result
      }).catch(() => {
        // Ignored. The side panel might not be open yet.
      });
      
      // Auto-trigger ingestion endpoint
      fetch('http://localhost:8000/api/v1/ingest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_query: result })
      }).catch(err => console.error("Auto-ingestion failed:", err));
    }
  } catch (err) {
    console.error("Script execution failed:", err);
  }
}

// Monitor tab updates (e.g. user navigates to a product page)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.active) {
    detectAndSend(tabId, tab.url);
  }
});

// Monitor tab activation (user switches to an existing product page)
chrome.tabs.onActivated.addListener(async (activeInfo) => {
  try {
    const tab = await chrome.tabs.get(activeInfo.tabId);
    detectAndSend(tab.id, tab.url);
  } catch (err) {
    console.error(err);
  }
});

// Listen for the Side Panel asking for the current product
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === "GET_CURRENT_PRODUCT") {
    // Try to detect immediately if not already cached, or return cached
    chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
      if (tabs.length > 0) {
        const tab = tabs[0];
        if (tab.url && (tab.url.includes('amazon.') || tab.url.includes('flipkart.'))) {
            try {
              const [{ result }] = await chrome.scripting.executeScript({
                target: { tabId: tab.id },
                func: getProductName,
              });
              if (result) {
                lastDetectedProduct = result;
                sendResponse({ productName: lastDetectedProduct });
              } else {
                 sendResponse({ productName: lastDetectedProduct });
              }
            } catch (e) {
               sendResponse({ productName: lastDetectedProduct });
            }
        } else {
            sendResponse({ productName: lastDetectedProduct });
        }
      } else {
        sendResponse({ productName: lastDetectedProduct });
      }
    });
    return true; // Keep message channel open for async response
  }
});
