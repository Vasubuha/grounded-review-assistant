// Content script that runs on e-commerce pages
// Extracts product information and structured reviews, bridging background script to side panel

/**
 * Extract product name from Amazon product pages
 */
function extractAmazonProduct() {
  const titleSelectors = [
    'a[data-hook="product-link"]',
    'span#productTitle',
    'h1 span.a-size-large.product-title',
    'h1 span.a-size-large',
    'div[data-feature-name="title"] span.a-size-large'
  ];
  
  for (const selector of titleSelectors) {
    const element = document.querySelector(selector);
    if (element && element.textContent.trim().length > 0) {
      let productName = element.textContent.trim();
      productName = productName.replace(/\s*\([^)]*(?:GB|RAM|Storage|Color|Variant|variant)[^)]*\)/gi, '');
      if (productName.includes('|')) productName = productName.split('|')[0].trim();
      productName = productName.replace(/\s*[\[\(].*?(?:Processor|Snapdragon|Gen|Ghz|Battery|Camera|FPS|Gaming).*?[\]\)]/gi, '');
      productName = productName.replace(/\s+/g, ' ').trim();
      
      if (productName.length > 5 && productName.length < 150) {
        return productName;
      }
    }
  }
  return null;
}

/**
 * Extract product name from Flipkart product pages
 */
function extractFlipkartProduct() {
  const titleSelectors = [
    'div._2s4DIt', 'div.g2d-DF',
    'h1.B_NuCI', 'h1._6EBuvT', 'div[data-testid="productTitle"] h1', 'span.B_NuCI', 'div[data-qa="title"] h1'
  ];
  
  for (const selector of titleSelectors) {
    const element = document.querySelector(selector);
    if (element && element.textContent.trim().length > 0) {
      let productName = element.textContent.trim();
      productName = productName.replace(/\s*\([^)]*(?:GB|RAM|Storage|Color|Variant|variant)[^)]*\)/gi, '');
      if (productName.includes('|')) productName = productName.split('|')[0].trim();
      productName = productName.replace(/\s*[\[\(].*?(?:Processor|Snapdragon|Gen|Ghz|Battery|Camera|FPS|Gaming).*?[\]\)]/gi, '');
      productName = productName.replace(/\s+/g, ' ').trim();
      
      if (productName.length > 5 && productName.length < 150) {
        return productName;
      }
    }
  }
  return null;
}

function extractProductInfo() {
  const url = window.location.href;
  let productName = null;
  let platform = null;
  
  if (url.includes('amazon.')) {
    platform = 'amazon';
    productName = extractAmazonProduct();
  } else if (url.includes('flipkart.')) {
    platform = 'flipkart';
    productName = extractFlipkartProduct();
  } else {
    productName = document.title.split('-')[0].split('|')[0].replace(/Reviews/gi, '').trim();
  }
  
  // Fallback for review pages if selectors fail
  if (!productName || productName.length < 5) {
      productName = document.title.split(/Reviews|Amazon|Flipkart|-/i)[0].trim();
  }
  
  return { productName, platform, url };
}

/**
 * Amazon Review Extractor
 */
function extractAmazonReviews() {
  const reviews = [];
  const reviewNodes = document.querySelectorAll('div[data-hook="review"]');
  
  reviewNodes.forEach(node => {
    const bodyNode = node.querySelector('span[data-hook="review-body"]');
    const starNode = node.querySelector('i[data-hook="review-star-rating"] span, i[data-hook="cmps-review-star-rating"] span');
    const authorNode = node.querySelector('span.a-profile-name');
    const dateNode = node.querySelector('span[data-hook="review-date"]');
    const verifiedNode = node.querySelector('span[data-hook="avp-badge"]');
    const helpfulNode = node.querySelector('span[data-hook="helpful-vote-statement"]');
    
    if (bodyNode && bodyNode.textContent.trim().length > 15) {
      reviews.push({
        text: bodyNode.textContent.trim(),
        rating: starNode ? starNode.textContent.trim() : null,
        author: authorNode ? authorNode.textContent.trim() : null,
        date: dateNode ? dateNode.textContent.trim() : null,
        verified: !!verifiedNode,
        helpful_votes: helpfulNode ? helpfulNode.textContent.trim() : "0"
      });
    }
  });
  return reviews;
}

/**
 * Flipkart Review Extractor
 */
