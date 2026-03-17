'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-provider'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft, GitBranch, Play, Trash2, Loader2, CheckCircle2, XCircle, Clock,
} from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const statusIcons: Record<string, any> = {
  pending: Clock,
  running: Loader2,
  completed: CheckCircle2,
  failed: XCircle,
}

const statusColors: Record<string, string> = {
  pending: 'text-yellow-400',
  running: 'text-blue-400',
  completed: 'text-green-400',
  failed: 'text-red-400',
}

interface Pipeline {
  id: string
  name: string
  description?: string
  steps: any[]
  created_at: string
  updated_at: string
}

interface PipelineRun {
  id: string
  status: string
  current_step: number
  step_statuses?: any[]
  started_at?: string
  completed_at?: string
  created_at: string
}

export default function PipelineDetailPage({ params }: { params: { id: string } }) {
  const { authFetch } = useAuth()
  const router = useRouter()
  const [pipeline, setPipeline] = useState<Pipeline | null>(null)
  const [runs, setRuns] = useState<PipelineRun[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  useEffect(() => {
    loadPipeline()
  }, [params.id])

  const loadPipeline = async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/pipelines/${params.id}`)
      if (res.ok) setPipeline(await res.json())

      const runsRes = await authFetch(`${API_URL}/api/v1/pipelines/${params.id}/runs`)
      if (runsRes.ok) {
        const data = await runsRes.json()
        setRuns(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      console.error('failed to load pipeline:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRun = async () => {
    setActionLoading('run')
    try {
      await authFetch(`${API_URL}/api/v1/pipelines/${params.id}/run`, { method: 'POST' })
      await loadPipeline()
    } catch (err) {
      console.error('failed to run pipeline:', err)
    } finally {
      setActionLoading(null)
    }
  }

  const handleDelete = async () => {
    setActionLoading('delete')
    try {
      const res = await authFetch(`${API_URL}/api/v1/pipelines/${params.id}`, { method: 'DELETE' })
      if (res.ok) router.push('/pipelines')
    } catch (err) {
      console.error('failed to delete:', err)
    } finally {
      setActionLoading(null)
    }
  }

  if (loading) return <div className="text-center text-muted-foreground py-12">Loading...</div>

  if (!pipeline) {
    return (
      <div className="space-y-4">
        <button onClick={() => router.push('/pipelines')} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back to Pipelines
        </button>
        <div className="text-center text-muted-foreground py-12">Pipeline not found</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <button onClick={() => router.push('/pipelines')} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-2">
            <ArrowLeft className="h-4 w-4" /> Back to Pipelines
          </button>
          <div className="flex items-center gap-3">
            <GitBranch className="h-6 w-6 text-teal-400" />
            <h1 className="text-2xl font-bold tracking-tight">{pipeline.name}</h1>
            <span className="text-xs text-muted-foreground font-mono">
              {pipeline.steps?.length ?? 0} steps
            </span>
          </div>
          {pipeline.description && <p className="text-muted-foreground">{pipeline.description}</p>}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleRun} disabled={!!actionLoading} className="inline-flex items-center gap-1.5 rounded-md bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700 transition-colors disabled:opacity-50">
            {actionLoading === 'run' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            Run Pipeline
          </button>
          <button onClick={handleDelete} disabled={!!actionLoading} className="inline-flex items-center gap-1.5 rounded-md border border-white/10 px-3 py-2 text-sm font-medium hover:bg-red-500/10 hover:border-red-500/50 transition-colors disabled:opacity-50">
            {actionLoading === 'delete' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
            Delete
          </button>
        </div>
      </div>

      {/* Pipeline Steps */}
      <div className="rounded-lg border border-white/10 bg-card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Pipeline Steps</h2>
        <div className="space-y-3">
          {pipeline.steps.map((step: any, idx: number) => (
            <div key={idx} className="flex items-center gap-3 p-3 rounded-lg bg-muted/20 border border-white/5">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted/40 flex items-center justify-center text-sm font-bold">
                {idx + 1}
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium capitalize">{step.type || 'unknown'}</div>
                <div className="text-xs text-muted-foreground">
                  {step.model_id && <span>Model: {step.model_id.slice(0, 8)} </span>}
                  {step.hardware_tier && <span>({step.hardware_tier})</span>}
                </div>
              </div>
              {idx < pipeline.steps.length - 1 && (
                <div className="text-muted-foreground">→</div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Pipeline Runs */}
      <div className="rounded-lg border border-white/10 bg-card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Pipeline Runs</h2>
        {runs.length === 0 ? (
          <div className="text-center text-muted-foreground py-6 text-sm">No runs yet.</div>
        ) : (
          <div className="space-y-2">
            {runs.map((run) => {
              const Icon = statusIcons[run.status] || Clock
              return (
                <div key={run.id} className="flex items-center justify-between p-3 rounded-lg bg-muted/20 border border-white/5">
                  <div className="flex items-center gap-3">
                    <Icon className={`h-4 w-4 ${statusColors[run.status] || 'text-gray-400'} ${run.status === 'running' ? 'animate-spin' : ''}`} />
                    <span className="font-mono text-sm">{run.id.slice(0, 8)}</span>
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      run.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                      run.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                      run.status === 'running' ? 'bg-blue-500/20 text-blue-400' :
                      'bg-yellow-500/20 text-yellow-400'
                    }`}>
                      {run.status}
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Step {run.current_step + 1}/{pipeline.steps.length}
                    <span className="ml-2">{new Date(run.created_at).toLocaleString()}</span>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Raw Steps JSON */}
      <div className="rounded-lg border border-white/10 bg-card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Steps Configuration</h2>
        <pre className="bg-muted/30 rounded-md p-4 text-xs font-mono overflow-auto max-h-64 text-muted-foreground">
          {JSON.stringify(pipeline.steps, null, 2)}
        </pre>
      </div>
    </div>
  )
}
