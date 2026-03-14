'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-provider'
import Link from 'next/link'
import {
  Plus, GitBranch, X, Loader2, Play, Trash2,
} from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-500/20 text-yellow-400',
  running: 'bg-blue-500/20 text-blue-400',
  completed: 'bg-green-500/20 text-green-400',
  failed: 'bg-red-500/20 text-red-400',
  idle: 'bg-gray-500/20 text-gray-400',
}

interface Pipeline {
  id: string
  name: string
  description?: string
  steps?: any[]
  step_count?: number
  status?: string
  last_run_at?: string
  created_at: string
  updated_at?: string
}

export default function PipelinesPage() {
  const { authFetch } = useAuth()
  const [items, setItems] = useState<Pipeline[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [creating, setCreating] = useState(false)

  const [formName, setFormName] = useState('')
  const [formDescription, setFormDescription] = useState('')
  const [formSteps, setFormSteps] = useState('[\n  {"type": "training", "model_id": "", "hardware_tier": "cpu-small"}\n]')

  useEffect(() => { loadItems() }, [])

  const loadItems = async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/pipelines`)
      if (res.ok) {
        const data = await res.json()
        setItems(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      console.error('failed to load pipelines:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!formName.trim()) return
    setCreating(true)
    try {
      let steps = []
      try { steps = JSON.parse(formSteps) } catch {}
      const res = await authFetch(`${API_URL}/api/v1/pipelines`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formName.trim(),
          description: formDescription.trim() || undefined,
          steps,
        }),
      })
      if (res.ok) {
        setDialogOpen(false)
        setFormName('')
        setFormDescription('')
        setFormSteps('[\n  {"type": "training", "model_id": "", "hardware_tier": "cpu-small"}\n]')
        await loadItems()
      }
    } catch (err) {
      console.error('failed to create pipeline:', err)
    } finally {
      setCreating(false)
    }
  }

  const handleRun = async (id: string) => {
    try {
      await authFetch(`${API_URL}/api/v1/pipelines/${id}/run`, { method: 'POST' })
      await loadItems()
    } catch (err) {
      console.error('failed to run pipeline:', err)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      await authFetch(`${API_URL}/api/v1/pipelines/${id}`, { method: 'DELETE' })
      await loadItems()
    } catch (err) {
      console.error('failed to delete pipeline:', err)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Pipelines</h1>
          <p className="text-muted-foreground">Multi-step workflow automation</p>
        </div>
        <button
          onClick={() => setDialogOpen(true)}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" /> Create Pipeline
        </button>
      </div>

      {loading ? (
        <div className="text-center text-muted-foreground py-12">Loading...</div>
      ) : items.length === 0 ? (
        <div className="text-center text-muted-foreground py-12">
          <GitBranch className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>No pipelines yet. Create one to get started.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map((pipeline) => (
            <div key={pipeline.id} className="rounded-lg border border-white/10 bg-card p-4 space-y-3">
              <div className="flex items-center justify-between">
                <Link href={`/pipelines/${pipeline.id}`} className="font-medium hover:underline">
                  {pipeline.name}
                </Link>
                {pipeline.status && (
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[pipeline.status] || 'bg-gray-500/20 text-gray-400'}`}>
                    {pipeline.status}
                  </span>
                )}
              </div>
              {pipeline.description && (
                <p className="text-sm text-muted-foreground line-clamp-2">{pipeline.description}</p>
              )}

              <div className="space-y-1 text-sm text-muted-foreground">
                <div className="flex justify-between">
                  <span>Steps</span>
                  <span className="font-mono text-foreground">
                    {pipeline.step_count ?? pipeline.steps?.length ?? 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Created</span>
                  <span>{new Date(pipeline.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-1">
                <button
                  onClick={() => handleRun(pipeline.id)}
                  className="inline-flex items-center gap-1 rounded-md bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 transition-colors"
                >
                  <Play className="h-3 w-3" /> Run
                </button>
                <button
                  onClick={() => handleDelete(pipeline.id)}
                  className="inline-flex items-center gap-1 rounded-md border border-white/10 px-3 py-1.5 text-xs font-medium hover:bg-red-500/10 hover:border-red-500/50 transition-colors"
                >
                  <Trash2 className="h-3 w-3" /> Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Pipeline Dialog */}
      {dialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/50" onClick={() => setDialogOpen(false)} />
          <div className="relative z-50 w-full max-w-md rounded-lg border border-white/10 bg-background p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Create Pipeline</h2>
              <button onClick={() => setDialogOpen(false)} className="text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-sm font-medium text-muted-foreground">Name</label>
                <input type="text" value={formName} onChange={(e) => setFormName(e.target.value)} placeholder="my-pipeline" className="mt-1 w-full rounded-md border border-white/10 bg-muted/40 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring" />
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Description</label>
                <textarea value={formDescription} onChange={(e) => setFormDescription(e.target.value)} placeholder="Pipeline description..." rows={2} className="mt-1 w-full rounded-md border border-white/10 bg-muted/40 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring resize-none" />
              </div>
              <div>
                <label className="text-sm font-medium text-muted-foreground">Steps (JSON)</label>
                <textarea value={formSteps} onChange={(e) => setFormSteps(e.target.value)} rows={6} className="mt-1 w-full rounded-md border border-white/10 bg-muted/40 px-3 py-2 text-sm font-mono focus:outline-none focus:ring-2 focus:ring-ring resize-none" />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setDialogOpen(false)} className="rounded-md border border-white/10 px-4 py-2 text-sm font-medium hover:bg-muted/40 transition-colors">Cancel</button>
              <button onClick={handleCreate} disabled={creating || !formName.trim()} className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
                {creating && <Loader2 className="h-4 w-4 animate-spin" />}
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
