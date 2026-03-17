'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
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
  succeeded: 'bg-green-500/20 text-green-400',
  completed: 'bg-green-500/20 text-green-400',
  failed: 'bg-red-500/20 text-red-400',
  stopped: 'bg-gray-500/20 text-gray-400',
}

const typeColors: Record<string, string> = {
  training: 'bg-purple-500/20 text-purple-400',
  inference: 'bg-cyan-500/20 text-cyan-400',
  evaluation: 'bg-orange-500/20 text-orange-400',
}

const levelColors: Record<string, string> = {
  error: 'text-red-400',
  warning: 'text-yellow-400',
  info: 'text-blue-400',
}

interface Job {
  id: string
  name?: string
  job_type: string
  model?: string
  model_id?: string
  model_run_id?: string
  status: string
  progress?: number
  hardware_tier?: string
  metrics?: Record<string, number>
  error_message?: string
  created_at: string
  started_at?: string
  completed_at?: string
  updated_at?: string
}

interface LogEntry {
  id: string
  job_id: string
  level: string
  message: string
  logger_name?: string
  created_at: string
}

interface SSEMetric {
  metric_name: string
  metric_value: number
  epoch?: number
  step?: number
  created_at: string
}

function formatDuration(startedAt?: string, completedAt?: string): string {
  if (!startedAt) return '-'
  const start = new Date(startedAt).getTime()
  const end = completedAt ? new Date(completedAt).getTime() : Date.now()
  const ms = end - start
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`
}

export default function JobDetailPage({ params }: { params: { id: string } }) {
  const { authFetch } = useAuth()
  const router = useRouter()
  const [job, setJob] = useState<Job | null>(null)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [logsLoading, setLogsLoading] = useState(true)
  const [sseConnected, setSSEConnected] = useState(false)
  const [sseMetrics, setSSEMetrics] = useState<SSEMetric[]>([])
  const sseRef = useRef<EventSource | null>(null)

  const loadJob = useCallback(async () => {
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
  }, [authFetch, params.id])

  const loadLogs = useCallback(async () => {
    setLogsLoading(true)
    try {
      const res = await authFetch(`${API_URL}/api/v1/jobs/${params.id}/logs`)
      if (res.ok) {
        const data = await res.json()
        if (Array.isArray(data)) {
          setLogs(data)
        } else {
          setLogs([])
        }
      }
    } catch (err) {
      console.error('failed to load job logs:', err)
    } finally {
      setLogsLoading(false)
    }
  }, [authFetch, params.id])

  // initial load
  useEffect(() => {
    loadJob()
    loadLogs()
  }, [loadJob, loadLogs])

  // auto-poll job status and logs while running
  useEffect(() => {
    if (!job) return
    const isActive = ['pending', 'running'].includes(job.status)
    if (!isActive) return

    const jobInterval = setInterval(loadJob, 5000)
    const logsInterval = setInterval(loadLogs, 3000)
    return () => {
      clearInterval(jobInterval)
      clearInterval(logsInterval)
    }
  }, [job?.status, loadJob, loadLogs])

  // SSE streaming for live metrics
  useEffect(() => {
    if (!job || !['pending', 'running'].includes(job.status)) return

    const token = typeof window !== 'undefined' ? localStorage.getItem('openuba_token') : null
    const url = `${API_URL}/api/v1/jobs/${params.id}/metrics/stream${token ? `?token=${encodeURIComponent(token)}` : ''}`
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
      loadLogs()
    })

    source.onopen = () => setSSEConnected(true)
    source.onerror = () => {
      setSSEConnected(false)
      source.close()
    }

    return () => { source.close() }
  }, [job?.status, params.id, loadJob, loadLogs])

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

  const progress = job.progress ?? (job.status === 'succeeded' || job.status === 'completed' ? 100 : 0)

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
          <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${typeColors[job.job_type] || 'bg-gray-500/20 text-gray-400'}`}>
            {job.job_type}
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
              job.status === 'succeeded' || job.status === 'completed' ? 'bg-green-500' :
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
            <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${typeColors[job.job_type] || 'bg-gray-500/20 text-gray-400'}`}>
              {job.job_type}
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
          <DetailField label="Duration">
            <span className="font-mono text-sm tabular-nums">{formatDuration(job.started_at, job.completed_at)}</span>
          </DetailField>
          <DetailField label="Created">
            <span className="text-sm">{new Date(job.created_at).toLocaleString()}</span>
          </DetailField>
          {job.started_at && (
            <DetailField label="Started">
              <span className="text-sm">{new Date(job.started_at).toLocaleString()}</span>
            </DetailField>
          )}
          {job.completed_at && (
            <DetailField label="Completed">
              <span className="text-sm">{new Date(job.completed_at).toLocaleString()}</span>
            </DetailField>
          )}
        </div>

        {job.error_message && (
          <div className="mt-4">
            <span className="text-[10px] font-medium uppercase tracking-wide text-red-400">Error</span>
            <pre className="text-xs mt-1 p-3 rounded bg-red-500/10 border border-red-500/20 overflow-x-auto whitespace-pre-wrap text-red-300">
              {job.error_message}
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

      {/* Structured Logs */}
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
        {logsLoading && logs.length === 0 ? (
          <div className="text-center text-muted-foreground py-6 text-sm">Loading logs...</div>
        ) : logs.length > 0 ? (
          <div className="max-h-96 overflow-y-auto rounded bg-black/40 border border-white/5 p-4 space-y-1">
            {logs.map((log) => (
              <div key={log.id} className="flex gap-2 py-0.5">
                <span className="text-[10px] text-muted-foreground font-mono shrink-0 pt-0.5 w-[60px]">
                  {new Date(log.created_at).toLocaleTimeString()}
                </span>
                <span className={`text-[10px] font-mono uppercase shrink-0 pt-0.5 w-[50px] ${levelColors[log.level] || 'text-blue-400'}`}>
                  {log.level}
                </span>
                <span className="text-xs font-mono whitespace-pre-wrap break-all text-muted-foreground">
                  {log.message}
                </span>
              </div>
            ))}
            {['pending', 'running'].includes(job.status) && (
              <div className="flex items-center gap-2 py-2">
                <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                <span className="text-xs text-muted-foreground">listening for new logs...</span>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center text-muted-foreground py-6 text-sm">
            {['pending', 'running'].includes(job.status) ? 'Waiting for logs...' : 'No logs available'}
          </div>
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
