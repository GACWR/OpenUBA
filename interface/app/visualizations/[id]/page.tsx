'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-provider'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft, BarChart3, Trash2, Loader2, Eye, Save, Code2,
} from 'lucide-react'
import VizRenderer from '@/components/shared/viz-renderer'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

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
  matplotlib: 'bg-orange-500/20 text-orange-400',
  seaborn: 'bg-blue-500/20 text-blue-400',
  plotly: 'bg-cyan-500/20 text-cyan-400',
  bokeh: 'bg-green-500/20 text-green-400',
  altair: 'bg-purple-500/20 text-purple-400',
  plotnine: 'bg-pink-500/20 text-pink-400',
  datashader: 'bg-teal-500/20 text-teal-400',
  networkx: 'bg-yellow-500/20 text-yellow-400',
  geopandas: 'bg-indigo-500/20 text-indigo-400',
}

export default function VisualizationDetailPage({ params }: { params: { id: string } }) {
  const { authFetch } = useAuth()
  const router = useRouter()
  const [viz, setViz] = useState<Visualization | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [editingCode, setEditingCode] = useState(false)
  const [codeValue, setCodeValue] = useState('')

  useEffect(() => {
    loadViz()
  }, [params.id])

  const loadViz = async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/visualizations/${params.id}`)
      if (res.ok) {
        const data = await res.json()
        setViz(data)
        setCodeValue(data.code || '')
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

  const handleSaveCode = async () => {
    setActionLoading('save')
    try {
      await authFetch(`${API_URL}/api/v1/visualizations/${params.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: codeValue }),
      })
      setEditingCode(false)
      await loadViz()
    } catch (err) {
      console.error('failed to save code:', err)
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

      {/* Chart Preview */}
      <div className="rounded-lg border border-white/10 bg-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Chart Preview</h2>
          <span className="text-xs text-muted-foreground">Rendered with {viz.backend}</span>
        </div>
        <VizRenderer
          backend={viz.backend}
          outputType={viz.output_type}
          config={viz.config}
          data={viz.data}
          renderedOutput={viz.rendered_output}
          code={viz.code}
        />
      </div>

      {/* Code Editor */}
      <div className="rounded-lg border border-white/10 bg-card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Code2 className="h-4 w-4 text-blue-400" />
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Visualization Code</h2>
          </div>
          <div className="flex items-center gap-2">
            {editingCode ? (
              <>
                <button onClick={handleSaveCode} disabled={!!actionLoading} className="inline-flex items-center gap-1 rounded-md bg-primary px-3 py-1.5 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50">
                  {actionLoading === 'save' ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3" />}
                  Save
                </button>
                <button onClick={() => { setEditingCode(false); setCodeValue(viz.code || '') }} className="rounded-md border border-white/10 px-3 py-1.5 text-xs font-medium hover:bg-muted/40">
                  Cancel
                </button>
              </>
            ) : (
              <button onClick={() => setEditingCode(true)} className="inline-flex items-center gap-1 rounded-md border border-white/10 px-3 py-1.5 text-xs font-medium hover:bg-blue-500/10 hover:border-blue-500/50 transition-colors">
                <Code2 className="h-3 w-3" /> Edit Code
              </button>
            )}
          </div>
        </div>

        {editingCode ? (
          <textarea
            value={codeValue}
            onChange={(e) => setCodeValue(e.target.value)}
            rows={20}
            spellCheck={false}
            className="w-full rounded-md border border-white/10 bg-black/40 px-4 py-3 text-sm font-mono text-green-300 focus:outline-none focus:ring-2 focus:ring-ring resize-y"
            placeholder={`# Write your ${viz.backend} visualization code here\nimport matplotlib.pyplot as plt\n\n# Your code...`}
          />
        ) : viz.code ? (
          <pre className="bg-black/40 rounded-md p-4 text-sm font-mono overflow-auto max-h-96 text-green-300 whitespace-pre-wrap">
            {viz.code}
          </pre>
        ) : (
          <div className="text-center text-muted-foreground py-8">
            <Code2 className="h-8 w-8 mx-auto mb-2 opacity-30" />
            <p className="text-sm">No code yet. Click "Edit Code" to add visualization code.</p>
          </div>
        )}
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