function extractFlipkartReviews() {
  const reviews = [];
  const reviewNodes = document.querySelectorAll('div.col._2wzgFH, div.col.EPCm59, div.RcXBOT');
  
  reviewNodes.forEach(node => {
    const bodyNode = node.querySelector('.t-ZTKy > div > div, .ZmyHeo > div > div');
    const starNode = node.querySelector('._3LWZlK, .XQDdHH');
    const authorNode = node.querySelector('._2sc7ZR, ._2NsDsF');
    const dateNode = node.querySelectorAll('._2sc7ZR, ._2NsDsF')[1];
    const helpfulNode = node.querySelector('._1LmwT9, ._2hkH1Z');
    
    if (bodyNode && bodyNode.textContent.trim().length > 15) {
      reviews.push({
        text: bodyNode.textContent.trim(),
        rating: starNode ? starNode.textContent.trim() : null,
        author: authorNode ? authorNode.textContent.trim() : null,
        date: dateNode ? dateNode.textContent.trim() : null,
        verified: true, // Standard for visible reviews
        helpful_votes: helpfulNode ? helpfulNode.textContent.trim() : "0"
      });
    }
  });
  return reviews;
}

/**
 * Auto-scroll to load dynamic reviews and trigger read-more expansions
 */
async function autoScrollAndExtract(platform) {
  return new Promise((resolve) => {
    let totalHeight = 0;
    let distance = 800;
    let maxScroll = 8000;
    
    let timer = setInterval(() => {
      let scrollHeight = document.body.scrollHeight;
      window.scrollBy(0, distance);
      totalHeight += distance;
      
      // Attempt to expand hidden text
      document.querySelectorAll('a.a-expander-header, span.a-expander-prompt').forEach(el => {
        if (el.textContent.includes('Read more') || el.textContent.includes('See more')) {
          try { el.click(); } catch(e) {}
        }
      });
      document.querySelectorAll('span._1BWGvX').forEach(el => { // Flipkart read more
        if (el.textContent.includes('READ MORE')) {
          try { el.click(); } catch(e) {}
        }
      });
      
      if (totalHeight >= scrollHeight || totalHeight > maxScroll) {
        clearInterval(timer);
        // Revert scroll to top
        window.scrollTo(0, 0);
        
        let extractedReviews = [];
        if (platform === 'amazon') extractedReviews = extractAmazonReviews();
        else if (platform === 'flipkart') extractedReviews = extractFlipkartReviews();
        
        resolve(extractedReviews);
      }
    }, 300);
  });
}

function navigateToReviewPageIfNeeded(platform) {
  const url = window.location.href;
  if (platform === 'amazon') {
    if (!url.includes('/product-reviews/')) {
      const reviewLink = document.querySelector('a[data-hook="see-all-reviews-link-foot"]');
      if (reviewLink && reviewLink.href) {
        window.location.replace(reviewLink.href);
        return true;
      }
      const dpMatch = url.match(/\/dp\/([A-Z0-9]{10})/);
      if (dpMatch && dpMatch[1]) {
        window.location.replace(`https://www.amazon.in/product-reviews/${dpMatch[1]}?reviewerType=all_reviews`);
        return true;
      }
    }
  } else if (platform === 'flipkart') {
    if (!url.includes('/product-reviews/')) {
      const reviewLink = document.querySelector('div.col.J-kEgu a, a[href*="/product-reviews/"]');
      if (reviewLink && reviewLink.href) {
        window.location.replace(reviewLink.href);
        return true;
      }
    }
  }
  return false;
}

/**
 * Send product and rich reviews to background
 */
async function sendProductAndReviewsToBackground() {
  const productInfo = extractProductInfo();
  
  if (productInfo.productName && productInfo.productName.length >= 5) {
    if (!productInfo.productName.includes('Amazon') && !productInfo.productName.includes('Flipkart')) {
      
      if (navigateToReviewPageIfNeeded(productInfo.platform)) {
        console.log('[Content] Navigating to dedicated review page...');
        return;
      }
      
      console.log('[Content] Waiting for reviews to render fully...');
      await new Promise(r => setTimeout(r, 3000));
      
      // Scroll and extract rich reviews
      const reviews = await autoScrollAndExtract(productInfo.platform);
      console.log(`[Content] Extracted ${reviews.length} structured reviews for ${productInfo.productName}`);
      
      chrome.runtime.sendMessage(
        {
          type: 'INGEST_RICH_REVIEWS',
          productName: productInfo.productName,
          platform: productInfo.platform,
          url: productInfo.url,
          reviews: reviews,
          timestamp: Date.now()
        },
        (response) => {
          if (!chrome.runtime.lastError) {
            console.log('[Content] Reviews sent to backend ingestion pipeline.');
          }
        }
      );
    }
  }
}

let ingestionTriggered = false;

// Trigger ingestion sequence on page load after a slight delay
setTimeout(() => {
  if (!ingestionTriggered) {
    ingestionTriggered = true;
    sendProductAndReviewsToBackground();
  }
}, 2000);

// Also listen for messages
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'GET_PRODUCT_INFO') {
    sendResponse(extractProductInfo());
  }
});
