// Side Panel Script - Manages communication, state, and UI for the assistant panel

const BACKEND_URL = 'https://grounded-review-assistant.onrender.com';
const CHAT_ENDPOINT = '/api/v1/chat';

/**
 * Initialize the side panel
 */
async function initializeSidePanel() {
  console.log('[SidePanel] Initializing...');
  
  const productNameEl = document.getElementById('product-name');
  const statusBadgeEl = document.getElementById('status-badge');
  const loadingIndicator = document.getElementById('loading-indicator');
  const appContainer = document.getElementById('app-container');

  // Get current product from background
  chrome.runtime.sendMessage(
    { type: 'GET_CURRENT_PRODUCT' },
    (response) => {
      if (response && response.productName) {
        const productName = response.productName;
        console.log('[SidePanel] Current product:', productName);
        
        // Truncate long product names for display
        const displayName = productName.length > 50 
          ? productName.substring(0, 50) + '...' 
          : productName;
        productNameEl.textContent = displayName;
        productNameEl.title = productName; // Full name on hover
        statusBadgeEl.textContent = 'Active';
        statusBadgeEl.className = 'status-badge active';

        // Load the React app into the iframe with the product
        loadReactApp(productName);
      } else {
        productNameEl.textContent = 'No product detected';
        statusBadgeEl.textContent = 'Waiting';
      }
    }
  );

  // Listen for product changes
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.type === 'PRODUCT_DETECTED' || request.type === 'PRODUCT_DETECTED_FROM_PAGE') {
      const productName = request.productName;
      console.log('[SidePanel] Product changed:', productName);
      
      productNameEl.textContent = productName;
      statusBadgeEl.textContent = 'Active';
      statusBadgeEl.className = 'status-badge active';

      // Update the React app
      if (appContainer.style.display === 'block') {
        postMessageToApp({
          type: 'UPDATE_PRODUCT',
          productName: productName
        });
      } else {
        loadReactApp(productName);
      }

      sendResponse({ received: true });
    } else if (request.type === 'INGESTION_STARTED') {
      console.log('[SidePanel] Ingestion started for:', request.productName);
      statusBadgeEl.textContent = 'Ingesting';
      statusBadgeEl.className = 'status-badge loading';

      setTimeout(() => {
        statusBadgeEl.textContent = 'Ready';
        statusBadgeEl.className = 'status-badge active';
      }, 3000);
    }
  });
}

/**
 * Load the React app in the side panel
 */
function loadReactApp(productName) {
  const appContainer = document.getElementById('app-container');
  const loadingIndicator = document.getElementById('loading-indicator');

  // Create iframe for React app
  const iframe = document.createElement('iframe');
  iframe.id = 'react-app-iframe';
  iframe.src = 'https://grounded-review-assistant.vercel.app'; // Vite dev server or built frontend
  iframe.sandbox.add('allow-same-origin');
  iframe.sandbox.add('allow-scripts');
  iframe.sandbox.add('allow-forms');
  iframe.sandbox.add('allow-popups');

  let iframeLoadTimeout;
  
  // Wait for iframe to load
  iframe.onload = () => {
    clearTimeout(iframeLoadTimeout);
    console.log('[SidePanel] React app loaded in iframe');
    
    loadingIndicator.style.display = 'none';
    appContainer.style.display = 'block';

    // Give React time to mount, then inject product
    setTimeout(() => {
      console.log('[SidePanel] Injecting product into React app:', productName);
      postMessageToApp({
        type: 'SET_PRODUCT',
        productName: productName
      });
    }, 500);
  };

  // Fallback if iframe doesn't load within timeout
  iframeLoadTimeout = setTimeout(() => {
    console.warn('[SidePanel] Iframe load timeout, showing app anyway');
    loadingIndicator.style.display = 'none';
    appContainer.style.display = 'block';
    setTimeout(() => {
      postMessageToApp({
        type: 'SET_PRODUCT',
        productName: productName
      });
    }, 300);
  }, 3000);

  appContainer.appendChild(iframe);
}

/**
 * Post message to the React app inside iframe
 */
function postMessageToApp(message) {
  const iframe = document.getElementById('react-app-iframe');
  if (iframe && iframe.contentWindow) {
    try {
      // Use * for origin since we're in an extension iframe
      iframe.contentWindow.postMessage(
        {
          source: 'side-panel',
          ...message
        },
        '*'  // Allow any origin for localhost dev
      );
      console.log('[SidePanel] Posted message to app:', message.type);
    } catch (e) {
      console.error('[SidePanel] Error posting message:', e);
    }
  } else {
    console.warn('[SidePanel] Iframe not ready yet');
  }
}

/**
 * Intercept chat requests and handle them with product context
 */
async function forwardChatRequest(query, productName) {
  console.log('[SidePanel] Forwarding chat request:', query);

  try {
    const payload = { query };
    if (productName && productName.trim() !== '') {
      payload.product_id = productName;
    }

    const response = await fetch(`${BACKEND_URL}${CHAT_ENDPOINT}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('[SidePanel] Chat error:', error);
    return {
      answer: 'Failed to communicate with backend',
      error: error.message
    };
  }
}

/**
 * Listen for messages from the React app
 */
window.addEventListener('message', (event) => {
  if (event.source.frameElement?.id !== 'react-app-iframe') {
    return;
  }

  console.log('[SidePanel] Received message from app:', event.data.type);

  // Handle chat requests from React app
  if (event.data.type === 'CHAT_REQUEST') {
    const { query, productName } = event.data;

    forwardChatRequest(query, productName).then((response) => {
      // Send response back to React app
      postMessageToApp({
        type: 'CHAT_RESPONSE',
        requestId: event.data.requestId,
        response
      });
    });
  }

  // Handle product detection requests
  if (event.data.type === 'GET_PRODUCT_INFO') {
    chrome.runtime.sendMessage(
      { type: 'GET_CURRENT_PRODUCT' },
      (response) => {
        postMessageToApp({
          type: 'PRODUCT_INFO',
          productName: response?.productName || null
        });
      }
    );
  }

  // Handle side panel toggle requests
  if (event.data.type === 'OPEN_SIDE_PANEL') {
    chrome.runtime.sendMessage({ type: 'OPEN_SIDE_PANEL' });
  }
});

/**
 * Handle messages from the active tab to show detection status
 */
chrome.tabs.onActivated.addListener(() => {
  chrome.runtime.sendMessage(
    { type: 'GET_CURRENT_PRODUCT' },
    (response) => {
      if (response?.productName) {
        const productNameEl = document.getElementById('product-name');
        productNameEl.textContent = response.productName;
      }
    }
  );
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', initializeSidePanel);

console.log('[SidePanel] Script loaded');
