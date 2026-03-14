'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-provider'
import Link from 'next/link'
import { Cpu, RefreshCw } from 'lucide-react'

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
  created_at: string
  updated_at?: string
}

export default function JobsPage() {
  const { authFetch } = useAuth()
  const [jobs, setJobs] = useState<Job[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadJobs()
  }, [])

  const loadJobs = async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/jobs`)
      if (res.ok) {
        const data = await res.json()
        setJobs(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      console.error('failed to load jobs:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
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

      {loading ? (
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
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Hardware</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Created</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {jobs.map((job) => (
                <tr key={job.id} className="hover:bg-muted/20 transition-colors">
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${typeColors[job.type] || 'bg-gray-500/20 text-gray-400'}`}>
                      {job.type}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">
                    {job.model || job.model_id?.slice(0, 8) || '-'}
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
                            job.status === 'completed' ? 'bg-green-500' :
                            job.status === 'failed' ? 'bg-red-500' :
                            'bg-blue-500'
                          }`}
                          style={{ width: `${job.progress ?? (job.status === 'completed' ? 100 : 0)}%` }}
                        />
                      </div>
                      <span className="text-xs text-muted-foreground tabular-nums">
                        {job.progress ?? (job.status === 'completed' ? 100 : 0)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                    {job.hardware_tier || '-'}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {new Date(job.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/jobs/${job.id}`}
                      className="text-xs text-blue-400 hover:underline"
                    >
                      details
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
