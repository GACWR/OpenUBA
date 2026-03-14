'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-provider'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft, Monitor, Square, RotateCcw, Trash2, ExternalLink, Loader2,
} from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-500/20 text-yellow-400',
  running: 'bg-blue-500/20 text-blue-400',
  completed: 'bg-green-500/20 text-green-400',
  failed: 'bg-red-500/20 text-red-400',
  stopped: 'bg-gray-500/20 text-gray-400',
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
  const [workspace, setWorkspace] = useState<Workspace | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  useEffect(() => {
    loadWorkspace()
  }, [params.id])

  const loadWorkspace = async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/workspaces/${params.id}`)
      if (res.ok) {
        const data = await res.json()
        setWorkspace(data)
      }
    } catch (err) {
      console.error('failed to load workspace:', err)
    } finally {
      setLoading(false)
    }
  }

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

  return (
    <div className="space-y-6">
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
          {workspace.status === 'running' && (
            <button
              onClick={handleStop}
              disabled={!!actionLoading}
              className="inline-flex items-center gap-1.5 rounded-md border border-white/10 px-3 py-2 text-sm font-medium hover:bg-yellow-500/10 hover:border-yellow-500/50 transition-colors disabled:opacity-50"
            >
              {actionLoading === 'stop' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Square className="h-4 w-4" />}
              Stop
            </button>
          )}
          {(workspace.status === 'stopped' || workspace.status === 'failed') && (
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

      {/* Details Card */}
      <div className="rounded-lg border border-white/10 bg-card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Workspace Details</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <DetailField label="Status">
            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[workspace.status] || 'bg-gray-500/20 text-gray-400'}`}>
              {workspace.status}
            </span>
          </DetailField>
          <DetailField label="Hardware Tier">
            <span className="font-mono text-sm">{workspace.hardware_tier}</span>
          </DetailField>
          {workspace.nodeport && (
            <DetailField label="Nodeport">
              <span className="font-mono text-sm">{workspace.nodeport}</span>
            </DetailField>
          )}
          <DetailField label="Created">
            <span className="text-sm">{new Date(workspace.created_at).toLocaleString()}</span>
          </DetailField>
          {workspace.environment && (
            <DetailField label="Environment">
              <span className="text-sm">{workspace.environment}</span>
            </DetailField>
          )}
          {workspace.access_url && workspace.status === 'running' && (
            <DetailField label="Access URL">
              <a
                href={workspace.access_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-blue-400 hover:underline"
              >
                Open <ExternalLink className="h-3 w-3" />
              </a>
            </DetailField>
          )}
        </div>
      </div>

      {/* Embedded iframe for running workspaces */}
      {workspace.status === 'running' && workspace.access_url && (
        <div className="rounded-lg border border-white/10 bg-card overflow-hidden">
          <div className="flex items-center justify-between px-4 py-2 border-b border-white/10 bg-muted/30">
            <span className="text-sm font-medium">Workspace Environment</span>
            <a
              href={workspace.access_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1 text-xs text-blue-400 hover:underline"
            >
              Open in new tab <ExternalLink className="h-3 w-3" />
            </a>
          </div>
          <iframe
            src={workspace.access_url}
            className="w-full border-0"
            style={{ height: 'calc(100vh - 360px)', minHeight: '500px' }}
            title={`Workspace: ${workspace.name}`}
            sandbox="allow-same-origin allow-scripts allow-popups allow-forms"
          />
        </div>
      )}
    </div>
  )
}

function DetailField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">{label}</span>
      <div className="mt-0.5">{children}</div>
    </div>
  )
}
