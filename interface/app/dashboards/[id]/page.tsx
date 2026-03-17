'use client'

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '@/lib/auth-provider'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft, LayoutDashboard, Trash2, Loader2, Eye, Plus, Save, GripVertical,
} from 'lucide-react'
import VizRenderer from '@/components/shared/viz-renderer'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Dashboard {
  id: string
  name: string
  description?: string
  layout?: any[]
  published: boolean
  created_at: string
  updated_at: string
}

interface LayoutItem {
  i: string
  x: number
  y: number
  w: number
  h: number
}

interface Panel {
  id: string
  title: string
  chart_type: string
  x_key: string
  y_key: string
  color: string
  data?: any[]
  viz_id?: string
}

const DEFAULT_PANEL: Omit<Panel, 'id'> = {
  title: 'New Panel',
  chart_type: 'bar',
  x_key: 'name',
  y_key: 'value',
  color: '#8884d8',
  data: [
    { name: 'Q1', value: 400 },
    { name: 'Q2', value: 300 },
    { name: 'Q3', value: 600 },
    { name: 'Q4', value: 500 },
  ],
}

export default function DashboardDetailPage({ params }: { params: { id: string } }) {
  const { authFetch } = useAuth()
  const router = useRouter()
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [panels, setPanels] = useState<Panel[]>([])
  const [layoutItems, setLayoutItems] = useState<LayoutItem[]>([])
  const [draggedPanel, setDraggedPanel] = useState<string | null>(null)

  useEffect(() => {
    loadDashboard()
  }, [params.id])

  const loadDashboard = async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/dashboards/${params.id}`)
      if (res.ok) {
        const data = await res.json()
        setDashboard(data)
        parsePanels(data.layout || [])
      }
    } catch (err) {
      console.error('failed to load dashboard:', err)
    } finally {
      setLoading(false)
    }
  }

  const parsePanels = (layout: any[]) => {
    const parsed: Panel[] = []
    const items: LayoutItem[] = []
    let idx = 0

    for (const section of layout) {
      const sectionPanels = section.panels || section.widgets || (section.title ? [section] : [])
      for (const p of sectionPanels) {
        const id = p.id || `panel-${idx}`
        parsed.push({
          id,
          title: p.title || p.name || `Panel ${idx + 1}`,
          chart_type: p.chart_type || p.type || 'bar',
          x_key: p.x_key || 'name',
          y_key: p.y_key || 'value',
          color: p.color || '#8884d8',
          data: p.data,
          viz_id: p.viz_id,
        })
        items.push({
          i: id,
          x: (idx % 2) * 6,
          y: Math.floor(idx / 2) * 4,
          w: 6,
          h: 4,
          ...(p.layout || {}),
        })
        idx++
      }
    }
    setPanels(parsed)
    setLayoutItems(items)
  }

  const handlePublish = async () => {
    setActionLoading('publish')
    try {
      await authFetch(`${API_URL}/api/v1/dashboards/${params.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ published: true }),
      })
      await loadDashboard()
    } catch (err) {
      console.error('failed to publish:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const handleDelete = async () => {
    setActionLoading('delete')
    try {
      const res = await authFetch(`${API_URL}/api/v1/dashboards/${params.id}`, { method: 'DELETE' })
      if (res.ok) router.push('/dashboards')
    } catch (err) {
      console.error('failed to delete:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const handleAddPanel = () => {
    const id = `panel-${Date.now()}`
    setPanels(prev => [...prev, { ...DEFAULT_PANEL, id }])
    setLayoutItems(prev => [
      ...prev,
      { i: id, x: 0, y: Infinity, w: 6, h: 4 },
    ])
  }

  const handleRemovePanel = (panelId: string) => {
    setPanels(prev => prev.filter(p => p.id !== panelId))
    setLayoutItems(prev => prev.filter(l => l.i !== panelId))
  }

  const handleSaveLayout = async () => {
    setActionLoading('save')
    try {
      const layout = panels.map((p, idx) => ({
        ...p,
        layout: layoutItems.find(l => l.i === p.id) || { x: 0, y: idx * 4, w: 6, h: 4 },
      }))
      await authFetch(`${API_URL}/api/v1/dashboards/${params.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ layout }),
      })
      setEditing(false)
      await loadDashboard()
    } catch (err) {
      console.error('failed to save layout:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const movePanel = (panelId: string, direction: 'up' | 'down') => {
    const idx = panels.findIndex(p => p.id === panelId)
    if (idx === -1) return
    const newIdx = direction === 'up' ? idx - 1 : idx + 1
    if (newIdx < 0 || newIdx >= panels.length) return
    const newPanels = [...panels]
    ;[newPanels[idx], newPanels[newIdx]] = [newPanels[newIdx], newPanels[idx]]
    setPanels(newPanels)
  }

  if (loading) return <div className="text-center text-muted-foreground py-12">Loading...</div>

  if (!dashboard) {
    return (
      <div className="space-y-4">
        <button onClick={() => router.push('/dashboards')} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back to Dashboards
        </button>
        <div className="text-center text-muted-foreground py-12">Dashboard not found</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <button onClick={() => router.push('/dashboards')} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-2">
            <ArrowLeft className="h-4 w-4" /> Back to Dashboards
          </button>
          <div className="flex items-center gap-3">
            <LayoutDashboard className="h-6 w-6 text-blue-400" />
            <h1 className="text-2xl font-bold tracking-tight">{dashboard.name}</h1>
            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${dashboard.published ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
              {dashboard.published ? 'Published' : 'Draft'}
            </span>
          </div>
          {dashboard.description && <p className="text-muted-foreground">{dashboard.description}</p>}
        </div>
        <div className="flex items-center gap-2">
          {editing ? (
            <>
              <button onClick={handleAddPanel} className="inline-flex items-center gap-1.5 rounded-md border border-white/10 px-3 py-2 text-sm font-medium hover:bg-blue-500/10 hover:border-blue-500/50 transition-colors">
                <Plus className="h-4 w-4" /> Add Panel
              </button>
              <button onClick={handleSaveLayout} disabled={!!actionLoading} className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
                {actionLoading === 'save' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                Save Layout
              </button>
              <button onClick={() => { setEditing(false); parsePanels(dashboard.layout || []) }} className="rounded-md border border-white/10 px-3 py-2 text-sm font-medium hover:bg-muted/40">
                Cancel
              </button>
            </>
          ) : (
            <>
              <button onClick={() => setEditing(true)} className="inline-flex items-center gap-1.5 rounded-md border border-white/10 px-3 py-2 text-sm font-medium hover:bg-blue-500/10 hover:border-blue-500/50 transition-colors">
                <LayoutDashboard className="h-4 w-4" /> Edit Layout
              </button>
              {!dashboard.published && (
                <button onClick={handlePublish} disabled={!!actionLoading} className="inline-flex items-center gap-1.5 rounded-md border border-white/10 px-3 py-2 text-sm font-medium hover:bg-green-500/10 hover:border-green-500/50 transition-colors disabled:opacity-50">
                  {actionLoading === 'publish' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Eye className="h-4 w-4" />}
                  Publish
                </button>
              )}
              <button onClick={handleDelete} disabled={!!actionLoading} className="inline-flex items-center gap-1.5 rounded-md border border-white/10 px-3 py-2 text-sm font-medium hover:bg-red-500/10 hover:border-red-500/50 transition-colors disabled:opacity-50">
                {actionLoading === 'delete' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
                Delete
              </button>
            </>
          )}
        </div>
      </div>

      {/* Dashboard Info */}
      <div className="rounded-lg border border-white/10 bg-card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Dashboard Info</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Status</span>
            <div className="mt-0.5 text-sm">{dashboard.published ? 'Published' : 'Draft'}</div>
          </div>
          <div>
            <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Panels</span>
            <div className="mt-0.5 font-mono text-sm">{panels.length}</div>
          </div>
          <div>
            <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Created</span>
            <div className="mt-0.5 text-sm">{new Date(dashboard.created_at).toLocaleString()}</div>
          </div>
          <div>
            <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Updated</span>
            <div className="mt-0.5 text-sm">{new Date(dashboard.updated_at).toLocaleString()}</div>
          </div>
        </div>
      </div>

      {/* Dashboard Panels Grid */}
      {panels.length > 0 ? (
        <div className="grid gap-4 md:grid-cols-2">
          {panels.map((panel, idx) => (
            <div key={panel.id} className="rounded-lg border border-white/10 bg-card p-4 relative group">
              {editing && (
                <div className="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-10">
                  <button onClick={() => movePanel(panel.id, 'up')} className="p-1 rounded hover:bg-muted/40" title="Move up">
                    <GripVertical className="h-3 w-3" />
                  </button>
                  <button onClick={() => handleRemovePanel(panel.id)} className="p-1 rounded hover:bg-red-500/20 text-red-400" title="Remove">
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              )}
              <h3 className="text-sm font-medium mb-3">{panel.title}</h3>
              <VizRenderer
                backend="recharts"
                outputType="interactive"
                config={{
                  chart_type: panel.chart_type,
                  x_key: panel.x_key,
                  y_key: panel.y_key,
                  color: panel.color,
                  stat_value: panel.chart_type === 'stat' ? panel.data?.[0]?.value : undefined,
                  stat_label: panel.chart_type === 'stat' ? panel.y_key : undefined,
                }}
                data={panel.data}
                height={250}
              />
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-white/10 bg-card p-12 text-center text-muted-foreground">
          <LayoutDashboard className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>No panels configured yet.</p>
          {!editing && (
            <button onClick={() => setEditing(true)} className="mt-3 inline-flex items-center gap-1.5 rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90">
              <Plus className="h-4 w-4" /> Add Panels
            </button>
          )}
        </div>
      )}
    </div>
  )
}
