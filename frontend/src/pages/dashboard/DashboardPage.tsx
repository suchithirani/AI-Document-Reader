import React from 'react'
import {
  FileText,
  FolderKanban,
  MessageSquareQuote,
  Sparkles,
} from 'lucide-react'
import { PageHeader } from '@/components/ui/PageHeader'
import { GlassCard } from '@/components/ui/GlassCard'
import { Badge } from '@/components/ui/Badge'
import { StatusBadge } from '@/components/ui/StatusBadge'

export function DashboardPage() {
  return (
    <div className="space-y-6 text-left">
      <PageHeader
        title="Dashboard"
        description="System overview, document intelligence metrics, and platform status"
        badge={<Badge variant="default">Stage 3 Active</Badge>}
      />

      {/* 4 Responsive Metric Cards: Desktop 4-col, Tablet 2-col, Mobile 1-col */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Documents Card */}
        <GlassCard
          variant="default"
          className="p-5 flex flex-col justify-between hover:shadow-md transition-all duration-200"
        >
          <div className="flex items-center justify-between text-[#71695F] dark:text-[#A1A1AA]">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-[#EFE9E1] text-[#886F4E] dark:bg-white/[0.08] dark:text-[#A68A6A]">
                <FileText className="w-4 h-4" />
              </div>
              <span className="text-xs font-medium">Total Documents</span>
            </div>
            <FileText className="w-4 h-4 sm:hidden text-[#9A9187] dark:text-zinc-500" />
          </div>
          <div className="py-2.5">
            <div className="text-2xl sm:text-3xl font-bold tracking-tight text-[#211C17] dark:text-white">
              0
            </div>
          </div>
          <p className="text-[11px] text-[#9A9187] dark:text-zinc-500">
            PDF, PNG, JPG files
          </p>
        </GlassCard>

        {/* Active Collections Card */}
        <GlassCard
          variant="default"
          className="p-5 flex flex-col justify-between hover:shadow-md transition-all duration-200"
        >
          <div className="flex items-center justify-between text-[#71695F] dark:text-[#A1A1AA]">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-[#EFE9E1] text-[#886F4E] dark:bg-white/[0.08] dark:text-[#A68A6A]">
                <FolderKanban className="w-4 h-4" />
              </div>
              <span className="text-xs font-medium">Active Collections</span>
            </div>
            <FolderKanban className="w-4 h-4 sm:hidden text-[#9A9187] dark:text-zinc-500" />
          </div>
          <div className="py-2.5">
            <div className="text-2xl sm:text-3xl font-bold tracking-tight text-[#211C17] dark:text-white">
              0
            </div>
          </div>
          <p className="text-[11px] text-[#9A9187] dark:text-zinc-500">
            Grouped workspaces
          </p>
        </GlassCard>

        {/* Chat Sessions Card */}
        <GlassCard
          variant="default"
          className="p-5 flex flex-col justify-between hover:shadow-md transition-all duration-200"
        >
          <div className="flex items-center justify-between text-[#71695F] dark:text-[#A1A1AA]">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-[#EFE9E1] text-[#886F4E] dark:bg-white/[0.08] dark:text-[#A68A6A]">
                <MessageSquareQuote className="w-4 h-4" />
              </div>
              <span className="text-xs font-medium">Chat Sessions</span>
            </div>
            <MessageSquareQuote className="w-4 h-4 sm:hidden text-[#9A9187] dark:text-zinc-500" />
          </div>
          <div className="py-2.5">
            <div className="text-2xl sm:text-3xl font-bold tracking-tight text-[#211C17] dark:text-white">
              0
            </div>
          </div>
          <p className="text-[11px] text-[#9A9187] dark:text-zinc-500">
            RAG query threads
          </p>
        </GlassCard>

        {/* AI System Status Card */}
        <GlassCard
          variant="default"
          className="p-5 flex flex-col justify-between hover:shadow-md transition-all duration-200"
        >
          <div className="flex items-center justify-between text-[#71695F] dark:text-[#A1A1AA]">
            <div className="flex items-center gap-2.5">
              <div className="p-1.5 rounded-lg bg-[#EFE9E1] text-[#886F4E] dark:bg-white/[0.08] dark:text-[#A68A6A]">
                <Sparkles className="w-4 h-4" />
              </div>
              <span className="text-xs font-medium">AI System Status</span>
            </div>
            <Sparkles className="w-4 h-4 sm:hidden text-[#9A9187] dark:text-zinc-500" />
          </div>
          <div className="py-2.5">
            <StatusBadge status="READY" />
          </div>
          <p className="text-[11px] text-[#9A9187] dark:text-zinc-500">
            Hybrid Search + Vision
          </p>
        </GlassCard>
      </div>

      {/* Main Section: Recent Processing Activity */}
      <GlassCard variant="default" className="p-6 md:p-8 space-y-6">
        <div className="space-y-1 text-left">
          <h3 className="text-sm md:text-base font-semibold text-[#211C17] dark:text-white">
            Recent Processing Activity
          </h3>
          <p className="text-xs text-[#71695F] dark:text-[#A1A1AA] leading-relaxed">
            Dashboard activity, live query metrics, and system analytics will be connected in subsequent stages.
          </p>
        </div>

        {/* Clean minimal empty state matching mockup */}
        <div className="py-8 flex flex-col items-center justify-center text-center space-y-3">
          <div className="w-10 h-10 rounded-full bg-[#EFE9E1] text-[#886F4E] dark:bg-white/[0.08] dark:text-[#A68A6A] flex items-center justify-center shadow-xs">
            <FileText className="w-5 h-5" />
          </div>
          <div className="space-y-0.5 max-w-sm">
            <h4 className="text-sm font-semibold text-[#211C17] dark:text-white">
              No recent activity
            </h4>
            <p className="text-xs text-[#71695F] dark:text-[#A1A1AA]">
              Activity will appear here once processing begins
            </p>
          </div>
        </div>
      </GlassCard>
    </div>
  )
}
