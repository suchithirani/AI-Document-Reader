import React, { useState } from 'react'
import { Plus } from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { Button } from '@/components/ui/Button'
import { GlassCard } from '@/components/ui/GlassCard'
import { ChatMessage, type ChatMessageProps } from '@/components/chat/ChatMessage'
import { ChatComposer } from '@/components/chat/ChatComposer'

export function ChatPage() {
  const [messages, setMessages] = useState<ChatMessageProps[]>([
    {
      role: 'assistant',
      content:
        'Welcome to **AI Document Reader Intelligence**. You can query single documents or multi-document collections with grounded citations, OCR parsing, and hybrid vector search.',
      citations: [
        { documentName: 'sample_doc.pdf', pageNumber: 1, score: 0.94 },
      ],
      timestamp: 'Just now',
    },
  ])

  const handleSend = (userQuery: string) => {
    const newMsg: ChatMessageProps = {
      role: 'user',
      content: userQuery,
      timestamp: 'Just now',
    }
    setMessages((prev) => [...prev, newMsg])
  }

  return (
    <div className="space-y-4 md:space-y-6 text-left flex flex-col h-[calc(100vh-8rem)] lg:h-[calc(100vh-10rem)]">
      <PageHeader
        title="Chat & Intelligence"
        description="Interact with documents using RAG, hybrid search, citations, and streaming responses"
        actions={
          <Button
            variant="secondary"
            size="sm"
            leftIcon={<Plus className="w-3.5 h-3.5" />}
            onClick={() => setMessages([messages[0]])}
          >
            New Thread
          </Button>
        }
      />

      {/* Main Chat Workspace */}
      <GlassCard
        variant="default"
        className="flex-1 flex flex-col justify-between p-3 sm:p-5 min-h-0 overflow-hidden"
      >
        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto space-y-4 p-2 sm:p-4 pr-3">
          {messages.map((msg, i) => (
            <ChatMessage
              key={i}
              role={msg.role}
              content={msg.content}
              citations={msg.citations}
              timestamp={msg.timestamp}
              isStreaming={msg.isStreaming}
            />
          ))}
        </div>

        {/* Chat Composer */}
        <div className="pt-2">
          <ChatComposer onSend={handleSend} />
        </div>
      </GlassCard>
    </div>
  )
}
