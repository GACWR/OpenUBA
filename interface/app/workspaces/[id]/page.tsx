'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useAuth } from '@/lib/auth-provider'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft, Monitor, Square, RotateCcw, Trash2, ExternalLink, Loader2,
  RefreshCw, Maximize2,
} from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-500/20 text-yellow-400',
  creating: 'bg-yellow-500/20 text-yellow-400',
  running: 'bg-green-500/20 text-green-400',
  stopping: 'bg-orange-500/20 text-orange-400',
  stopped: 'bg-gray-500/20 text-gray-400',
  failed: 'bg-red-500/20 text-red-400',
}

interface Workspace {
  id: string
  name: string
  status: string
  hardware_tier: string
  environment?: string
  access_url?: string
  nodeport?: number
  created_at: string
}

export default function WorkspaceDetailPage({ params }: { params: { id: string } }) {
  const { authFetch } = useAuth()
  const router = useRouter()
  const iframeRef = useRef<HTMLIFrameElement>(null)
  const [workspace, setWorkspace] = useState<Workspace | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [wsReady, setWsReady] = useState(false)
  const [connecting, setConnecting] = useState(false)

  const loadWorkspace = useCallback(async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/workspaces/${params.id}`)
      if (res.ok) {
        const data = await res.json()
        setWorkspace(data)
        return data
      }
    } catch (err) {
      console.error('failed to load workspace:', err)
    } finally {
      setLoading(false)
    }
    return null
  }, [authFetch, params.id])

  // initial load
  useEffect(() => {
    loadWorkspace()
  }, [loadWorkspace])

  // poll workspace status while pending/creating (every 3s)
  useEffect(() => {
    if (!workspace) return
    if (workspace.status !== 'pending' && workspace.status !== 'creating') return

    const interval = setInterval(async () => {
      const ws = await loadWorkspace()
      if (ws && ws.status !== 'pending' && ws.status !== 'creating') {
        clearInterval(interval)
      }
    }, 3000)

    return () => clearInterval(interval)
  }, [workspace?.status, loadWorkspace])

  // probe JupyterLab readiness once workspace is running with access_url
  useEffect(() => {
    if (!workspace) return
    if (workspace.status !== 'running' || !workspace.access_url) return
    if (wsReady) return

    setConnecting(true)
    let cancelled = false

    const probe = async () => {
      while (!cancelled) {
        try {
          // use no-cors to avoid CORS issues during probing —
          // we just need to know if the server responds at all
          await fetch(workspace.access_url!, { mode: 'no-cors' })
          if (!cancelled) {
            setWsReady(true)
            setConnecting(false)
          }
          return
        } catch {
          // JupyterLab not ready yet, retry in 2s
          await new Promise((r) => setTimeout(r, 2000))
        }
      }
    }

    probe()

    return () => {
      cancelled = true
      setConnecting(false)
    }
  }, [workspace?.status, workspace?.access_url, wsReady])

  // reset readiness when workspace changes state
  useEffect(() => {
    if (workspace?.status !== 'running') {
      setWsReady(false)
    }
  }, [workspace?.status])

  const handleStop = async () => {
    setActionLoading('stop')
    try {
      await authFetch(`${API_URL}/api/v1/workspaces/${params.id}/stop`, { method: 'POST' })
      await loadWorkspace()
    } catch (err) {
      console.error('failed to stop workspace:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const handleRestart = async () => {
    setActionLoading('restart')
    setWsReady(false)
    try {
      await authFetch(`${API_URL}/api/v1/workspaces/${params.id}/restart`, { method: 'POST' })
      await loadWorkspace()
    } catch (err) {
      console.error('failed to restart workspace:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const handleDelete = async () => {
    setActionLoading('delete')
    try {
      const res = await authFetch(`${API_URL}/api/v1/workspaces/${params.id}`, { method: 'DELETE' })
      if (res.ok) {
        router.push('/workspaces')
      }
    } catch (err) {
      console.error('failed to delete workspace:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const handleRefreshIframe = () => {
    if (iframeRef.current) {
      iframeRef.current.src = iframeRef.current.src
    }
  }

  const handlePopOut = () => {
    if (workspace?.access_url) {
      window.open(workspace.access_url, '_blank', 'noopener,noreferrer')
    }
  }

  if (loading) {
    return <div className="text-center text-muted-foreground py-12">Loading...</div>
  }

  if (!workspace) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => router.push('/workspaces')}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Workspaces
        </button>
        <div className="text-center text-muted-foreground py-12">Workspace not found</div>
      </div>
    )
  }

  const isRunning = workspace.status === 'running'
  const isPending = workspace.status === 'pending' || workspace.status === 'creating'
  const isStopped = workspace.status === 'stopped' || workspace.status === 'failed'

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <button
            onClick={() => router.push('/workspaces')}
            className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-2"
          >
            <ArrowLeft className="h-4 w-4" /> Back to Workspaces
          </button>
          <div className="flex items-center gap-3">
            <Monitor className="h-6 w-6 text-violet-400" />
            <h1 className="text-2xl font-bold tracking-tight">{workspace.name}</h1>
            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${statusColors[workspace.status] || 'bg-gray-500/20 text-gray-400'}`}>
              {workspace.status}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isRunning && (
            <button
              onClick={handleStop}
              disabled={!!actionLoading}
              className="inline-flex items-center gap-1.5 rounded-md border border-white/10 px-3 py-2 text-sm font-medium hover:bg-yellow-500/10 hover:border-yellow-500/50 transition-colors disabled:opacity-50"
            >
              {actionLoading === 'stop' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Square className="h-4 w-4" />}
              Stop
            </button>
          )}
          {isStopped && (
            <button
              onClick={handleRestart}
              disabled={!!actionLoading}
              className="inline-flex items-center gap-1.5 rounded-md border border-white/10 px-3 py-2 text-sm font-medium hover:bg-blue-500/10 hover:border-blue-500/50 transition-colors disabled:opacity-50"
            >
              {actionLoading === 'restart' ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
              Restart
            </button>
          )}
          <button
            onClick={handleDelete}
            disabled={!!actionLoading}
            className="inline-flex items-center gap-1.5 rounded-md border border-white/10 px-3 py-2 text-sm font-medium hover:bg-red-500/10 hover:border-red-500/50 transition-colors disabled:opacity-50"
          >
            {actionLoading === 'delete' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
            Delete
          </button>
        </div>
      </div>

      {/* Details (compact when running) */}
      <div className="rounded-lg border border-white/10 bg-card px-4 py-3">
        <div className="flex items-center gap-6 text-sm text-muted-foreground">
          <div>
            <span className="text-[10px] uppercase tracking-wide">Hardware</span>
            <div className="font-mono text-foreground text-xs">{workspace.hardware_tier}</div>
          </div>
          {workspace.environment && (
            <div>
              <span className="text-[10px] uppercase tracking-wide">Environment</span>
              <div className="text-foreground text-xs">{workspace.environment}</div>
            </div>
          )}
          {workspace.nodeport && (
            <div>
              <span className="text-[10px] uppercase tracking-wide">Port</span>
              <div className="font-mono text-foreground text-xs">{workspace.nodeport}</div>
            </div>
          )}
          <div>
            <span className="text-[10px] uppercase tracking-wide">Created</span>
            <div className="text-foreground text-xs">{new Date(workspace.created_at).toLocaleString()}</div>
          </div>
        </div>
      </div>

      {/* Pending state */}
      {isPending && (
        <div className="rounded-lg border border-white/10 bg-card flex items-center justify-center py-24">
          <div className="text-center space-y-3">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-yellow-400" />
            <p className="text-muted-foreground">Starting workspace pod...</p>
            <p className="text-xs text-muted-foreground/60">This may take a moment while the container initializes</p>
          </div>
        </div>
      )}

      {/* Connecting state — workspace running but JupyterLab not ready yet */}
      {isRunning && workspace.access_url && connecting && !wsReady && (
        <div className="rounded-lg border border-white/10 bg-card flex items-center justify-center py-24">
          <div className="text-center space-y-3">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-blue-400" />
            <p className="text-muted-foreground">Connecting to workspace...</p>
            <p className="text-xs text-muted-foreground/60">Waiting for JupyterLab to become ready</p>
          </div>
        </div>
      )}

      {/* JupyterLab iframe — only shown when ready */}
      {isRunning && workspace.access_url && wsReady && (
        <div className="rounded-lg border border-white/10 bg-card overflow-hidden">
          {/* Toolbar */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-white/10 bg-muted/30">
            <div className="flex items-center gap-2">
              <span className="inline-flex h-2 w-2 rounded-full bg-green-400 animate-pulse" />
              <span className="text-sm font-medium">{workspace.name}</span>
              <span className="text-xs text-muted-foreground">JupyterLab</span>
            </div>
            <div className="flex items-center gap-1">
              <button
                onClick={handleRefreshIframe}
                className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                title="Refresh"
              >
                <RefreshCw className="h-3.5 w-3.5" /> Refresh
              </button>
              <button
                onClick={handlePopOut}
                className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors"
                title="Open in new window"
              >
                <Maximize2 className="h-3.5 w-3.5" /> Pop Out
              </button>
              <button
                onClick={handleStop}
                disabled={!!actionLoading}
                className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors disabled:opacity-50"
                title="Stop workspace"
              >
                <Square className="h-3.5 w-3.5" /> Stop
              </button>
            </div>
          </div>
          {/* Iframe: no sandbox, allow clipboard for JupyterLab interactivity */}
          <iframe
            ref={iframeRef}
            src={workspace.access_url}
            className="w-full border-0"
            style={{ height: 'calc(100vh - 240px)', minHeight: '600px' }}
            title={`JupyterLab: ${workspace.name}`}
            allow="clipboard-read; clipboard-write"
          />
        </div>
      )}

      {/* Stopped/Failed state */}
      {isStopped && (
        <div className="rounded-lg border border-white/10 bg-card flex items-center justify-center py-24">
          <div className="text-center space-y-3">
            <Monitor className="h-8 w-8 mx-auto text-muted-foreground/40" />
            <p className="text-muted-foreground">
              Workspace is {workspace.status}
            </p>
            <button
              onClick={handleRestart}
              disabled={!!actionLoading}
              className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {actionLoading === 'restart' ? <Loader2 className="h-4 w-4 animate-spin" /> : <RotateCcw className="h-4 w-4" />}
              Restart Workspace
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
