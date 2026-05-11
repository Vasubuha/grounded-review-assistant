import { useState, useEffect } from 'react';
import { Card, Badge, cn } from './ui/primitives';
import { Activity, XCircle, RefreshCw } from 'lucide-react';

interface DiagnosticLog {
  timestamp: string;
  event_type: string;
  details: any;
}

export const DiagnosticPanel = () => {
  const [logs, setLogs] = useState<DiagnosticLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const res = await fetch(`${baseUrl}/api/v1/diagnostics`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data.logs || []);
      }
    } catch (e) {
      console.error("Failed to fetch diagnostics", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchLogs();
    }
  }, [isOpen]);

  if (!isOpen) {
    return (
      <div className="mt-4 pt-4 border-t">
        <button 
          onClick={() => setIsOpen(true)}
          className="text-[10px] uppercase font-bold text-muted-foreground flex items-center hover:text-primary transition-colors"
        >
          <Activity className="w-3 h-3 mr-2" /> Show Backend Diagnostics
        </button>
      </div>
    );
  }

  return (
    <div className="w-full bg-muted/5 border rounded-md flex flex-col overflow-hidden mt-6 shadow-inner animate-in fade-in slide-in-from-top-2 duration-300">
      <div className="p-2 bg-muted/20 border-b flex justify-between items-center">
        <h3 className="font-semibold text-[10px] flex items-center text-foreground uppercase tracking-wider">
          <Activity className="w-3 h-3 mr-2 text-primary" />
          Backend Diagnostics
          <Badge variant="secondary" className="ml-2 text-[9px] px-1 py-0">{logs.length} events</Badge>
        </h3>
        <div className="flex gap-2">
          <button onClick={fetchLogs} className="text-muted-foreground hover:text-primary transition-colors">
            <RefreshCw className={cn("w-3 h-3", loading ? "animate-spin" : "")} />
          </button>
          <button onClick={() => setIsOpen(false)} className="text-muted-foreground hover:text-destructive transition-colors">
            <XCircle className="w-3 h-3" />
          </button>
        </div>
      </div>
      
      <div className="p-3 max-h-64 overflow-y-auto custom-scrollbar bg-background/50">
        {logs.length === 0 ? (
          <div className="text-xs text-muted-foreground text-center py-4">No diagnostic events found</div>
        ) : (
          <div className="space-y-3">
            {logs.map((log, i) => (
              <Card key={i} className="p-2 text-[10px] border-border/50 bg-background/80">
                <div className="flex justify-between items-start mb-1.5">
                  <Badge variant={log.event_type === 'retrieval' ? 'default' : log.event_type.includes('failure') ? 'destructive' : 'secondary'} className="text-[9px] font-medium h-4">
                    {log.event_type.replace('_', ' ')}
                  </Badge>
                  <span className="text-muted-foreground opacity-70 font-mono text-[9px]">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                
                {log.event_type === 'validation_failure' && (
                  <div className="space-y-1">
                    <div>
                      <span className="font-semibold text-destructive mr-1">Reason:</span>
                      <span className="text-muted-foreground">{log.details.reason}</span>
                    </div>
                    <div className="font-mono bg-muted/40 border border-muted p-1.5 rounded text-[9px] overflow-hidden text-ellipsis whitespace-nowrap opacity-80">
                      {log.details.text_snippet}
                    </div>
                  </div>
                )}
                
                {log.event_type === 'duplicate_suppressed' && (
                  <div className="space-y-1">
                    <div>
                      <span className="font-semibold mr-1">Product:</span>
                      <span className="text-muted-foreground">{log.details.product_id}</span>
                    </div>
                    <div className="font-mono bg-muted/40 border border-muted p-1.5 rounded text-[9px] overflow-hidden text-ellipsis whitespace-nowrap opacity-60">
                      {log.details.text_snippet}
                    </div>
                  </div>
                )}

                {log.event_type === 'retrieval' && (
                  <div className="space-y-1">
                    <div>
                      <span className="font-semibold text-primary mr-1">Query:</span>
                      <span className="text-muted-foreground">{log.details.query}</span>
                    </div>
                    <div className="flex items-center text-muted-foreground gap-2">
                      <Badge variant="outline" className="text-[9px] h-4">
                        {log.details.retrieved_count} chunks retrieved
                      </Badge>
                    </div>
                  </div>
                )}
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
