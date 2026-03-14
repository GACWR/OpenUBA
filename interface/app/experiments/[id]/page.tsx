'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-provider'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft, FlaskConical, Plus, Trash2, Loader2, BarChart3,
} from 'lucide-react'
import {
  BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088FE', '#00C49F']

interface ExperimentRun {
  id: string
  parameters?: Record<string, any>
  metrics?: Record<string, number>
  status: string
  model_id?: string
  job_id?: string
  created_at: string
}

interface Experiment {
  id: string
  name: string
  description?: string
  runs?: ExperimentRun[]
  created_at: string
}

export default function ExperimentDetailPage({ params }: { params: { id: string } }) {
  const { authFetch } = useAuth()
  const router = useRouter()
  const [experiment, setExperiment] = useState<Experiment | null>(null)
  const [comparison, setComparison] = useState<any[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  useEffect(() => {
    loadExperiment()
  }, [params.id])

  const loadExperiment = async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/experiments/${params.id}`)
      if (res.ok) {
        const data = await res.json()
        setExperiment(data)
      }
      // load comparison data
      try {
        const cRes = await authFetch(`${API_URL}/api/v1/experiments/${params.id}/compare`)
        if (cRes.ok) {
          setComparison(await cRes.json())
        }
      } catch {}
    } catch (err) {
      console.error('failed to load experiment:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    setActionLoading('delete')
    try {
      const res = await authFetch(`${API_URL}/api/v1/experiments/${params.id}`, { method: 'DELETE' })
      if (res.ok) router.push('/experiments')
    } catch (err) {
      console.error('failed to delete:', err)
    } finally {
      setActionLoading(null)
    }
  }

  if (loading) return <div className="text-center text-muted-foreground py-12">Loading...</div>

  if (!experiment) {
    return (
      <div className="space-y-4">
        <button onClick={() => router.push('/experiments')} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> Back to Experiments
        </button>
        <div className="text-center text-muted-foreground py-12">Experiment not found</div>
      </div>
    )
  }

  const runs = experiment.runs || []

  // build comparison chart data from runs with metrics
  const metricNames = new Set<string>()
  runs.forEach(r => {
    if (r.metrics) Object.keys(r.metrics).forEach(k => metricNames.add(k))
  })

  const comparisonData = runs.filter(r => r.metrics).map((r, idx) => ({
    name: `Run ${idx + 1}`,
    ...r.metrics,
  }))

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="space-y-1">
          <button onClick={() => router.push('/experiments')} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-2">
            <ArrowLeft className="h-4 w-4" /> Back to Experiments
          </button>
          <div className="flex items-center gap-3">
            <FlaskConical className="h-6 w-6 text-purple-400" />
            <h1 className="text-2xl font-bold tracking-tight">{experiment.name}</h1>
          </div>
          {experiment.description && <p className="text-muted-foreground">{experiment.description}</p>}
        </div>
        <button onClick={handleDelete} disabled={!!actionLoading} className="inline-flex items-center gap-1.5 rounded-md border border-white/10 px-3 py-2 text-sm font-medium hover:bg-red-500/10 hover:border-red-500/50 transition-colors disabled:opacity-50">
          {actionLoading === 'delete' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
          Delete
        </button>
      </div>

      {/* Info Card */}
      <div className="rounded-lg border border-white/10 bg-card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Experiment Info</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Total Runs</span>
            <div className="mt-0.5 font-mono text-lg font-bold">{runs.length}</div>
          </div>
          <div>
            <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">Created</span>
            <div className="mt-0.5 text-sm">{new Date(experiment.created_at).toLocaleString()}</div>
          </div>
        </div>
      </div>

      {/* Comparison Chart */}
      {comparisonData.length > 0 && metricNames.size > 0 && (
        <div className="rounded-lg border border-white/10 bg-card p-6 space-y-4">
          <div className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 text-blue-400" />
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Run Comparison</h2>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={comparisonData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="name" stroke="#888" fontSize={12} />
              <YAxis stroke="#888" fontSize={12} />
              <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
              <Legend />
              {Array.from(metricNames).map((metric, i) => (
                <Bar key={metric} dataKey={metric} fill={COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Runs Table */}
      <div className="rounded-lg border border-white/10 bg-card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Experiment Runs</h2>
        {runs.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            <FlaskConical className="h-8 w-8 mx-auto mb-2 opacity-30" />
            <p className="text-sm">No runs yet. Add runs via the SDK or API.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left py-2 pr-4 text-muted-foreground font-medium">Run</th>
                  <th className="text-left py-2 pr-4 text-muted-foreground font-medium">Status</th>
                  <th className="text-left py-2 pr-4 text-muted-foreground font-medium">Parameters</th>
                  <th className="text-left py-2 pr-4 text-muted-foreground font-medium">Metrics</th>
                  <th className="text-left py-2 text-muted-foreground font-medium">Created</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run, idx) => (
                  <tr key={run.id} className="border-b border-white/5">
                    <td className="py-2 pr-4 font-mono text-xs">{run.id.slice(0, 8)}</td>
                    <td className="py-2 pr-4">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                        run.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                        run.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                        'bg-yellow-500/20 text-yellow-400'
                      }`}>
                        {run.status}
                      </span>
                    </td>
                    <td className="py-2 pr-4 font-mono text-xs text-muted-foreground max-w-[200px] truncate">
                      {run.parameters ? JSON.stringify(run.parameters) : '-'}
                    </td>
                    <td className="py-2 pr-4">
                      {run.metrics ? (
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(run.metrics).map(([k, v]) => (
                            <span key={k} className="inline-flex items-center rounded bg-muted/30 px-1.5 py-0.5 text-xs font-mono">
                              {k}: {typeof v === 'number' ? v.toFixed(4) : String(v)}
                            </span>
                          ))}
                        </div>
                      ) : '-'}
                    </td>
                    <td className="py-2 text-xs text-muted-foreground">
                      {new Date(run.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
