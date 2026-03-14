'use client'

import { useState, useEffect, useRef } from 'react'
import { useAuth } from '@/lib/auth-provider'
import { useRouter } from 'next/navigation'
import {
  ArrowLeft, Cpu, RefreshCw, Radio,
} from 'lucide-react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-500/20 text-yellow-400',
  running: 'bg-blue-500/20 text-blue-400',
  completed: 'bg-green-500/20 text-green-400',
  failed: 'bg-red-500/20 text-red-400',
  stopped: 'bg-gray-500/20 text-gray-400',
}

const typeColors: Record<string, string> = {
  training: 'bg-purple-500/20 text-purple-400',
  inference: 'bg-cyan-500/20 text-cyan-400',
  evaluation: 'bg-orange-500/20 text-orange-400',
}

interface Job {
  id: string
  type: string
  model?: string
  model_id?: string
  status: string
  progress?: number
  hardware_tier?: string
  metrics?: Record<string, number>
  error?: string
  created_at: string
  updated_at?: string
  completed_at?: string
}

interface SSEMetric {
  metric_name: string
  metric_value: number
  epoch?: number
  step?: number
  created_at: string
}

export default function JobDetailPage({ params }: { params: { id: string } }) {
  const { authFetch } = useAuth()
  const router = useRouter()
  const [job, setJob] = useState<Job | null>(null)
  const [logs, setLogs] = useState<string>('')
  const [loading, setLoading] = useState(true)
  const [logsLoading, setLogsLoading] = useState(true)
  const [sseConnected, setSSEConnected] = useState(false)
  const [sseMetrics, setSSEMetrics] = useState<SSEMetric[]>([])
  const sseRef = useRef<EventSource | null>(null)

  useEffect(() => {
    loadJob()
    loadLogs()
  }, [params.id])

  // SSE streaming for live metrics
  useEffect(() => {
    if (!job || !['pending', 'running'].includes(job.status)) return

    const url = `${API_URL}/api/v1/jobs/${params.id}/metrics/stream`
    const source = new EventSource(url)
    sseRef.current = source

    source.addEventListener('metric', (e: MessageEvent) => {
      const metric: SSEMetric = JSON.parse(e.data)
      setSSEMetrics(prev => [...prev, metric])
    })

    source.addEventListener('status', (e: MessageEvent) => {
      const status = JSON.parse(e.data)
      setJob(prev => prev ? { ...prev, ...status } : prev)
    })

    source.addEventListener('done', () => {
      source.close()
      setSSEConnected(false)
      loadJob()
    })

    source.onopen = () => setSSEConnected(true)
    source.onerror = () => {
      setSSEConnected(false)
      source.close()
    }

    return () => { source.close() }
  }, [job?.status, params.id])

  const loadJob = async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/jobs/${params.id}`)
      if (res.ok) {
        const data = await res.json()
        setJob(data)
      }
    } catch (err) {
      console.error('failed to load job:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadLogs = async () => {
    setLogsLoading(true)
    try {
      const res = await authFetch(`${API_URL}/api/v1/jobs/${params.id}/logs`)
      if (res.ok) {
        const data = await res.json()
        setLogs(typeof data === 'string' ? data : data.logs || data.content || JSON.stringify(data, null, 2))
      }
    } catch (err) {
      console.error('failed to load job logs:', err)
    } finally {
      setLogsLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center text-muted-foreground py-12">Loading...</div>
  }

  if (!job) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => router.push('/jobs')}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Jobs
        </button>
        <div className="text-center text-muted-foreground py-12">Job not found</div>
      </div>
    )
  }

  const progress = job.progress ?? (job.status === 'completed' ? 100 : 0)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="space-y-1">
        <button
          onClick={() => router.push('/jobs')}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-2"
        >
          <ArrowLeft className="h-4 w-4" /> Back to Jobs
        </button>
        <div className="flex items-center gap-3">
          <Cpu className="h-6 w-6 text-teal-400" />
          <h1 className="text-2xl font-bold tracking-tight">Job {job.id.slice(0, 8)}</h1>
          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${typeColors[job.type] || 'bg-gray-500/20 text-gray-400'}`}>
            {job.type}
          </span>
          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[job.status] || 'bg-gray-500/20 text-gray-400'}`}>
            {job.status}
          </span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="rounded-lg border border-white/10 bg-card p-4 space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">Progress</span>
          <span className="font-mono tabular-nums">{progress}%</span>
        </div>
        <div className="h-2 w-full rounded-full bg-muted/40 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              job.status === 'completed' ? 'bg-green-500' :
              job.status === 'failed' ? 'bg-red-500' :
              'bg-blue-500'
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Details Card */}
      <div className="rounded-lg border border-white/10 bg-card p-6 space-y-4">
        <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Job Details</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <DetailField label="Type">
            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${typeColors[job.type] || 'bg-gray-500/20 text-gray-400'}`}>
              {job.type}
            </span>
          </DetailField>
          <DetailField label="Status">
            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[job.status] || 'bg-gray-500/20 text-gray-400'}`}>
              {job.status}
            </span>
          </DetailField>
          <DetailField label="Model">
            <span className="font-mono text-sm">{job.model || job.model_id?.slice(0, 8) || '-'}</span>
          </DetailField>
          <DetailField label="Hardware Tier">
            <span className="font-mono text-sm">{job.hardware_tier || '-'}</span>
          </DetailField>
          <DetailField label="Created">
            <span className="text-sm">{new Date(job.created_at).toLocaleString()}</span>
          </DetailField>
          {job.completed_at && (
            <DetailField label="Completed">
              <span className="text-sm">{new Date(job.completed_at).toLocaleString()}</span>
            </DetailField>
          )}
        </div>

        {job.error && (
          <div className="mt-4">
            <span className="text-[10px] font-medium uppercase tracking-wide text-red-400">Error</span>
            <pre className="text-xs mt-1 p-3 rounded bg-red-500/10 border border-red-500/20 overflow-x-auto whitespace-pre-wrap text-red-300">
              {job.error}
            </pre>
          </div>
        )}
      </div>

      {/* SSE Live Metrics */}
      {sseMetrics.length > 0 && (
        <div className="rounded-lg border border-white/10 bg-card p-6 space-y-4">
          <div className="flex items-center gap-2">
            <Radio className={`h-4 w-4 ${sseConnected ? 'text-green-400 animate-pulse' : 'text-gray-400'}`} />
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Live Training Metrics</h2>
            {sseConnected && <span className="text-xs text-green-400">streaming</span>}
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={sseMetrics.map((m, i) => ({ idx: m.epoch ?? m.step ?? i, [m.metric_name]: m.metric_value }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="idx" stroke="#888" fontSize={12} />
              <YAxis stroke="#888" fontSize={12} />
              <Tooltip contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #333' }} />
              <Legend />
              {Array.from(new Set(sseMetrics.map(m => m.metric_name))).map((name, i) => (
                <Line key={name} type="monotone" dataKey={name} stroke={['#8884d8', '#82ca9d', '#ffc658', '#ff7300'][i % 4]} strokeWidth={2} dot={false} />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Metrics */}
      {job.metrics && Object.keys(job.metrics).length > 0 && (
        <div className="rounded-lg border border-white/10 bg-card p-6 space-y-4">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Metrics</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(job.metrics).map(([key, value]) => (
              <div key={key} className="rounded-lg bg-muted/30 p-3">
                <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">{key}</span>
                <div className="text-lg font-bold tabular-nums mt-0.5">
                  {typeof value === 'number' ? value.toFixed(4) : String(value)}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Logs */}
      <div className="rounded-lg border border-white/10 bg-card p-6 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Logs</h2>
          <button
            onClick={loadLogs}
            className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
          >
            <RefreshCw className={`h-3 w-3 ${logsLoading ? 'animate-spin' : ''}`} /> Refresh
          </button>
        </div>
        {logsLoading ? (
          <div className="text-center text-muted-foreground py-6 text-sm">Loading logs...</div>
        ) : logs ? (
          <pre className="text-xs p-4 rounded bg-black/40 border border-white/5 overflow-x-auto max-h-96 whitespace-pre-wrap font-mono text-muted-foreground">
            {logs}
          </pre>
        ) : (
          <div className="text-center text-muted-foreground py-6 text-sm">No logs available</div>
        )}
      </div>
    </div>
  )
}

function DetailField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">{label}</span>
      <div className="mt-0.5">{children}</div>
    </div>
  )
}
