'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-provider'
import { useRouter } from 'next/navigation'
import {
  Plus, BarChart3, X, Loader2,
} from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const backendColors: Record<string, string> = {
  plotly: 'bg-blue-500/20 text-blue-400',
  recharts: 'bg-green-500/20 text-green-400',
  vega: 'bg-purple-500/20 text-purple-400',
  matplotlib: 'bg-orange-500/20 text-orange-400',
  d3: 'bg-yellow-500/20 text-yellow-400',
}

interface Visualization {
  id: string
  name: string
  backend: string
  spec?: any
  published: boolean
  created_at: string
  updated_at?: string
}

export default function VisualizationsPage() {
  const { authFetch } = useAuth()
  const router = useRouter()
  const [items, setItems] = useState<Visualization[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [creating, setCreating] = useState(false)

  /* form state */
  const [formName, setFormName] = useState('')
  const [formBackend, setFormBackend] = useState('plotly')

  useEffect(() => {
    loadItems()
  }, [])

  const loadItems = async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/visualizations`)
      if (res.ok) {
        const data = await res.json()
        setItems(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      console.error('failed to load visualizations:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!formName.trim()) return
    setCreating(true)
    try {
      const res = await authFetch(`${API_URL}/api/v1/visualizations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formName.trim(),
          backend: formBackend,
        }),
      })
      if (res.ok) {
        setDialogOpen(false)
        setFormName('')
        setFormBackend('plotly')
        await loadItems()
      }
    } catch (err) {
      console.error('failed to create visualization:', err)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Visualizations</h1>
          <p className="text-muted-foreground">Multi-backend visualization framework</p>
        </div>
        <button
          onClick={() => setDialogOpen(true)}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" /> Create Visualization
        </button>
      </div>

      {loading ? (
        <div className="text-center text-muted-foreground py-12">Loading...</div>
      ) : items.length === 0 ? (
        <div className="text-center text-muted-foreground py-12">
          <BarChart3 className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>No visualizations yet. Create one to get started.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map((viz) => (
            <div key={viz.id} onClick={() => router.push(`/visualizations/${viz.id}`)} className="rounded-lg border border-white/10 bg-card p-4 space-y-3 cursor-pointer hover:border-white/25 transition-colors">
              <div className="flex items-center justify-between">
                <div className="font-medium">{viz.name}</div>
                <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${backendColors[viz.backend] || 'bg-gray-500/20 text-gray-400'}`}>
                  {viz.backend}
                </span>
              </div>

              <div className="space-y-1 text-sm text-muted-foreground">
                <div className="flex justify-between">
                  <span>Published</span>
                  <span className={viz.published ? 'text-green-400' : 'text-gray-400'}>
                    {viz.published ? 'Yes' : 'No'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Created</span>
                  <span>{new Date(viz.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Visualization Dialog */}
      {dialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/50" onClick={() => setDialogOpen(false)} />
          <div className="relative z-50 w-full max-w-md rounded-lg border border-white/10 bg-background p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Create Visualization</h2>
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
                  placeholder="My Visualization"
                  className="mt-1 w-full rounded-md border border-white/10 bg-muted/40 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              <div>
                <label className="text-sm font-medium text-muted-foreground">Backend</label>
                <select
                  value={formBackend}
                  onChange={(e) => setFormBackend(e.target.value)}
                  className="mt-1 w-full rounded-md border border-white/10 bg-muted/40 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="plotly">Plotly</option>
                  <option value="recharts">Recharts</option>
                  <option value="vega">Vega</option>
                  <option value="matplotlib">Matplotlib</option>
                  <option value="d3">D3</option>
                </select>
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
                onClick={handleCreate}
                disabled={creating || !formName.trim()}
                className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
              >
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
