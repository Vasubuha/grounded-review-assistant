document.addEventListener('DOMContentLoaded', () => {
  const input = document.getElementById('productInput');
  const btn = document.getElementById('ingestBtn');
  const status = document.getElementById('status');

  // Try to get current tab title as default product name
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs.length > 0) {
      const tab = tabs[0];
      // Get product from storage first (from content script extraction)
      chrome.storage.local.get(['activeProduct'], (result) => {
        if (result.activeProduct) {
          input.value = result.activeProduct;
        } else {
          // Fallback to tab title
          let title = tab.title.split('-')[0].split('|')[0].trim();
          input.value = title;
        }
      });
    }
  });

  btn.addEventListener('click', async () => {
    const productStr = input.value.trim();
    if (!productStr) return;

    btn.disabled = true;
    status.textContent = "Sending to backend...";

    try {
      const response = await fetch('https://grounded-review-assistant.onrender.com/api/v1/ingest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ product_query: productStr })
      });

      if (response.ok) {
        status.textContent = "Ingestion started successfully!";
        
        // Store the product in chrome storage for later retrieval
        chrome.storage.local.set({ lastProduct: productStr });
        
        // Send INGESTION_SUCCESS message to background script
        chrome.runtime.sendMessage(
          {
            type: 'INGESTION_SUCCESS',
            productName: productStr
          },
          (response) => {
            if (chrome.runtime.lastError) {
              console.log('Message sent (frontend may not be listening)');
            }
          }
        );

        // Open side panel for the current tab (THIS IS A USER GESTURE)
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          if (tabs.length > 0) {
            chrome.sidePanel.open({ tabId: tabs[0].id }, () => {
              if (chrome.runtime.lastError) {
                console.log('Side panel open error:', chrome.runtime.lastError);
              } else {
                console.log('[Popup] Side panel opened');
              }
            });
          }
        });
      } else {
        const errorData = await response.json();
        status.textContent = "Error: " + (errorData.detail || "Failed to start ingestion.");
      }
    } catch (error) {
      status.textContent = "Error connecting to backend.";
      console.error(error);
    } finally {
      btn.disabled = false;
    }
  });
});
