export interface RetrievedChunk {
  text: string;
  source: string;
  sentiment?: string;
  score?: number;
  url?: string;
}

export interface ChatResponse {
  answer: string;
  sources_used: string[];
  retrieved_chunks: RetrievedChunk[];
  intent: string;
  confidence_score: number;
  latency_ms?: number;
  error?: string;
}

export const sendChatQuery = async (query: string, productId?: string): Promise<ChatResponse> => {
  const startTime = Date.now();
  try {
    const payload: any = { query };
    if (productId && productId.trim() !== '') {
      payload.product_id = productId;
    }

    const res = await fetch('http://127.0.0.1:8000/api/v1/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      throw new Error(`Backend Error: ${res.statusText} (${res.status})`);
    }

    const data = await res.json();
    return {
      ...data,
      latency_ms: Date.now() - startTime,
    };
  } catch (err: any) {
    console.error("Chat API Failed:", err);
    return {
      answer: "Communication with the backend failed.",
      sources_used: [],
      retrieved_chunks: [],
      intent: "unknown",
      confidence_score: 0,
      error: err.message,
      latency_ms: Date.now() - startTime,
    };
  }
};
