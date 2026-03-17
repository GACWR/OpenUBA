'use client'

import { useState, useEffect, useRef } from 'react'
import { useAuth } from '@/lib/auth-provider'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft, BarChart3, Trash2, Loader2, Eye, Save, Code2,
  EyeOff, Download, Database, Settings2,
} from 'lucide-react'
import VizRenderer, { downloadVisualization } from '@/components/shared/viz-renderer'

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
  const previewContainerRef = useRef<HTMLDivElement>(null)
  const [viz, setViz] = useState<Visualization | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  // panel visibility
  const [showCode, setShowCode] = useState(true)
  const [showPreview, setShowPreview] = useState(true)

  // code editor state
  const [activeTab, setActiveTab] = useState<'code' | 'data' | 'config'>('code')
  const [codeValue, setCodeValue] = useState('')
  const [dataValue, setDataValue] = useState('')
  const [configValue, setConfigValue] = useState('')
  const [hasChanges, setHasChanges] = useState(false)

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
        setDataValue(data.data ? JSON.stringify(data.data, null, 2) : '{}')
        setConfigValue(data.config ? JSON.stringify(data.config, null, 2) : '{}')
        setHasChanges(false)
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

  const handleSave = async () => {
    setActionLoading('save')
    try {
      const body: any = { code: codeValue }
      try { body.data = JSON.parse(dataValue) } catch {}
      try { body.config = JSON.parse(configValue) } catch {}
      await authFetch(`${API_URL}/api/v1/visualizations/${params.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      setHasChanges(false)
      await loadViz()
    } catch (err) {
      console.error('failed to save:', err)
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

  const handleToggleCode = () => {
    if (showCode && !showPreview) setShowPreview(true)
    setShowCode(!showCode)
  }

  const handleTogglePreview = () => {
    if (showPreview && !showCode) setShowCode(true)
    setShowPreview(!showPreview)
  }

  const handleDownload = () => {
    if (!viz) return
    downloadVisualization(
      viz.name || 'visualization',
      viz.output_type,
      viz.rendered_output,
      previewContainerRef.current,
    )
  }

  const handleCodeChange = (val: string) => { setCodeValue(val); setHasChanges(true) }
  const handleDataChange = (val: string) => { setDataValue(val); setHasChanges(true) }
  const handleConfigChange = (val: string) => { setConfigValue(val); setHasChanges(true) }

  // determine preview source label
  const previewSource = ['plotly', 'altair', 'bokeh'].includes(viz?.backend || '')
    ? 'Live' : 'Rendered from notebook'

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
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      {/* Header */}
      <div className="flex-none px-1 py-3 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={() => router.push('/visualizations')} className="inline-flex items-center justify-center rounded-md p-1.5 hover:bg-muted/40 transition-colors">
              <ArrowLeft className="h-5 w-5" />
            </button>
            <BarChart3 className="h-5 w-5 text-green-400" />
            <h1 className="text-lg font-bold tracking-tight">{viz.name}</h1>
            <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${backendColors[viz.backend] || 'bg-gray-500/20 text-gray-400'}`}>
              {viz.backend}
            </span>
            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${viz.published ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}`}>
              {viz.published ? 'Published' : 'Draft'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            {/* Toggle buttons */}
            <button
              onClick={handleToggleCode}
              className={`inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium transition-colors ${
                showCode ? 'border-blue-500/50 bg-blue-500/10 text-blue-400' : 'border-white/10 text-muted-foreground hover:bg-muted/40'
              }`}
            >
              <Code2 className="h-3.5 w-3.5" />
              {showCode ? 'Hide Code' : 'Show Code'}
            </button>
            <button
              onClick={handleTogglePreview}
              className={`inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-sm font-medium transition-colors ${
                showPreview ? 'border-green-500/50 bg-green-500/10 text-green-400' : 'border-white/10 text-muted-foreground hover:bg-muted/40'
              }`}
            >
              {showPreview ? <EyeOff className="h-3.5 w-3.5" /> : <Eye className="h-3.5 w-3.5" />}
              {showPreview ? 'Hide Preview' : 'Show Preview'}
            </button>
            <button
              onClick={handleDownload}
              disabled={!viz.rendered_output}
              className="inline-flex items-center gap-1.5 rounded-md border border-white/10 px-3 py-1.5 text-sm font-medium hover:bg-muted/40 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <Download className="h-3.5 w-3.5" />
              Download
            </button>

            <div className="w-px h-6 bg-white/10 mx-1" />

            {/* Actions */}
            {hasChanges && (
              <button onClick={handleSave} disabled={!!actionLoading} className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 animate-in fade-in duration-200">
                {actionLoading === 'save' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}
                Save
              </button>
            )}
            {!viz.published && (
              <button onClick={handlePublish} disabled={!!actionLoading} className="inline-flex items-center gap-1.5 rounded-md border border-white/10 px-3 py-1.5 text-sm font-medium hover:bg-green-500/10 hover:border-green-500/50 transition-colors disabled:opacity-50">
                {actionLoading === 'publish' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Eye className="h-3.5 w-3.5" />}
                Publish
              </button>
            )}
            <button onClick={handleDelete} disabled={!!actionLoading} className="inline-flex items-center gap-1.5 rounded-md border border-white/10 px-3 py-1.5 text-sm font-medium hover:bg-red-500/10 hover:border-red-500/50 transition-colors disabled:opacity-50">
              {actionLoading === 'delete' ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Trash2 className="h-3.5 w-3.5" />}
              Delete
            </button>
          </div>
        </div>
        {viz.description && <p className="text-sm text-muted-foreground pl-12">{viz.description}</p>}
      </div>

      {/* Main Content: Side-by-side code + preview */}
      <div
        className="flex-1 min-h-0 grid gap-3 px-1 pb-3"
        style={{ gridTemplateColumns: showCode && showPreview ? '1fr 1fr' : '1fr' }}
      >
        {/* Code Panel */}
        {showCode && (
          <div className="rounded-lg border border-white/10 bg-card flex flex-col min-h-0 overflow-hidden">
            {/* Tab bar */}
            <div className="flex-none flex items-center border-b border-white/10">
              <button
                onClick={() => setActiveTab('code')}
                className={`inline-flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'code'
                    ? 'border-blue-400 text-blue-400'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                <Code2 className="h-3.5 w-3.5" />
                Code (Python)
              </button>
              <button
                onClick={() => setActiveTab('data')}
                className={`inline-flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'data'
                    ? 'border-blue-400 text-blue-400'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                <Database className="h-3.5 w-3.5" />
                Data
              </button>
              <button
                onClick={() => setActiveTab('config')}
                className={`inline-flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === 'config'
                    ? 'border-blue-400 text-blue-400'
                    : 'border-transparent text-muted-foreground hover:text-foreground'
                }`}
              >
                <Settings2 className="h-3.5 w-3.5" />
                Config
              </button>
            </div>

            {/* Editor content */}
            <div className="flex-1 min-h-0 overflow-auto">
              {activeTab === 'code' && (
                <div className="h-full flex flex-col">
                  <div className="flex-none px-4 py-2 text-xs text-muted-foreground border-b border-white/5">
                    Write a render(ctx) function that returns a {viz.backend} figure object.
                  </div>
                  <textarea
                    value={codeValue}
                    onChange={(e) => handleCodeChange(e.target.value)}
                    spellCheck={false}
                    className="flex-1 w-full bg-black/40 px-4 py-3 text-sm font-mono text-green-300 focus:outline-none resize-none"
                    style={{ tabSize: 4 }}
                    placeholder={`import matplotlib.pyplot as plt\nimport numpy as np\n\ndef render(ctx):\n    """Render a ${viz.backend} visualization."""\n    fig, ax = plt.subplots(figsize=(ctx.width / 100, ctx.height / 100))\n    \n    # Your visualization code here\n    x = np.linspace(0, 10, 100)\n    ax.plot(x, np.sin(x), color="#8b5cf6", linewidth=2)\n    ax.set_title("Sine Wave", color="white")\n    ax.tick_params(colors="white")\n    \n    return fig`}
                  />
                </div>
              )}
              {activeTab === 'data' && (
                <textarea
                  value={dataValue}
                  onChange={(e) => handleDataChange(e.target.value)}
                  spellCheck={false}
                  className="w-full h-full bg-black/40 px-4 py-3 text-sm font-mono text-yellow-300 focus:outline-none resize-none"
                  style={{ tabSize: 2 }}
                  placeholder="{}"
                />
              )}
              {activeTab === 'config' && (
                <div className="h-full flex flex-col">
                  <div className="flex-none px-4 py-3 space-y-3 border-b border-white/5">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Backend</label>
                        <div className="mt-0.5 font-mono text-sm">{viz.backend}</div>
                      </div>
                      <div>
                        <label className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Output Type</label>
                        <div className="mt-0.5 font-mono text-sm">{viz.output_type}</div>
                      </div>
                    </div>
                  </div>
                  <textarea
                    value={configValue}
                    onChange={(e) => handleConfigChange(e.target.value)}
                    spellCheck={false}
                    className="flex-1 w-full bg-black/40 px-4 py-3 text-sm font-mono text-purple-300 focus:outline-none resize-none"
                    style={{ tabSize: 2 }}
                    placeholder="{}"
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {/* Preview Panel */}
        {showPreview && (
          <div className="rounded-lg border border-white/10 bg-card flex flex-col min-h-0 overflow-hidden">
            {/* Preview header */}
            <div className="flex-none flex items-center justify-between px-4 py-2.5 border-b border-white/10">
              <div className="flex items-center gap-2">
                <Eye className="h-3.5 w-3.5 text-muted-foreground" />
                <span className="text-sm font-medium text-muted-foreground">Preview</span>
              </div>
              <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${
                previewSource === 'Live' ? 'text-green-400' : 'text-muted-foreground'
              }`}>
                {previewSource === 'Live' && <span className="h-1.5 w-1.5 rounded-full bg-green-400 animate-pulse" />}
                {previewSource}
              </span>
            </div>

            {/* Preview content — interactive backends (plotly/vega/bokeh) need
                overflow:hidden so height:100% resolves correctly */}
            <div
              className={`flex-1 min-h-0 p-4 ${
                ['plotly', 'vega-lite', 'bokeh'].includes(viz.output_type)
                  ? 'overflow-hidden'
                  : 'overflow-auto'
              }`}
              ref={previewContainerRef}
            >
              {viz.rendered_output ? (
                <VizRenderer
                  backend={viz.backend}
                  outputType={viz.output_type}
                  config={viz.config}
                  data={viz.data}
                  renderedOutput={viz.rendered_output}
                  code={viz.code}
                  autoResize
                />
              ) : (
                <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                  <BarChart3 className="h-12 w-12 opacity-20 mb-3" />
                  <p className="text-sm">No rendered output yet.</p>
                  <p className="text-xs mt-1">Run the visualization from a workspace notebook to generate output.</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
