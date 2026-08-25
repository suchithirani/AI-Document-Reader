import React from 'react'
import {
  Activity,
  CheckCircle2,
  FileText,
  Layers,
  RefreshCw,
  Server,
  ShieldCheck,
  Sparkles,
  Zap,
} from 'lucide-react'
import { useHealth } from '@/hooks/useHealth'
import { GlassCard } from '@/components/ui/GlassCard'

export function ScaffoldStatusPage() {
  const { data: health, isLoading, isError, refetch, isFetching } = useHealth()

  const modules = [
    {
      name: 'API Client & Interceptors',
      desc: 'Axios with Bearer injection & refresh queue',
      icon: Server,
      status: 'Ready',
    },
    {
      name: 'ID Normalization Engine',
      desc: 'MongoDB _id / Pydantic id normalization',
      icon: Layers,
      status: 'Ready',
    },
    {
      name: 'State Store (Zustand)',
      desc: 'Normalized auth & persistent storage',
      icon: ShieldCheck,
      status: 'Ready',
    },
    {
      name: 'Data Fetching (React Query)',
      desc: 'Cached queries with automatic retries',
      icon: Zap,
      status: 'Ready',
    },
    {
      name: 'Design System',
      desc: 'Black + white glass aesthetic with backdrop blur',
      icon: Sparkles,
      status: 'Ready',
    },
    {
      name: 'Markdown & GFM Streamer',
      desc: 'Prepared for SSE streaming responses',
      icon: FileText,
      status: 'Ready',
    },
  ]

  return (
    <div className="min-h-screen bg-[#07080c] text-zinc-100 flex flex-col items-center justify-center p-6 relative overflow-hidden font-sans selection:bg-white/20 selection:text-white">
      {/* Background ambient lighting */}
      <div className="absolute top-[-10%] left-[20%] w-[500px] h-[500px] bg-white/[0.02] rounded-full blur-[140px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[20%] w-[500px] h-[500px] bg-zinc-500/[0.02] rounded-full blur-[140px] pointer-events-none" />

      <main className="w-full max-w-4xl space-y-8 z-10">
        {/* Header Title */}
        <header className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-white/[0.08] bg-white/[0.03] backdrop-blur-md text-xs font-medium text-zinc-400 tracking-wide uppercase">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Stage 1 • Architecture & Scaffold
          </div>
          <h1 className="text-4xl md:text-5xl font-semibold tracking-tight text-white">
            AI Document Reader
          </h1>
          <p className="text-zinc-400 text-sm md:text-base max-w-lg mx-auto leading-relaxed">
            Enterprise document intelligence platform frontend built with React 19, TypeScript,
            Vite, and Black & White glass surfaces.
          </p>
        </header>

        {/* Live Backend Connection Card */}
        <GlassCard variant="elevated" className="p-6 md:p-8 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-white/[0.06]">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-white/[0.06] border border-white/[0.1] text-zinc-200">
                <Activity className="w-5 h-5 text-zinc-200" />
              </div>
              <div>
                <h2 className="text-base font-medium text-white">Backend Connection Status</h2>
                <p className="text-xs text-zinc-400">Target: {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}</p>
              </div>
            </div>

            <button
              onClick={() => refetch()}
              disabled={isFetching}
              className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-xs font-medium bg-white/[0.06] hover:bg-white/[0.12] border border-white/[0.1] active:scale-95 transition-all cursor-pointer text-zinc-200 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isFetching ? 'animate-spin' : ''}`} />
              {isFetching ? 'Testing...' : 'Refresh Health'}
            </button>
          </div>

          {/* Health Status Box */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <GlassCard variant="subtle" className="p-4 space-y-1">
              <span className="text-xs text-zinc-500 font-medium">Server Status</span>
              <div className="flex items-center gap-2 pt-1">
                {isLoading ? (
                  <span className="text-xs text-zinc-400 animate-pulse">Connecting...</span>
                ) : isError ? (
                  <span className="text-xs font-medium text-rose-400">Offline / Unreachable</span>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className="text-sm font-medium text-emerald-400 capitalize">
                      {health?.status || 'Online'}
                    </span>
                  </>
                )}
              </div>
            </GlassCard>

            <GlassCard variant="subtle" className="p-4 space-y-1">
              <span className="text-xs text-zinc-500 font-medium">Backend Application</span>
              <div className="pt-1">
                <span className="text-sm font-medium text-zinc-200">
                  {health?.application || 'AI Document Reader'}
                </span>
              </div>
            </GlassCard>

            <GlassCard variant="subtle" className="p-4 space-y-1">
              <span className="text-xs text-zinc-500 font-medium">Version</span>
              <div className="pt-1">
                <span className="text-sm font-mono text-zinc-300">
                  v{health?.version || '1.0.0'}
                </span>
              </div>
            </GlassCard>
          </div>

          {isError && (
            <div className="p-3.5 rounded-xl bg-rose-500/[0.08] border border-rose-500/20 text-xs text-rose-300">
              <strong>Connection Notice:</strong> Unable to connect to backend at {import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}. Ensure backend container is running.
            </div>
          )}
        </GlassCard>

        {/* Scaffold Modules Grid */}
        <section className="space-y-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 px-1">
            Architectural Foundations Initialized
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {modules.map((mod) => {
              const Icon = mod.icon
              return (
                <GlassCard
                  key={mod.name}
                  variant="interactive"
                  className="p-5 flex items-start justify-between gap-4"
                >
                  <div className="flex items-start gap-3.5">
                    <div className="p-2 rounded-xl bg-white/[0.04] border border-white/[0.08] text-zinc-300 shrink-0">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="space-y-1">
                      <h4 className="text-sm font-medium text-zinc-100">{mod.name}</h4>
                      <p className="text-xs text-zinc-400 leading-relaxed">{mod.desc}</p>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded-md text-[10px] font-mono font-medium bg-emerald-500/[0.1] text-emerald-300 border border-emerald-500/20 shrink-0">
                    {mod.status}
                  </span>
                </GlassCard>
              )
            })}
          </div>
        </section>

        {/* Next Stage Roadmap Notice */}
        <footer className="text-center pt-4 text-xs text-zinc-500">
          Ready for <strong>Stage 2: Design System & Shared Components</strong> upon approval.
        </footer>
      </main>
    </div>
  )
}
