'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Database, RefreshCw, ChevronRight } from 'lucide-react'

export interface DataSource {
  name: string
  type: 'spark' | 'elasticsearch'
  rowCount?: number
  size?: string
  lastUpdated?: string
}

interface DataSourcesTableProps {
  sources: DataSource[]
  loading?: boolean
  onRefresh?: () => void
  onSourceClick?: (source: DataSource) => void
}

export function DataSourcesTable({ sources, loading, onRefresh, onSourceClick }: DataSourcesTableProps) {
  return (
    <Card className="hover:shadow-card-hover transition-all h-full flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div>
          <CardTitle className="text-lg font-semibold">Data Sources</CardTitle>
          <p className="text-xs text-muted-foreground mt-1">{sources.length} sources configured</p>
        </div>
        <div className="flex items-center gap-2">
          {onRefresh && (
            <Button variant="ghost" size="icon" onClick={onRefresh} disabled={loading} className="h-8 w-8">
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          )}
          <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
            <Database className="h-5 w-5 text-muted-foreground" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="flex-1 overflow-auto">
        <div className="rounded-lg border bg-card/50 backdrop-blur-sm">
          <table className="w-full">
            <thead>
              <tr>
                <th className="h-10 px-3 text-left align-middle text-xs font-medium text-muted-foreground">Name</th>
                <th className="h-10 px-3 text-left align-middle text-xs font-medium text-muted-foreground">Type</th>
                <th className="h-10 px-3 text-right align-middle text-xs font-medium text-muted-foreground">Rows</th>
                <th className="h-10 px-3 text-right align-middle text-xs font-medium text-muted-foreground">Size</th>
              </tr>
            </thead>
            <tbody>
              {loading && sources.length === 0 ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="border-t">
                    <td className="px-3 py-2.5"><Skeleton className="h-4 w-32" /></td>
                    <td className="px-3 py-2.5"><Skeleton className="h-5 w-16 rounded-full" /></td>
                    <td className="px-3 py-2.5 text-right"><Skeleton className="h-4 w-12 ml-auto" /></td>
                    <td className="px-3 py-2.5 text-right"><Skeleton className="h-4 w-14 ml-auto" /></td>
                  </tr>
                ))
              ) : sources.length > 0 ? (
                sources.map((source) => (
                  <tr
                    key={`${source.type}-${source.name}`}
                    className={`border-t transition-colors hover:bg-muted/50 ${onSourceClick ? 'cursor-pointer' : ''}`}
                    onClick={() => onSourceClick?.(source)}
                  >
                    <td className="px-3 py-2.5 align-middle">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-sm">{source.name}</span>
                        {onSourceClick && (
                          <ChevronRight className="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                        )}
                      </div>
                    </td>
                    <td className="px-3 py-2.5 align-middle">
                      <Badge
                        variant={source.type === 'spark' ? 'warning' : 'info'}
                        size="sm"
                      >
                        {source.type}
                      </Badge>
                    </td>
                    <td className="px-3 py-2.5 align-middle text-right">
                      <span className="font-medium text-sm tabular-nums">
                        {source.rowCount?.toLocaleString() || '-'}
                      </span>
                    </td>
                    <td className="px-3 py-2.5 align-middle text-right">
                      <span className="text-xs text-muted-foreground">
                        {source.size || '-'}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="h-20 text-center text-muted-foreground text-sm">
                    No data sources found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  )
}
