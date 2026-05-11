import { useState } from 'react';
import { Badge, Card, cn } from './ui/primitives';
import type { RetrievedChunk } from '../services/chatService';
import { ChevronDown, ChevronRight, FileText, Play, ShoppingCart } from 'lucide-react';

const ChunkItem = ({ chunk, index }: { chunk: RetrievedChunk; index: number }) => {
  const [expanded, setExpanded] = useState(false);
  const isSpec = chunk.source.toLowerCase() === 'spec';
  const isYoutube = chunk.source.toLowerCase() === 'youtube';

  const textLength = chunk.text.length;
  const shouldTruncate = textLength > 200;
  
  const getSourceIcon = () => {
    if (isYoutube) return <Play className="w-4 h-4 mr-1 text-red-500" />;
    if (isSpec) return <FileText className="w-4 h-4 mr-1 text-blue-500" />;
    return <ShoppingCart className="w-4 h-4 mr-1 text-orange-500" />;
  };

  const getSentimentBadge = () => {
    if (!chunk.sentiment) return null;
    const s = chunk.sentiment.toUpperCase();
    if (s === 'POSITIVE') return <Badge variant="success">Positive</Badge>;
    if (s === 'NEGATIVE') return <Badge variant="destructive">Negative</Badge>;
    return <Badge variant="secondary">Neutral</Badge>;
  };

  return (
    <Card className={cn("p-3 mb-3 text-sm transition-all", isSpec ? "border-blue-200 bg-blue-50/30 dark:border-blue-900 dark:bg-blue-900/10" : "")}>
      <div className="flex justify-between items-start mb-2">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="outline" className="flex items-center">
            {getSourceIcon()}
            <span className="capitalize">{chunk.source}</span>
          </Badge>
          {getSentimentBadge()}
          {chunk.score !== undefined && (
            <Badge variant="secondary" title="CrossEncoder Rerank Score">
              Score: {chunk.score.toFixed(2)}
            </Badge>
          )}
        </div>
        <span className="text-xs text-muted-foreground font-mono">#{index + 1}</span>
      </div>
      
      <div className="mt-2 text-foreground/90 whitespace-pre-wrap leading-relaxed">
        {shouldTruncate && !expanded ? (
          <>
            {chunk.text.substring(0, 200)}...
            <button 
              onClick={() => setExpanded(true)} 
              className="text-primary hover:underline ml-1 font-medium text-xs"
            >
              Show more
            </button>
          </>
        ) : (
          <>
            {chunk.text}
            {shouldTruncate && expanded && (
              <button 
                onClick={() => setExpanded(false)} 
                className="block mt-2 text-primary hover:underline font-medium text-xs"
              >
                Show less
              </button>
            )}
          </>
        )}
      </div>
    </Card>
  );
};

export const RetrievedChunkPanel = ({ chunks }: { chunks: RetrievedChunk[] }) => {
  const [isOpen, setIsOpen] = useState(true);

  if (!chunks || chunks.length === 0) return null;

  const specChunks = chunks.filter(c => c.source.toLowerCase() === 'spec');
  const otherChunks = chunks.filter(c => c.source.toLowerCase() !== 'spec');

  return (
    <div className="w-full bg-muted/10 border rounded-md flex flex-col overflow-hidden mt-4">
      <div 
        className="p-3 bg-muted/20 border-b flex justify-between items-center cursor-pointer hover:bg-muted/40 transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div>
          <h3 className="font-semibold text-xs flex items-center">
            Retrieved Context
            <Badge variant="secondary" className="ml-2 text-[10px]">{chunks.length}</Badge>
          </h3>
        </div>
        {isOpen ? <ChevronDown className="w-4 h-4 text-muted-foreground" /> : <ChevronRight className="w-4 h-4 text-muted-foreground" />}
      </div>
      
      {isOpen && (
        <div className="p-3">
          {specChunks.length > 0 && (
            <div className="mb-4">
              <h4 className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-2 flex items-center">
                <FileText className="w-3 h-3 mr-1" />
                Specifications ({specChunks.length})
              </h4>
              {specChunks.map((c, i) => <ChunkItem key={`spec-${i}`} chunk={c} index={i} />)}
            </div>
          )}
          
          {otherChunks.length > 0 && (
            <div>
              <h4 className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground mb-2 flex items-center">
                <ShoppingCart className="w-3 h-3 mr-1" />
                Reviews & Opinions ({otherChunks.length})
              </h4>
              {otherChunks.map((c, i) => <ChunkItem key={`opinion-${i}`} chunk={c} index={specChunks.length + i} />)}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
