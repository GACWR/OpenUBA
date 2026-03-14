'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-provider'
import Link from 'next/link'
import {
  Plus, Monitor, Square, Trash2, ExternalLink, Loader2, X, Play, RotateCcw,
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

export default function WorkspacesPage() {
  const { authFetch } = useAuth()
  const [workspaces, setWorkspaces] = useState<Workspace[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [launching, setLaunching] = useState(false)

  /* form state */
  const [formName, setFormName] = useState('')
  const [formTier, setFormTier] = useState('cpu-small')
  const [formEnv, setFormEnv] = useState('')

  useEffect(() => {
    loadWorkspaces()
  }, [])

  const loadWorkspaces = async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/workspaces`)
      if (res.ok) {
        const data = await res.json()
        setWorkspaces(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      console.error('failed to load workspaces:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleLaunch = async () => {
    if (!formName.trim()) return
    setLaunching(true)
    try {
      const res = await authFetch(`${API_URL}/api/v1/workspaces/launch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formName.trim(),
          hardware_tier: formTier,
          environment: formEnv.trim() || undefined,
        }),
      })
      if (res.ok) {
        setDialogOpen(false)
        setFormName('')
        setFormTier('cpu-small')
        setFormEnv('')
        await loadWorkspaces()
      }
    } catch (err) {
      console.error('failed to launch workspace:', err)
    } finally {
      setLaunching(false)
    }
  }

  const handleStop = async (id: string) => {
    try {
      await authFetch(`${API_URL}/api/v1/workspaces/${id}/stop`, { method: 'POST' })
      await loadWorkspaces()
    } catch (err) {
      console.error('failed to stop workspace:', err)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await authFetch(`${API_URL}/api/v1/workspaces/${id}`, { method: 'DELETE' })
      await loadWorkspaces()
    } catch (err) {
      console.error('failed to delete workspace:', err)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Workspaces</h1>
          <p className="text-muted-foreground">Interactive development environments for UBA model prototyping</p>
        </div>
        <button
          onClick={() => setDialogOpen(true)}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" /> Launch Workspace
        </button>
      </div>

      {loading ? (
        <div className="text-center text-muted-foreground py-12">Loading...</div>
      ) : workspaces.length === 0 ? (
        <div className="text-center text-muted-foreground py-12">
          <Monitor className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>No workspaces yet. Launch one to get started.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {workspaces.map((ws) => (
            <div key={ws.id} className="rounded-lg border border-white/10 bg-card p-4 space-y-3">
              <div className="flex items-center justify-between">
                <Link href={`/workspaces/${ws.id}`} className="font-medium hover:underline">
                  {ws.name}
                </Link>
                <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[ws.status] || 'bg-gray-500/20 text-gray-400'}`}>
                  {ws.status}
                </span>
              </div>

              <div className="space-y-1 text-sm text-muted-foreground">
                <div className="flex justify-between">
                  <span>Hardware</span>
                  <span className="font-mono text-foreground">{ws.hardware_tier}</span>
                </div>
                <div className="flex justify-between">
                  <span>IDE</span>
                  <span className="text-foreground">JupyterLab</span>
                </div>
                <div className="flex justify-between">
                  <span>Created</span>
                  <span>{new Date(ws.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-1">
                {ws.status === 'running' && (
                  <>
                    <Link
                      href={`/workspaces/${ws.id}`}
                      className="inline-flex items-center gap-1 rounded-md bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 transition-colors"
                    >
                      <Play className="h-3 w-3" /> Open
                    </Link>
                    <button
                      onClick={() => handleStop(ws.id)}
                      className="inline-flex items-center gap-1 rounded-md border border-white/10 px-3 py-1.5 text-xs font-medium hover:bg-yellow-500/10 hover:border-yellow-500/50 transition-colors"
                    >
                      <Square className="h-3 w-3" /> Stop
                    </button>
                  </>
                )}
                {(ws.status === 'stopped' || ws.status === 'failed') && (
                  <Link
                    href={`/workspaces/${ws.id}`}
                    className="inline-flex items-center gap-1 rounded-md border border-white/10 px-3 py-1.5 text-xs font-medium hover:bg-blue-500/10 hover:border-blue-500/50 transition-colors"
                  >
                    <RotateCcw className="h-3 w-3" /> Restart
                  </Link>
                )}
                {(ws.status === 'pending' || ws.status === 'creating') && (
                  <span className="inline-flex items-center gap-1 text-xs text-yellow-400">
                    <Loader2 className="h-3 w-3 animate-spin" /> Starting...
                  </span>
                )}
                <button
                  onClick={() => handleDelete(ws.id)}
                  className="inline-flex items-center gap-1 rounded-md border border-white/10 px-3 py-1.5 text-xs font-medium hover:bg-red-500/10 hover:border-red-500/50 transition-colors"
                >
                  <Trash2 className="h-3 w-3" /> Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Launch Workspace Dialog */}
      {dialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/50" onClick={() => setDialogOpen(false)} />
          <div className="relative z-50 w-full max-w-md rounded-lg border border-white/10 bg-background p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Launch Workspace</h2>
              <button onClick={() => setDialogOpen(false)} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-muted-foreground">Name</label>
                <input
                  type="text"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="my-workspace"
                  className="mt-1 w-full rounded-md border border-white/10 bg-muted/40 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              <div>
                <label className="text-sm font-medium text-muted-foreground">Hardware Tier</label>
                <select
                  value={formTier}
                  onChange={(e) => setFormTier(e.target.value)}
                  className="mt-1 w-full rounded-md border border-white/10 bg-muted/40 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="cpu-small">cpu-small</option>
                  <option value="cpu-large">cpu-large</option>
                  <option value="gpu-small">gpu-small</option>
                  <option value="gpu-large">gpu-large</option>
                </select>
              </div>

              <div>
                <label className="text-sm font-medium text-muted-foreground">Environment (optional)</label>
                <input
                  type="text"
                  value={formEnv}
                  onChange={(e) => setFormEnv(e.target.value)}
                  placeholder="e.g. python-3.11, pytorch-2.0"
                  className="mt-1 w-full rounded-md border border-white/10 bg-muted/40 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setDialogOpen(false)}
                className="rounded-md border border-white/10 px-4 py-2 text-sm font-medium hover:bg-muted/40 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleLaunch}
                disabled={launching || !formName.trim()}
                className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
                {launching && <Loader2 className="h-4 w-4 animate-spin" />}
                Launch
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
