'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-provider'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft, LayoutDashboard, Trash2, Loader2, Eye,
} from 'lucide-react'
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088FE', '#00C49F', '#FFBB28', '#FF8042']

interface Dashboard {
  id: string
  name: string
  description?: string
  layout?: any[]
  published: boolean
  created_at: string
  updated_at: string
}

function PanelChart({ panel }: { panel: any }) {
  const chartType = panel.chart_type || panel.type || 'bar'
  const data = panel.data || [
    { name: 'Q1', value: 400 },
    { name: 'Q2', value: 300 },
    { name: 'Q3', value: 600 },
    { name: 'Q4', value: 500 },
  ]
  const xKey = panel.x_key || 'name'
  const yKey = panel.y_key || 'value'
  const title = panel.title || panel.name || 'Panel'
  const color = panel.color || COLORS[0]

  return (
    <div className="rounded-lg border border-white/10 bg-card p-4">
      <h3 className="text-sm font-medium mb-3">{title}</h3>
      {chartType === 'line' ? (
        <ResponsiveContainer width="100%" height={250}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey={xKey} stroke="#888" fontSize={12} />
            <YAxis stroke="#888" fontSize={12} />
            <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
            <Line type="monotone" dataKey={yKey} stroke={color} strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      ) : chartType === 'area' ? (
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey={xKey} stroke="#888" fontSize={12} />
            <YAxis stroke="#888" fontSize={12} />
            <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
            <Area type="monotone" dataKey={yKey} stroke={color} fill={color} fillOpacity={0.3} />
          </AreaChart>
        </ResponsiveContainer>
      ) : chartType === 'pie' ? (
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie data={data} cx="50%" cy="50%" outerRadius={80} fill={color} dataKey={yKey} nameKey={xKey} label>
              {data.map((_: any, i: number) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie>
            <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
          </PieChart>
        </ResponsiveContainer>
      ) : chartType === 'stat' ? (
        <div className="flex items-center justify-center h-[250px]">
          <div className="text-center">
            <div className="text-4xl font-bold text-primary">{panel.stat_value ?? data[0]?.value ?? '—'}</div>
            <div className="text-sm text-muted-foreground mt-1">{panel.stat_label || yKey}</div>
          </div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#333" />
            <XAxis dataKey={xKey} stroke="#888" fontSize={12} />
            <YAxis stroke="#888" fontSize={12} />
            <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
            <Bar dataKey={yKey} fill={color} radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}

export default function DashboardDetailPage({ params }: { params: { id: string } }) {
  const { authFetch } = useAuth()
  const router = useRouter()
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  useEffect(() => {
    loadDashboard()
  }, [params.id])

  const loadDashboard = async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/dashboards/${params.id}`)
      if (res.ok) {
        setDashboard(await res.json())
      }
    } catch (err) {
      console.error('failed to load dashboard:', err)
    } finally {
      setLoading(false)
    }
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

  // extract panels from layout
  const panels: any[] = []
  if (dashboard.layout && Array.isArray(dashboard.layout)) {
    for (const section of dashboard.layout) {
      if (section.panels) {
        panels.push(...section.panels)
      } else if (section.widgets) {
        panels.push(...section.widgets)
      } else if (section.chart_type || section.type || section.title) {
        panels.push(section)
      }
    }
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
          {panels.map((panel: any, idx: number) => (
            <PanelChart key={idx} panel={panel} />
          ))}
        </div>
      ) : (
        <div className="rounded-lg border border-white/10 bg-card p-12 text-center text-muted-foreground">
          <LayoutDashboard className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>No panels configured yet. Add panels to the layout to see charts here.</p>
        </div>
      )}
    </div>
  )
}
