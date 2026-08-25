import React from 'react'
import { Copy, Check, Sparkles, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { cn } from '@/lib/utils'
import { Citation, type CitationProps } from './Citation'

export interface ChatMessageProps {
  role: 'user' | 'assistant' | 'system'
  content: string
  citations?: Omit<CitationProps, 'onClick'>[]
  timestamp?: string
  isStreaming?: boolean
  onCitationClick?: (citation: Omit<CitationProps, 'onClick'>) => void
  className?: string
}

export function ChatMessage({
  role,
  content,
  citations = [],
  timestamp,
  isStreaming = false,
  onCitationClick,
  className,
}: ChatMessageProps) {
  const [copied, setCopied] = React.useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const isUser = role === 'user'

  return (
    <div
      className={cn(
        'group flex gap-3.5 py-4 text-left transition-colors',
        isUser ? 'justify-end' : 'justify-start',
        className,
      )}
    >
      {!isUser && (
        <div className="w-8 h-8 rounded-xl bg-[#886F4E] text-white dark:bg-[#A68A6A] dark:text-[#08090B] flex items-center justify-center shrink-0 shadow-xs mt-0.5">
          <Sparkles className="w-4 h-4" />
        </div>
      )}

      <div
        className={cn(
          'space-y-2.5 max-w-2xl',
          isUser && 'flex flex-col items-end',
        )}
      >
        <div
          className={cn(
            'p-4 rounded-2xl text-sm leading-relaxed',
            isUser
              ? 'bg-[#E9E1D7] text-[#211C17] border border-[#C8BBA6] dark:bg-[#1A1C20] dark:text-[#F5F5F5] dark:border-[#2A2D33] rounded-tr-xs'
              : 'bg-[rgba(255,255,255,0.60)] text-[#211C17] border border-[rgba(90,70,50,0.14)] dark:bg-[rgba(255,255,255,0.055)] dark:text-[#F5F5F5] dark:border-white/[0.10] rounded-tl-xs backdrop-blur-md shadow-xs',
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{content}</p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none space-y-2">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {content}
              </ReactMarkdown>
              {isStreaming && (
                <span className="inline-block w-1.5 h-4 ml-1 bg-[#886F4E] dark:bg-[#A68A6A] animate-pulse align-middle" />
              )}
            </div>
          )}
        </div>

        {/* Citations List */}
        {!isUser && citations.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 pt-1">
            <span className="text-[10px] uppercase tracking-wider font-semibold text-[#9A9187] dark:text-zinc-500 mr-1">
              Sources:
            </span>
            {citations.map((cite, idx) => (
              <Citation
                key={idx}
                documentName={cite.documentName}
                pageNumber={cite.pageNumber}
                score={cite.score}
                onClick={() => onCitationClick?.(cite)}
              />
            ))}
          </div>
        )}

        {/* Footer controls & timestamp */}
        <div className="flex items-center gap-2 px-1 text-[11px] text-[#9A9187] dark:text-zinc-500">
          {timestamp && <span>{timestamp}</span>}
          {!isUser && (
            <button
              type="button"
              onClick={handleCopy}
              aria-label="Copy message"
              className="opacity-0 group-hover:opacity-100 transition-opacity p-1 rounded hover:bg-[#E9E1D7] dark:hover:bg-white/[0.08] text-[#71695F] dark:text-zinc-400 cursor-pointer"
            >
              {copied ? (
                <Check className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
              ) : (
                <Copy className="w-3 h-3" />
              )}
            </button>
          )}
        </div>
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-[#E9E1D7] text-[#211C17] dark:bg-white/[0.1] dark:text-zinc-200 flex items-center justify-center shrink-0 text-xs font-semibold mt-0.5">
          <User className="w-4 h-4" />
        </div>
      )}
    </div>
  )
}
