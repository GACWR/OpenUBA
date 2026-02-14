'use client'

import * as React from 'react'
import { useQuery } from '@apollo/client'
import { GET_EXECUTION_LOGS } from '@/lib/graphql/queries'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Terminal } from 'lucide-react'

interface LogEntry {
  timestamp: string
  component: string
  level: 'info' | 'warn' | 'error'
  message: string
}

interface SystemLogPanelProps {
  logs?: LogEntry[]
}

export function SystemLogPanel({ logs: propLogs }: SystemLogPanelProps) {
  const { data, loading } = useQuery(GET_EXECUTION_LOGS, { pollInterval: 10000 })

  const executionLogs: LogEntry[] = React.useMemo(() => {
    const nodes = data?.allExecutionLogs?.nodes || []
    return nodes.slice(0, 20).map((log: any) => ({
      timestamp: log.startedAt
        ? new Date(log.startedAt).toLocaleTimeString()
        : log.completedAt
          ? new Date(log.completedAt).toLocaleTimeString()
          : '-',
      component: log.modelByModelId?.name || 'system',
      level: log.status === 'failed' ? 'error' as const
        : (log.status === 'running' || log.status === 'dispatched') ? 'warn' as const
        : 'info' as const,
      message: log.status === 'failed'
        ? `execution failed${log.errorMessage ? ': ' + log.errorMessage : ''}`
        : log.status === 'succeeded'
          ? `completed${log.executionTimeSeconds ? ' in ' + log.executionTimeSeconds + 's' : ''}${log.outputSummary ? ' — ' + (typeof log.outputSummary === 'string' ? log.outputSummary : JSON.stringify(log.outputSummary)) : ''}`
          : log.status,
    }))
  }, [data])

  const logs = propLogs && propLogs.length > 0 ? propLogs : executionLogs

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-semibold">System Events</CardTitle>
        <Terminal className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full overflow-auto">
          <div className="space-y-1">
            {loading && logs.length === 0 ? (
              Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="flex items-center gap-2 py-1.5">
                  <Skeleton className="h-3 w-16 shrink-0" />
                  <Skeleton className="h-4 w-12 rounded-full shrink-0" />
                  <Skeleton className="h-3 w-20 shrink-0" />
                  <Skeleton className="h-3 flex-1" />
                </div>
              ))
            ) : logs.length === 0 ? (
              <div className="text-sm text-muted-foreground">No system events</div>
            ) : (
              logs.map((log, index) => (
                <div
                  key={index}
                  className="flex items-start gap-2 text-xs py-1.5 border-b border-border/30 last:border-0"
                >
                  <span className="text-muted-foreground w-16 shrink-0 font-mono text-[10px] pt-0.5">{log.timestamp}</span>
                  <Badge
                    variant={log.level === 'error' ? 'error' : log.level === 'warn' ? 'warning' : 'info'}
                    className="h-4 px-1.5 text-[9px] uppercase w-12 justify-center shrink-0"
                  >
                    {log.level}
                  </Badge>
                  <span className="text-muted-foreground font-medium shrink-0">{log.component}</span>
                  <span className="text-foreground truncate">{log.message}</span>
                </div>
              ))
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
