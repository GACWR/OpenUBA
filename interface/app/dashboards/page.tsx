'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-provider'
import { useRouter } from 'next/navigation'
import {
  Plus, LayoutDashboard, X, Loader2,
} from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Dashboard {
  id: string
  name: string
  panels?: any[]
  published: boolean
  created_at: string
  updated_at?: string
}

export default function DashboardsPage() {
  const { authFetch } = useAuth()
  const router = useRouter()
  const [items, setItems] = useState<Dashboard[]>([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [creating, setCreating] = useState(false)

  /* form state */
  const [formName, setFormName] = useState('')

  useEffect(() => {
    loadItems()
  }, [])

  const loadItems = async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/dashboards`)
      if (res.ok) {
        const data = await res.json()
        setItems(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      console.error('failed to load dashboards:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!formName.trim()) return
    setCreating(true)
    try {
      const res = await authFetch(`${API_URL}/api/v1/dashboards`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formName.trim(),
        }),
      })
      if (res.ok) {
        setDialogOpen(false)
        setFormName('')
        await loadItems()
      }
    } catch (err) {
      console.error('failed to create dashboard:', err)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dashboards</h1>
          <p className="text-muted-foreground">Responsive grid dashboards composed of visualizations</p>
        </div>
        <button
          onClick={() => setDialogOpen(true)}
          className="inline-flex items-center gap-2 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          <Plus className="h-4 w-4" /> Create Dashboard
        </button>
      </div>

      {loading ? (
        <div className="text-center text-muted-foreground py-12">Loading...</div>
      ) : items.length === 0 ? (
        <div className="text-center text-muted-foreground py-12">
          <LayoutDashboard className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>No dashboards yet. Create one to get started.</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map((dash) => (
            <div key={dash.id} onClick={() => router.push(`/dashboards/${dash.id}`)} className="rounded-lg border border-white/10 bg-card p-4 space-y-3 cursor-pointer hover:border-white/25 transition-colors">
              <div className="flex items-center justify-between">
                <div className="font-medium">{dash.name}</div>
                <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${dash.published ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
                  {dash.published ? 'Published' : 'Draft'}
                </span>
              </div>

              <div className="space-y-1 text-sm text-muted-foreground">
                <div className="flex justify-between">
                  <span>Panels</span>
                  <span className="font-mono text-foreground">{dash.panels?.length || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Created</span>
                  <span>{new Date(dash.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Dashboard Dialog */}
      {dialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="fixed inset-0 bg-black/50" onClick={() => setDialogOpen(false)} />
          <div className="relative z-50 w-full max-w-md rounded-lg border border-white/10 bg-background p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Create Dashboard</h2>
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
                  placeholder="My Dashboard"
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
