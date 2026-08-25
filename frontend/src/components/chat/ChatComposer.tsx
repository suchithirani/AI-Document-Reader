import React, { useState } from 'react'
import { Paperclip, Send, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/Button'

export interface ChatComposerProps {
  onSend?: (message: string, detailLevel: string) => void
  disabled?: boolean
  placeholder?: string
  className?: string
}

export function ChatComposer({
  onSend,
  disabled = false,
  placeholder = 'Ask a question about your documents...',
  className,
}: ChatComposerProps) {
  const [input, setInput] = useState('')
  const [detailLevel, setDetailLevel] = useState<'concise' | 'detailed' | 'bullet'>('detailed')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || disabled) return
    onSend?.(input.trim(), detailLevel)
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className={cn(
        'w-full p-2.5 sm:p-3 rounded-2xl border transition-all',
        'bg-[rgba(255,255,255,0.80)] border-[rgba(90,70,50,0.18)] dark:bg-[rgba(255,255,255,0.065)] dark:border-white/[0.12]',
        'backdrop-blur-xl shadow-md dark:shadow-2xl dark:shadow-black/60',
        className,
      )}
    >
      {/* Detail Level Selector & Document Context */}
      <div className="flex items-center justify-between pb-2 border-b border-[rgba(90,70,50,0.08)] dark:border-white/[0.06] text-xs">
        <div className="flex items-center gap-1.5">
          <span className="text-[11px] text-[#9A9187] dark:text-zinc-500 font-medium">
            Response:
          </span>
          {(['detailed', 'concise', 'bullet'] as const).map((level) => (
            <button
              key={level}
              type="button"
              onClick={() => setDetailLevel(level)}
              className={cn(
                'px-2 py-0.5 rounded-md text-[11px] font-medium capitalize transition-colors cursor-pointer',
                detailLevel === level
                  ? 'bg-[#E9E1D7] text-[#211C17] dark:bg-white/[0.12] dark:text-white font-semibold'
                  : 'text-[#71695F] hover:text-[#211C17] dark:text-zinc-400 dark:hover:text-white',
              )}
            >
              {level}
            </button>
          ))}
        </div>

        <div className="hidden sm:flex items-center gap-1 text-[11px] text-[#71695F] dark:text-zinc-400">
          <Sparkles className="w-3 h-3 text-[#886F4E] dark:text-[#A68A6A]" />
          <span>Hybrid RAG Active</span>
        </div>
      </div>

      {/* Input area */}
      <div className="flex items-end gap-2 pt-2">
        <button
          type="button"
          aria-label="Attach document context"
          className="p-2 rounded-xl text-[#71695F] hover:text-[#211C17] hover:bg-[#E9E1D7] dark:text-zinc-400 dark:hover:text-white dark:hover:bg-white/[0.08] transition-colors shrink-0 cursor-pointer"
        >
          <Paperclip className="w-4 h-4" />
        </button>

        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder={placeholder}
          rows={1}
          className="flex-1 max-h-32 min-h-[36px] py-1.5 px-2 bg-transparent text-sm text-[#211C17] dark:text-[#F5F5F5] placeholder:text-[#9A9187] dark:placeholder:text-zinc-500 focus:outline-none resize-none"
        />

        <Button
          type="submit"
          variant="primary"
          size="sm"
          disabled={disabled || !input.trim()}
          className="shrink-0 rounded-xl"
        >
          <Send className="w-3.5 h-3.5" />
        </Button>
      </div>
    </form>
  )
}
