'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-provider'
import { GitBranch } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-500/20 text-yellow-400',
  running: 'bg-blue-500/20 text-blue-400',
  completed: 'bg-green-500/20 text-green-400',
  failed: 'bg-red-500/20 text-red-400',
  idle: 'bg-gray-500/20 text-gray-400',
}

interface Pipeline {
  id: string
  name: string
  description?: string
  steps?: any[]
  step_count?: number
  status?: string
  last_run_at?: string
  created_at: string
  updated_at?: string
}

export default function PipelinesPage() {
  const { authFetch } = useAuth()
  const [items, setItems] = useState<Pipeline[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadItems()
  }, [])

  const loadItems = async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/pipelines`)
      if (res.ok) {
        const data = await res.json()
        setItems(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      console.error('failed to load pipelines:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Pipelines</h1>
          <p className="text-muted-foreground">Multi-step workflow automation</p>
        </div>
      </div>

      {loading ? (
        <div className="text-center text-muted-foreground py-12">Loading...</div>
      ) : items.length === 0 ? (
        <div className="text-center text-muted-foreground py-12">
          <GitBranch className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>No pipelines yet</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {items.map((pipeline) => (
            <div key={pipeline.id} className="rounded-lg border border-white/10 bg-card p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="font-medium">{pipeline.name}</div>
                {pipeline.status && (
                  <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${statusColors[pipeline.status] || 'bg-gray-500/20 text-gray-400'}`}>
                    {pipeline.status}
                  </span>
                )}
              </div>
              {pipeline.description && (
                <p className="text-sm text-muted-foreground line-clamp-2">{pipeline.description}</p>
              )}

              <div className="space-y-1 text-sm text-muted-foreground">
                <div className="flex justify-between">
                  <span>Steps</span>
                  <span className="font-mono text-foreground">
                    {pipeline.step_count ?? pipeline.steps?.length ?? 0}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Created</span>
                  <span>{new Date(pipeline.created_at).toLocaleDateString()}</span>
                </div>
                {pipeline.last_run_at && (
                  <div className="flex justify-between">
                    <span>Last Run</span>
                    <span>{new Date(pipeline.last_run_at).toLocaleDateString()}</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
