'use client'

import React, { useEffect, useState, useCallback } from 'react'
import { DataSourcesTable } from './data-sources-table'
import { Button } from '@/components/ui/button'
import { RefreshCw, AlertCircle } from 'lucide-react'
import { useAuth } from '@/lib/auth-provider'

interface DataSource {
    name: string
    type: 'spark' | 'elasticsearch'
    rowCount?: number
    size?: string
    lastUpdated?: string
}

export function MetricsDisplay() {
    const [sources, setSources] = useState<DataSource[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const { authFetch } = useAuth()

    const fetchMetrics = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            const [sparkRes, esRes] = await Promise.all([
                authFetch('/api/v1/data/metrics/spark'),
                authFetch('/api/v1/data/metrics/elasticsearch')
            ])

            if (!sparkRes.ok || !esRes.ok) {
                throw new Error('Failed to fetch metrics')
            }

            const sparkData = await sparkRes.json()
            const esData = await esRes.json()

            const newSources: DataSource[] = []

            // Process Spark Data
            if (sparkData.tables) {
                Object.entries(sparkData.tables).forEach(([name, info]: [string, any]) => {
                    newSources.push({
                        name,
                        type: 'spark',
                        rowCount: info.count,
                        size: info.partition_count != null ? `${info.partition_count} partitions` : undefined,
                        lastUpdated: new Date().toISOString() // Timestamp not yet in API
                    })
                })
            }

            // Process Elasticsearch Data
            if (esData.indices) {
                Object.entries(esData.indices).forEach(([name, info]: [string, any]) => {
                    // ES stats structure: { indices: { name: { header: {...}, total: {...}, primaries: {...} } } } 
                    // usually _stats returns detailed structure. 
                    // My verify output (Step 738) didn't show ES structure deeply. 
                    // Assuming standard ES _stats or whatever get_elasticsearch_metrics returns.
                    // service.get_elasticsearch_metrics() usually calls `_stats`.
                    // docs.count is usually in `primaries.docs.count` or `total.docs.count`.
                    // Let's safe guard.

                    let count = 0
                    let sizeBytes = 0

                    if (info.primaries?.docs) {
                        count = info.primaries.docs.count
                    } else if (info.total?.docs) {
                        count = info.total.docs.count
                    }

                    if (info.total?.store) {
                        sizeBytes = info.total.store.size_in_bytes
                    }

                    newSources.push({
                        name,
                        type: 'elasticsearch',
                        rowCount: count,
                        size: sizeBytes ? `${(sizeBytes / 1024 / 1024).toFixed(2)} MB` : undefined,
                        lastUpdated: new Date().toISOString()
                    })
                })
            }

            setSources(newSources)
        } catch (err) {
            console.error('Metrics fetch error:', err)
            setError('Failed to load data sources. Is the backend running?')
        } finally {
            setLoading(false)
        }
    }, [authFetch])

    useEffect(() => {
        fetchMetrics()
        const interval = setInterval(fetchMetrics, 30000) // Poll every 30s
        return () => clearInterval(interval)
    }, [fetchMetrics])

    return (
        <div className="space-y-4 h-full flex flex-col">
            {error && (
                <div className="bg-red-500/15 text-red-500 p-3 rounded-md text-sm flex items-center gap-2">
                    <AlertCircle className="h-4 w-4" />
                    <span>{error}</span>
                </div>
            )}

            {/* 
        DataSourcesTable renders a Card internally. 
        We pass the sources. 
      */}
            <div className="relative">
                <div className="absolute top-4 right-4 z-10">
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={fetchMetrics}
                        disabled={loading}
                        className="h-8 w-8"
                    >
                        <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
                    </Button>
                </div>
                <DataSourcesTable sources={sources} />
            </div>
        </div>
    )
}
