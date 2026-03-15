'use client'

import { useEffect, useRef, useCallback, useState } from 'react'

interface SSEMetric {
  metric_name: string
  metric_value: number
  epoch?: number
  step?: number
  created_at: string
}

interface SSEStatus {
  status: string
  progress?: number
  epoch_current?: number
  epoch_total?: number
  loss?: number
}

interface UseJobSSEOptions {
  jobId: string
  enabled?: boolean
  onMetric?: (metric: SSEMetric) => void
  onStatus?: (status: SSEStatus) => void
  onDone?: (status: string) => void
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function useJobSSE({ jobId, enabled = true, onMetric, onStatus, onDone }: UseJobSSEOptions) {
  const [connected, setConnected] = useState(false)
  const [metrics, setMetrics] = useState<SSEMetric[]>([])
  const [latestStatus, setLatestStatus] = useState<SSEStatus | null>(null)
  const sourceRef = useRef<EventSource | null>(null)

  const connect = useCallback(() => {
    if (!enabled || !jobId) return

    const token = typeof window !== 'undefined' ? localStorage.getItem('openuba_token') : null
    const url = `${API_URL}/api/v1/jobs/${jobId}/metrics/stream${token ? `?token=${token}` : ''}`

    const source = new EventSource(url)
    sourceRef.current = source

    source.addEventListener('metric', (e) => {
      const metric: SSEMetric = JSON.parse(e.data)
      setMetrics(prev => [...prev, metric].slice(-1000))
      onMetric?.(metric)
    })

    source.addEventListener('status', (e) => {
      const status: SSEStatus = JSON.parse(e.data)
      setLatestStatus(status)
      onStatus?.(status)
    })

    source.addEventListener('done', (e) => {
      const data = JSON.parse(e.data)
      onDone?.(data.status)
      source.close()
      setConnected(false)
    })

    source.onopen = () => setConnected(true)
    source.onerror = () => {
      setConnected(false)
      source.close()
    }
  }, [jobId, enabled, onMetric, onStatus, onDone])

  useEffect(() => {
    connect()
    return () => {
      sourceRef.current?.close()
    }
  }, [connect])

  return { connected, metrics, latestStatus }
}
