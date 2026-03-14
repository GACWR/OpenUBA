'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-provider'
import { FileSpreadsheet, RefreshCw } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const formatColors: Record<string, string> = {
  csv: 'bg-green-500/20 text-green-400',
  parquet: 'bg-blue-500/20 text-blue-400',
  json: 'bg-yellow-500/20 text-yellow-400',
  avro: 'bg-purple-500/20 text-purple-400',
  delta: 'bg-orange-500/20 text-orange-400',
}

interface Dataset {
  id: string
  name: string
  format?: string
  source_type?: string
  row_count?: number
  size_bytes?: number
  description?: string
  created_at: string
  updated_at?: string
}

export default function DatasetsPage() {
  const { authFetch } = useAuth()
  const [items, setItems] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadItems()
  }, [])

  const loadItems = async () => {
    try {
      const res = await authFetch(`${API_URL}/api/v1/datasets`)
      if (res.ok) {
        const data = await res.json()
        setItems(Array.isArray(data) ? data : [])
      }
    } catch (err) {
      console.error('failed to load datasets:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatSize = (bytes?: number) => {
    if (!bytes) return '-'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Datasets</h1>
          <p className="text-muted-foreground">Manage datasets for training and inference</p>
        </div>
        <button
          onClick={() => { setLoading(true); loadItems() }}
          className="inline-flex items-center gap-2 rounded-md border border-white/10 px-3 py-2 text-sm font-medium hover:bg-muted/40 transition-colors"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} /> Refresh
        </button>
      </div>

      {loading ? (
        <div className="text-center text-muted-foreground py-12">Loading...</div>
      ) : items.length === 0 ? (
        <div className="text-center text-muted-foreground py-12">
          <FileSpreadsheet className="h-12 w-12 mx-auto mb-3 opacity-30" />
          <p>No datasets found</p>
        </div>
      ) : (
        <div className="rounded-lg border border-white/10 bg-card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/10 bg-muted/30">
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Name</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Format</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Source Type</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Rows</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Size</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {items.map((ds) => (
                <tr key={ds.id} className="hover:bg-muted/20 transition-colors">
                  <td className="px-4 py-3">
                    <div className="font-medium">{ds.name}</div>
                    {ds.description && (
                      <div className="text-xs text-muted-foreground truncate max-w-[250px]">{ds.description}</div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {ds.format ? (
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${formatColors[ds.format] || 'bg-gray-500/20 text-gray-400'}`}>
                        {ds.format}
                      </span>
                    ) : (
                      <span className="text-muted-foreground">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {ds.source_type || '-'}
                  </td>
                  <td className="px-4 py-3 text-right font-mono tabular-nums">
                    {ds.row_count != null ? ds.row_count.toLocaleString() : '-'}
                  </td>
                  <td className="px-4 py-3 text-right font-mono tabular-nums text-muted-foreground">
                    {formatSize(ds.size_bytes)}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {new Date(ds.created_at).toLocaleDateString()}
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
