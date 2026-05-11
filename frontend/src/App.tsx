import { useState, useEffect } from 'react';
import { sendChatQuery, type ChatResponse } from './services/chatService';
import { RetrievedChunkPanel } from './components/RetrievedChunkPanel';
import { DiagnosticPanel } from './components/DiagnosticPanel';
import { Skeleton, Badge, cn } from './components/ui/primitives';
import { Send, Copy, AlertCircle, Bot, User, Check, Clock, Zap } from 'lucide-react';

interface SidePanelMessage {
  source?: string;
  type: string;
  productName?: string;
  query?: string;
  requestId?: string;
  response?: any;
}

const App = () => {
  const [query, setQuery] = useState('');
  const [productId, setProductId] = useState('Redmi 15 5G');
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [recentProducts, setRecentProducts] = useState<string[]>(['Redmi 15 5G']);
  const [copied, setCopied] = useState(false);
  const [isInSidePanel, setIsInSidePanel] = useState(false);
  const [pendingChatRequests, setPendingChatRequests] = useState<Map<string, (response: any) => void>>(new Map());

  /**
   * Check if running in side panel context and setup communication
   */
  useEffect(() => {
    // Detect if we're in a side panel (iframe)
    const inSidePanel = window !== window.parent;
    setIsInSidePanel(inSidePanel);

    if (inSidePanel) {
      console.log('[App] Running in side panel mode');
      
      // Listen for messages from the side panel script
      const handleSidePanelMessage = (event: MessageEvent) => {
        const message = event.data as SidePanelMessage;

        console.log('[App] Received message from side panel:', message.type, message);

        if (message.type === 'SET_PRODUCT') {
          // Auto-set the product name from the side panel
          if (message.productName) {
            console.log('[App] Setting product from side panel:', message.productName);
            setProductId(message.productName);
            setRecentProducts(prev => {
              const product = message.productName ?? "";

            if (product && !prev.includes(product)) {
              return [product, ...prev].slice(0, 5);
          }

          return prev;
        });
          }
        } else if (message.type === 'UPDATE_PRODUCT') {
          // Update product when changed on shopping page
          if (message.productName) {
            console.log('[App] Updating product from side panel:', message.productName);
            setProductId(message.productName);
            setRecentProducts(prev => {
              const product = message.productName ?? "";

              if (product && !prev.includes(product)) {
                return [product, ...prev].slice(0, 5);
              }

              return prev;
            });
          }
        } else if (message.type === 'CHAT_RESPONSE') {
          // Handle async chat responses
          if (!message.requestId) return;

          const callback = pendingChatRequests.get(message.requestId);
          if (callback) {
            callback(message.response);
            setPendingChatRequests(prev => {
              const newMap = new Map(prev);
              newMap.delete(message.requestId!);
              return newMap;
            });
          }
        }
      };

      window.addEventListener('message', handleSidePanelMessage);

      // Tell the side panel that the app is ready
      window.parent.postMessage({ type: 'APP_READY' }, '*');

      return () => {
        window.removeEventListener('message', handleSidePanelMessage);
      };
    } else {
      // Standard chrome extension or direct frontend mode
      const isChromeExtension = typeof (window as any).chrome !== 'undefined' && 
                               (window as any).chrome.runtime && 
                               (window as any).chrome.runtime.onMessage;
      
      if (isChromeExtension) {
        // Listener for chrome.runtime.onMessage (direct messages)
        const listener = (request: any) => {
          if (request.type === 'PRODUCT_DETECTED' && request.productName) {
            setProductId(request.productName);
            setRecentProducts(prev => {
              const product = request.productName ?? "";

              if (product && !prev.includes(product)) {
                return [product, ...prev].slice(0, 5);
              }

              return prev;
            });
          }
        };
        
        // Listener for window.postMessage (from content script)
        const windowMessageListener = (event: MessageEvent) => {
          if (event.source !== window) return;
          
          if (event.data.type === 'FROM_EXTENSION' && event.data.contentType === 'PRODUCT_DETECTED' && event.data.productName) {
            setProductId(event.data.productName);
            setRecentProducts(prev => {
              const product = event.data.productName ?? "";

              if (product && !prev.includes(product)) {
                return [product, ...prev].slice(0, 5);
              }

            return prev;
            });
          }
        };
        
        (window as any).chrome.runtime.onMessage.addListener(listener);
        window.addEventListener('message', windowMessageListener);
        
        // Request current product immediately on mount
        (window as any).chrome.runtime.sendMessage({ type: "GET_CURRENT_PRODUCT" }, (response: any) => {
          if (response && response.productName) {
            setProductId(response.productName);
            setRecentProducts(prev => {
              const product = response.productName ?? "";

              if (product && !prev.includes(product)) {
                return [product, ...prev].slice(0, 5);
              } 

              return prev;
            });
          }
        });
        
        return () => {
          (window as any).chrome.runtime.onMessage.removeListener(listener);
          window.removeEventListener('message', windowMessageListener);
        };
      }
    }
  }, []);

  /**
   * Send chat result back to side panel if running in iframe
   */
  const sendResponseToSidePanel = (data: any) => {
    if (isInSidePanel) {
      window.parent.postMessage({
        type: 'CHAT_RESULT',
        response: data
      }, '*');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setResponse(null);
    setCopied(false);
    
    // Add to recent products if new
    if (productId.trim() && !recentProducts.includes(productId.trim())) {
      setRecentProducts(prev => [productId.trim(), ...prev].slice(0, 5));
    }

    const res = await sendChatQuery(query, productId);
    setResponse(res);
    setLoading(false);

    // Send response to side panel if applicable
    sendResponseToSidePanel(res);
  };

  const handleCopy = () => {
    if (response?.answer) {
      navigator.clipboard.writeText(response.answer);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden font-sans">
      
      {/* TOP HEADER */}
      <div className="p-3 border-b bg-muted/30 flex flex-col shrink-0">
        <div className="flex items-center gap-2 mb-2">
          <Zap className="w-5 h-5 text-primary" />
          <h1 className="text-base font-bold">RAG Assistant</h1>
          {isInSidePanel && <Badge variant="outline" className="text-[10px] ml-auto">Side Panel</Badge>}
        </div>
        
        <div className="flex items-center bg-background border rounded-md px-2 py-1.5 shadow-sm">
          <Bot className="w-4 h-4 text-muted-foreground mr-2 shrink-0" />
          <input
            type="text"
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
            className="w-full text-sm bg-transparent focus:outline-none"
            placeholder="Waiting for product detection..."
          />
          {productId && <Badge variant="success" className="ml-2 text-[10px] px-1 py-0 h-4">Active</Badge>}
        </div>
      </div>

      {/* CENTER CHAT AREA */}
      <div className="flex-1 flex flex-col min-w-0 bg-background relative">
        <div className="flex-1 overflow-y-auto p-6 md:p-10 custom-scrollbar">
          
          {/* Welcome State */}
          {!loading && !response && (
            <div className="h-full flex flex-col items-center justify-center text-center opacity-60 mt-10">
              <Bot className="w-12 h-12 text-muted-foreground mb-4" />
              <h2 className="text-sm font-semibold mb-2">Ready to query</h2>
              <p className="text-xs text-muted-foreground">
                {isInSidePanel 
                  ? 'Product detected! Enter a query to start RAG analysis.'
                  : 'The extension will auto-detect products. Enter a query below to start RAG.'
                }
              </p>
            </div>
          )}

          {/* Loading Skeleton */}
          {loading && (
            <div className="max-w-3xl mx-auto space-y-8 animate-in fade-in duration-300">
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                  <User className="w-4 h-4 text-primary" />
                </div>
                <div className="mt-1">
                  <div className="text-sm font-medium mb-1">You</div>
                  <div className="text-foreground">{query}</div>
                </div>
              </div>
              
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0 dark:bg-blue-900">
                  <Bot className="w-4 h-4 text-blue-600 dark:text-blue-300" />
                </div>
                <div className="mt-1 w-full max-w-2xl">
                  <div className="text-sm font-medium mb-2 flex items-center gap-2">
                    System <Badge variant="secondary" className="animate-pulse">Retrieving & Generating...</Badge>
                  </div>
                  <Skeleton className="h-4 w-full mb-2" />
                  <Skeleton className="h-4 w-[90%] mb-2" />
                  <Skeleton className="h-4 w-[95%] mb-2" />
                  <Skeleton className="h-4 w-[60%]" />
                </div>
              </div>
            </div>
          )}

          {/* Response Bubble */}
          {response && !loading && (
            <div className="max-w-3xl mx-auto space-y-8 animate-in slide-in-from-bottom-4 duration-300 pb-10">
              
              {/* User Query */}
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                  <User className="w-4 h-4 text-primary" />
                </div>
                <div className="mt-1">
                  <div className="text-sm font-medium mb-1">You</div>
                  <div className="text-foreground">{query}</div>
                </div>
              </div>

              {/* LLM Response */}
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center shrink-0 dark:bg-blue-900">
                  <Bot className="w-4 h-4 text-blue-600 dark:text-blue-300" />
                </div>
                <div className="mt-1 flex-1">
                  <div className="text-sm font-medium mb-2 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      System
                      {response.error ? (
                        <Badge variant="destructive">Error</Badge>
                      ) : (
                        <>
                          <Badge variant="outline" className="text-xs font-normal">Intent: {response.intent}</Badge>
                          <Badge variant="secondary" className="text-xs font-normal">
                            Conf: {Math.round(response.confidence_score * 100)}%
                          </Badge>
                          {response.latency_ms && (
                            <span className="text-xs text-muted-foreground flex items-center">
                              <Clock className="w-3 h-3 mr-1" /> {response.latency_ms}ms
                            </span>
                          )}
                        </>
                      )}
                    </div>
                    
                    {!response.error && response.answer && (
                      <button 
                        onClick={handleCopy}
                        className="text-muted-foreground hover:text-foreground transition-colors p-1"
                        title="Copy to clipboard"
                      >
                        {copied ? <Check className="w-4 h-4 text-green-500" /> : <Copy className="w-4 h-4" />}
                      </button>
                    )}
                  </div>

                  <div className={cn(
                    "prose prose-sm dark:prose-invert max-w-none leading-relaxed",
                    response.error ? "text-destructive" : "text-foreground"
                  )}>
                    {response.error ? (
                      <div className="flex items-center gap-2 p-3 border border-destructive/20 bg-destructive/10 rounded-md">
                        <AlertCircle className="w-5 h-5 shrink-0" />
                        {response.error}
                      </div>
                    ) : (
                      response.answer.includes("insufficient product data") ? (
                         <div className="p-3 border border-yellow-200 bg-yellow-50 dark:bg-yellow-900/20 dark:border-yellow-900 rounded-md text-yellow-800 dark:text-yellow-200 flex items-start gap-2">
                           <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                           {response.answer}
                         </div>
                      ) : (
                        <div className="whitespace-pre-wrap">{response.answer}</div>
                      )
                    )}
                  </div>

                  {/* Sources citations block */}
                  {!response.error && response.sources_used.length > 0 && (
                    <div className="mt-4 pt-4 border-t">
                      <p className="text-[10px] font-semibold text-muted-foreground mb-2 uppercase tracking-wider">Sources</p>
                      <ul className="text-[10px] text-muted-foreground space-y-1">
                        {response.sources_used.map((url, i) => (
                          <li key={i} className="truncate">
                            <a href={url} target="_blank" rel="noreferrer" className="text-primary hover:underline">
                              {url}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
              
              {/* Inline Retrieved Chunks for Side Panel */}
              {!response.error && response.retrieved_chunks && (
                <div className="mt-6 border-t pt-4">
                  <RetrievedChunkPanel chunks={response.retrieved_chunks} />
                </div>
              )}

              <DiagnosticPanel />

            </div>
          )}
        </div>

        {/* INPUT BOX */}
        <div className="p-3 border-t bg-background/80 backdrop-blur-sm shrink-0">
          <form onSubmit={handleSubmit} className="relative flex items-center">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask about the product..."
              disabled={loading}
              className="w-full p-3 pr-10 rounded-xl border bg-background text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="absolute right-2 p-1.5 rounded-lg bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 disabled:hover:bg-primary transition-colors"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default App;
