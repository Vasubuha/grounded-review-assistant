import logging
import json
from datetime import datetime
from collections import deque

class DiagnosticLogger:
    def __init__(self):
        self.logs = deque(maxlen=200)

    def log_event(self, event_type: str, details: dict):
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        self.logs.append(event)
        # Also print to console
        print(f"[DIAGNOSTICS] {event_type}: {json.dumps(details)[:500]}")

    def get_logs(self, limit: int = 50):
        # Return newest first
        return list(self.logs)[-limit:][::-1]

diagnostic_logger = DiagnosticLogger()

def log_validation_failure(text: str, reason: str, metadata: dict = None):
    diagnostic_logger.log_event("validation_failure", {
        "reason": reason,
        "text_snippet": text[:150] + "..." if len(text) > 150 else text,
        "metadata": metadata
    })

def log_duplicate_suppressed(product_id: str, text: str):
    diagnostic_logger.log_event("duplicate_suppressed", {
        "product_id": product_id,
        "text_snippet": text[:150] + "..." if len(text) > 150 else text
    })

def log_retrieval(query: str, chunks: list):
    diagnostic_logger.log_event("retrieval", {
        "query": query,
        "retrieved_count": len(chunks),
        "chunks": chunks
    })
