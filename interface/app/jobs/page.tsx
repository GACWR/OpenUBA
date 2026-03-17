'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useAuth } from '@/lib/auth-provider'
import Link from 'next/link'
import { Cpu, RefreshCw, FileText, X } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-500/20 text-yellow-400',
  running: 'bg-blue-500/20 text-blue-400',
  succeeded: 'bg-green-500/20 text-green-400',
  failed: 'bg-red-500/20 text-red-400',
  cancelled: 'bg-gray-500/20 text-gray-400',
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

function formatDuration(startedAt?: string, completedAt?: string): string {
  if (!startedAt) return '-'
  const start = new Date(startedAt).getTime()
  const end = completedAt ? new Date(completedAt).getTime() : Date.now()
  const ms = end - start
  if (ms < 1000) return `${ms}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${Math.floor(ms / 60000)}m ${Math.floor((ms % 60000) / 1000)}s`
}

export default function JobsPage() {
  const { authFetch } = useAuth()
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [logsLoading, setLogsLoading] = useState(false)
  const [closing, setClosing] = useState(false)
  const prevStatusMap = useRef<Map<string, string>>(new Map())
  const isFirstLoad = useRef(true)
  const [toasts, setToasts] = useState<Array<{ id: number; message: string; type: string }>>([])
  const toastIdRef = useRef(0)

  const addToast = useCallback((message: string, type: string = 'info') => {
    const id = ++toastIdRef.current
    setToasts(prev => [...prev, { id, message, type }])
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), type === 'error' ? 15000 : 5000)
  }, [])

  const loadJobs = useCallback(async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/jobs`)
      if (res.ok) {
        const data = await res.json()
        const jobList: Job[] = Array.isArray(data) ? data : []
        setJobs(jobList)

        // detect status transitions and fire toasts
        if (isFirstLoad.current) {
          jobList.forEach(j => prevStatusMap.current.set(j.id, j.status))
          isFirstLoad.current = false
        } else {
          jobList.forEach(j => {
            const prev = prevStatusMap.current.get(j.id)
            if (prev && prev !== j.status) {
              const name = j.name || j.model || j.model_id?.slice(0, 8) || 'job'
              if (j.status === 'running') {
                addToast(`${name} ${j.job_type} running`, 'info')
              } else if (j.status === 'succeeded') {
                addToast(`${name} ${j.job_type} succeeded`, 'success')
              } else if (j.status === 'failed') {
                addToast(`${name} ${j.job_type} failed`, 'error')
              }
            }
            prevStatusMap.current.set(j.id, j.status)
          })
        }
      }
    } catch (err) {
      console.error('failed to load jobs:', err)
    } finally {
      setLoading(false)
    }
  }, [authFetch, addToast])

  // initial load + auto-polling every 5 seconds
  useEffect(() => {
    loadJobs()
    const interval = setInterval(loadJobs, 5000)
    return () => clearInterval(interval)
  }, [loadJobs])

  // load logs when a job is selected
  useEffect(() => {
    if (!selectedJobId) return
    setLogsLoading(true)
    const fetchLogs = async () => {
      try {
        const res = await authFetch(`${API_URL}/api/v1/jobs/${selectedJobId}/logs`)
        if (res.ok) {
          const data = await res.json()
          setLogs(Array.isArray(data) ? data : [])
        }
      } catch (err) {
        console.error('failed to load logs:', err)
      } finally {
        setLogsLoading(false)
      }
    }
    fetchLogs()
    // poll logs if job is running
    const job = jobs.find(j => j.id === selectedJobId)
    const isRunning = job?.status === 'running' || job?.status === 'pending'
    let logInterval: NodeJS.Timeout | undefined
    if (isRunning) {
      logInterval = setInterval(fetchLogs, 3000)
    }
    return () => { if (logInterval) clearInterval(logInterval) }
  }, [selectedJobId, authFetch, jobs])

  const selectedJob = jobs.find(j => j.id === selectedJobId)
  const isSelectedRunning = selectedJob?.status === 'running' || selectedJob?.status === 'pending'

  const handleClosePanel = () => {
    setClosing(true)
  }

  return (
    <div className="space-y-6">
      {/* Toast notifications */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map(t => (
          <div key={t.id} className={`px-4 py-2 rounded-lg text-sm font-medium shadow-lg animate-in slide-in-from-right ${
            t.type === 'success' ? 'bg-green-500/90 text-white' :
            t.type === 'error' ? 'bg-red-500/90 text-white' :
            'bg-blue-500/90 text-white'
          }`}>
            {t.message}
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Jobs</h1>
          <p className="text-muted-foreground">Training and inference job monitoring</p>
        </div>
        <button
          onClick={() => { setLoading(true); loadJobs() }}
          className="inline-flex items-center gap-2 rounded-md border border-white/10 px-3 py-2 text-sm font-medium hover:bg-muted/40 transition-colors"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {loading && jobs.length === 0 ? (
        <div className="text-center text-muted-foreground py-12">Loading...</div>
      ) : jobs.length === 0 ? (
        <div className="text-center text-muted-foreground py-12">
          <Cpu className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>No jobs found</p>
        </div>
      ) : (
        <div className="rounded-lg border border-white/10 bg-card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10 bg-muted/30">
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Type</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Model</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Progress</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Duration</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Hardware</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Created</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {jobs.map((job) => (
                <tr key={job.id} className="hover:bg-muted/20 transition-colors">
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${typeColors[job.job_type] || 'bg-gray-500/20 text-gray-400'}`}>
                      {job.job_type}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-col">
                      <span className="font-mono text-xs">{job.model || job.model_id?.slice(0, 8) || '-'}</span>
                      <span className="text-[10px] text-muted-foreground">{job.id.slice(0, 8)}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[job.status] || 'bg-gray-500/20 text-gray-400'}`}>
                      {job.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-20 rounded-full bg-muted/40 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            job.status === 'succeeded' ? 'bg-green-500' :
                            job.status === 'failed' ? 'bg-red-500' :
                            'bg-blue-500'
                          }`}
                          style={{ width: `${job.progress ?? (job.status === 'succeeded' ? 100 : 0)}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground tabular-nums">
                        {job.progress ?? (job.status === 'succeeded' ? 100 : 0)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-xs tabular-nums text-muted-foreground">
                    {formatDuration(job.started_at, job.completed_at)}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                    {job.hardware_tier || '-'}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {new Date(job.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => { setClosing(false); setSelectedJobId(job.id) }}
                        className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
                      >
                        <FileText className="h-3.5 w-3.5" /> logs
                      </button>
                      <Link
                        href={`/jobs/${job.id}`}
                        className="text-xs text-blue-400 hover:underline"
                      >
                        details
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Slide-in Logs Panel */}
      {selectedJobId && (
        <>
          <div
            className="fixed inset-0 bg-black/30 z-40"
            style={{ animation: closing ? 'jobsFadeOut 150ms ease-in forwards' : 'jobsFadeIn 150ms ease-out' }}
            onClick={handleClosePanel}
          />
          <div
            className="fixed top-0 right-0 h-full w-[480px] bg-background border-l shadow-2xl z-50 flex flex-col"
            style={{ animation: closing ? 'jobsSlideOut 200ms ease-in forwards' : 'jobsSlideIn 200ms ease-out' }}
            onAnimationEnd={() => { if (closing) { setSelectedJobId(null); setClosing(false) } }}
          >
            <div className="p-4 border-b space-y-2">
              <div className="flex justify-between items-center">
                <h2 className="text-lg font-semibold">job logs</h2>
                <button onClick={handleClosePanel} className="p-1 rounded hover:bg-muted/40">
                  <X className="h-4 w-4" />
                </button>
              </div>
              {selectedJob && (
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm text-muted-foreground">{selectedJob.model || selectedJob.model_id?.slice(0, 8) || '-'}</span>
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${typeColors[selectedJob.job_type] || 'bg-gray-500/20 text-gray-400'}`}>
                    {selectedJob.job_type}
                  </span>
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[selectedJob.status] || 'bg-gray-500/20 text-gray-400'}`}>
                    {selectedJob.status}
                  </span>
                </div>
              )}
              <p className="text-xs text-muted-foreground font-mono">{selectedJobId.slice(0, 8)}</p>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-1">
              {logsLoading && logs.length === 0 && (
                <p className="text-sm text-muted-foreground">loading logs...</p>
              )}
              {!logsLoading && logs.length === 0 && (
                <p className="text-sm text-muted-foreground">
                  {isSelectedRunning ? 'waiting for logs...' : 'no logs recorded for this job'}
                </p>
              )}
              {logs.map((log) => (
                <div key={log.id} className="flex gap-2 py-1 border-b border-border/50 last:border-0">
                  <span className="text-[10px] text-muted-foreground font-mono shrink-0 pt-0.5 w-[60px]">
                    {new Date(log.created_at).toLocaleTimeString()}
                  </span>
                  <span className={`text-[10px] font-mono uppercase shrink-0 pt-0.5 w-[50px] ${levelColors[log.level] || 'text-blue-400'}`}>
                    {log.level}
                  </span>
                  <span className="text-xs font-mono whitespace-pre-wrap break-all">
                    {log.message}
                  </span>
                </div>
              ))}
              {isSelectedRunning && logs.length > 0 && (
                <div className="flex items-center gap-2 py-2">
                  <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                  <span className="text-xs text-muted-foreground">listening for new logs...</span>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* Inject keyframes */}
      <style jsx global>{`
        @keyframes jobsSlideIn {
          from { transform: translateX(100%); }
          to { transform: translateX(0); }
        }
        @keyframes jobsSlideOut {
          from { transform: translateX(0); }
          to { transform: translateX(100%); }
        }
        @keyframes jobsFadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes jobsFadeOut {
          from { opacity: 1; }
          to { opacity: 0; }
        }
      `}</style>
    </div>
  )
}
