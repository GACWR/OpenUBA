'use client'

import React from 'react'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, XCircle, AlertTriangle, Database, Zap } from 'lucide-react'

interface SparkResult {
  format: string
  status: string
  row_count: number
  table_name: string
}

interface ElasticsearchResult {
  failed: number
  status: string
  index_name: string
  document_count: number
}

interface RunDetails {
  dataset?: string
  spark?: Record<string, SparkResult>
  elasticsearch?: Record<string, ElasticsearchResult>
  errors?: string[]
}

interface IngestionRunDetailsProps {
  details: string | RunDetails
}

function parseDetails(details: string | RunDetails): RunDetails | null {
  try {
    if (typeof details === 'string') {
      return JSON.parse(details)
    }
    return details
  } catch {
    return null
  }
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'success') return <CheckCircle className="h-3 w-3 text-green-500" />
  if (status === 'failed' || status === 'error') return <XCircle className="h-3 w-3 text-red-500" />
  return <AlertTriangle className="h-3 w-3 text-yellow-500" />
}

export function IngestionRunDetails({ details }: IngestionRunDetailsProps) {
  const parsed = parseDetails(details)

  if (!parsed) {
    // Fallback: show raw string
    return (
      <div className="text-xs text-muted-foreground bg-muted/50 p-2 rounded font-mono overflow-x-auto">
        {typeof details === 'string' ? details : JSON.stringify(details, null, 2)}
      </div>
    )
  }

  const sparkEntries = parsed.spark ? Object.entries(parsed.spark) : []
  const esEntries = parsed.elasticsearch ? Object.entries(parsed.elasticsearch) : []
  const totalSparkRows = sparkEntries.reduce((sum, [, v]) => sum + (v.row_count || 0), 0)
  const totalEsDocs = esEntries.reduce((sum, [, v]) => sum + (v.document_count || 0), 0)
  const totalEsFailed = esEntries.reduce((sum, [, v]) => sum + (v.failed || 0), 0)

  return (
    <div className="space-y-2">
      {/* Spark results */}
      {sparkEntries.length > 0 && (
        <div className="rounded border bg-muted/30 overflow-hidden">
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-muted/50 border-b">
            <Zap className="h-3 w-3 text-yellow-500" />
            <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide">Spark</span>
            <span className="text-[11px] text-muted-foreground ml-auto">{totalSparkRows.toLocaleString()} rows</span>
          </div>
          <div className="divide-y divide-border/50">
            {sparkEntries.map(([source, result]) => (
              <div key={source} className="flex items-center gap-2 px-2.5 py-1.5 text-xs">
                <StatusIcon status={result.status} />
                <span className="font-medium min-w-[40px]">{source}</span>
                <span className="text-muted-foreground truncate">{result.table_name}</span>
                <span className="ml-auto font-mono tabular-nums">{result.row_count.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Elasticsearch results */}
      {esEntries.length > 0 && (
        <div className="rounded border bg-muted/30 overflow-hidden">
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 bg-muted/50 border-b">
            <Database className="h-3 w-3 text-blue-500" />
            <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wide">Elasticsearch</span>
            <span className="text-[11px] text-muted-foreground ml-auto">
              {totalEsDocs.toLocaleString()} docs
              {totalEsFailed > 0 && (
                <span className="text-red-400 ml-1.5">({totalEsFailed.toLocaleString()} failed)</span>
              )}
            </span>
          </div>
          <div className="divide-y divide-border/50">
            {esEntries.map(([source, result]) => (
              <div key={source} className="flex items-center gap-2 px-2.5 py-1.5 text-xs">
                <StatusIcon status={result.status} />
                <span className="font-medium min-w-[40px]">{source}</span>
                <span className="text-muted-foreground truncate">{result.index_name}</span>
                <div className="ml-auto flex items-center gap-2">
                  <span className="font-mono tabular-nums">{result.document_count.toLocaleString()}</span>
                  {result.failed > 0 && (
                    <Badge variant="error" size="sm" className="text-[10px] px-1.5 py-0">
                      {result.failed.toLocaleString()} failed
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Errors */}
      {parsed.errors && parsed.errors.length > 0 && (
        <div className="rounded border border-red-500/30 bg-red-500/10 p-2 space-y-1">
          <div className="flex items-center gap-1.5 text-[11px] font-medium text-red-400 uppercase tracking-wide">
            <XCircle className="h-3 w-3" />
            Errors
          </div>
          {parsed.errors.map((err, i) => (
            <div key={i} className="text-xs text-red-300">{err}</div>
          ))}
        </div>
      )}
    </div>
  )
}
