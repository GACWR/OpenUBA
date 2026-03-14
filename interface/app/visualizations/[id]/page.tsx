'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-provider'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft, BarChart3, Trash2, ExternalLink, Loader2, Eye, EyeOff,
} from 'lucide-react'
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088FE', '#00C49F', '#FFBB28', '#FF8042']

interface Visualization {
  id: string
  name: string
  description?: string
  backend: string
  output_type: string
  code?: string
  data?: any
  config?: any
  rendered_output?: string
  refresh_interval: number
  published: boolean
  created_at: string
  updated_at: string
}

const backendColors: Record<string, string> = {
  plotly: 'bg-blue-500/20 text-blue-400',
  recharts: 'bg-green-500/20 text-green-400',
  vega: 'bg-purple-500/20 text-purple-400',
  matplotlib: 'bg-orange-500/20 text-orange-400',
  d3: 'bg-yellow-500/20 text-yellow-400',
}

function RenderChart({ viz }: { viz: Visualization }) {
  const config = viz.config || {}
  const chartType = config.chart_type || 'bar'
  const chartData = viz.data?.values || viz.data?.datasets || config.sample_data || [
    { name: 'Jan', value: 400 },
    { name: 'Feb', value: 300 },
    { name: 'Mar', value: 600 },
    { name: 'Apr', value: 800 },
    { name: 'May', value: 500 },
    { name: 'Jun', value: 700 },
  ]

  const xKey = config.x_key || 'name'
  const yKey = config.y_key || 'value'

  if (chartType === 'line') {
    return (
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey={xKey} stroke="#888" />
          <YAxis stroke="#888" />
          <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
          <Legend />
          <Line type="monotone" dataKey={yKey} stroke="#8884d8" strokeWidth={2} dot={{ fill: '#8884d8' }} />
        </LineChart>
      </ResponsiveContainer>
    )
  }

  if (chartType === 'area') {
    return (
      <ResponsiveContainer width="100%" height={400}>
        <AreaChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis dataKey={xKey} stroke="#888" />
          <YAxis stroke="#888" />
          <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
          <Legend />
          <Area type="monotone" dataKey={yKey} stroke="#8884d8" fill="#8884d8" fillOpacity={0.3} />
        </AreaChart>
      </ResponsiveContainer>
    )
  }

  if (chartType === 'pie') {
    return (
      <ResponsiveContainer width="100%" height={400}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={true}
            label={({ name, value }: any) => `${name}: ${value}`}
            outerRadius={150}
            fill="#8884d8"
            dataKey={yKey}
            nameKey={xKey}
          >
            {chartData.map((_: any, index: number) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    )
  }

  // default: bar chart
  return (
    <ResponsiveContainer width="100%" height={400}>
      <BarChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="#333" />
        <XAxis dataKey={xKey} stroke="#888" />
        <YAxis stroke="#888" />
        <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
        <Legend />
        <Bar dataKey={yKey} fill="#8884d8" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export default function VisualizationDetailPage({ params }: { params: { id: string } }) {
  const { authFetch } = useAuth()
  const router = useRouter()
  const [viz, setViz] = useState<Visualization | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  useEffect(() => {
    loadViz()
  }, [params.id])

  const loadViz = async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/visualizations/${params.id}`)
      if (res.ok) {
        setViz(await res.json())
      }
    } catch (err) {
      console.error('failed to load visualization:', err)
    } finally {
      setLoading(false)
    }
  }

  const handlePublish = async () => {
    setActionLoading('publish')
    try {
      await authFetch(`${API_URL}/api/v1/visualizations/${params.id}/publish`, { method: 'POST' })
      await loadViz()
    } catch (err) {
      console.error('failed to publish:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const handleDelete = async () => {
    setActionLoading('delete')
    try {
      const res = await authFetch(`${API_URL}/api/v1/visualizations/${params.id}`, { method: 'DELETE' })
      if (res.ok) router.push('/visualizations')
    } catch (err) {
      console.error('failed to delete:', err)
    } finally {
      setActionLoading(null)
    }
  }

  if (loading) return <div className="text-center text-muted-foreground py-12">Loading...</div>

  if (!viz) {
    return (
      <div className="space-y-4">
        <button onClick={() => router.push('/visualizations')} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back to Visualizations
        </button>
        <div className="text-center text-muted-foreground py-12">Visualization not found</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <button onClick={() => router.push('/visualizations')} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-2">
            <ArrowLeft className="h-4 w-4" /> Back to Visualizations
          </button>
          <div className="flex items-center gap-3">
            <BarChart3 className="h-6 w-6 text-green-400" />
            <h1 className="text-2xl font-bold tracking-tight">{viz.name}</h1>
            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${backendColors[viz.backend] || 'bg-gray-500/20 text-gray-400'}`}>
              {viz.backend}
            </span>
            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${viz.published ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
              {viz.published ? 'Published' : 'Draft'}
            </span>
          </div>
          {viz.description && <p className="text-muted-foreground">{viz.description}</p>}
        </div>
        <div className="flex items-center gap-2">
          {!viz.published && (
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

      {/* Details */}
      <div className="rounded-lg border border-white/10 bg-card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Details</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Backend</span>
            <div className="mt-0.5 font-mono text-sm">{viz.backend}</div>
          </div>
          <div>
            <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Output Type</span>
            <div className="mt-0.5 font-mono text-sm">{viz.output_type}</div>
          </div>
          <div>
            <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Chart Type</span>
            <div className="mt-0.5 font-mono text-sm">{viz.config?.chart_type || 'bar'}</div>
          </div>
          <div>
            <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Created</span>
            <div className="mt-0.5 text-sm">{new Date(viz.created_at).toLocaleString()}</div>
          </div>
        </div>
      </div>

      {/* Chart Render */}
      <div className="rounded-lg border border-white/10 bg-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Chart Preview</h2>
          <span className="text-xs text-muted-foreground">Rendered with {viz.backend}</span>
        </div>
        <RenderChart viz={viz} />
      </div>

      {/* Config/Data Section */}
      {(viz.config || viz.data) && (
        <div className="rounded-lg border border-white/10 bg-card p-6 space-y-4">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Configuration</h2>
          <pre className="bg-muted/30 rounded-md p-4 text-xs font-mono overflow-auto max-h-64 text-muted-foreground">
            {JSON.stringify({ config: viz.config, data: viz.data }, null, 2)}
          </pre>
        </div>
      )}
    </div>
  )
}
