'use client'

import { useState } from 'react'
import { useQuery } from '@apollo/client'
import { GET_MODEL_LOGS } from '@/lib/graphql/queries'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { X } from 'lucide-react'

interface ModelLog {
  id: string
  level: string
  message: string
  loggerName?: string
  createdAt: string
}

interface ModelLogsSheetProps {
  runId: string
  runType: string
  status: string
  modelName: string
  onClose: () => void
}

function getLevelColor(level: string) {
  switch (level) {
    case 'error': return 'text-red-400'
    case 'warning': return 'text-yellow-400'
    default: return 'text-blue-400'
  }
}

export function ModelLogsSheet({ runId, runType, status, modelName, onClose }: ModelLogsSheetProps) {
  const [closing, setClosing] = useState(false)
  const isRunning = status === 'running' || status === 'dispatched' || status === 'pending'

  const { data, loading } = useQuery(GET_MODEL_LOGS, {
    variables: { runId },
    pollInterval: isRunning ? 3000 : 0,
  })

  const logs: ModelLog[] = data?.allModelLogs?.nodes || []
  const errorCount = logs.filter(l => l.level === 'error').length
  const warningCount = logs.filter(l => l.level === 'warning').length

  const statusVariant = status === 'failed' ? 'destructive'
    : (status === 'succeeded' && errorCount > 0) ? 'destructive'
    : (status === 'succeeded' && warningCount > 0) ? 'warning'
    : status === 'succeeded' ? 'success'
    : 'default'

  const statusLabel = (status === 'succeeded' && errorCount > 0) ? `errors (${errorCount})`
    : (status === 'succeeded' && warningCount > 0) ? `warnings (${warningCount})`
    : status

  const handleClose = () => setClosing(true)

  return (
    <>
      <div
        className="fixed inset-0 bg-black/30 z-40"
        style={{ animation: closing ? 'fadeOut 150ms ease-in forwards' : 'fadeIn 150ms ease-out' }}
        onClick={handleClose}
      />
      <div
        className="fixed top-0 right-0 h-full w-[480px] bg-background border-l shadow-2xl z-50 flex flex-col"
        style={{ animation: closing ? 'slideOutRight 200ms ease-in forwards' : 'slideInRight 200ms ease-out' }}
        onAnimationEnd={() => { if (closing) onClose() }}
      >
        <div className="p-4 border-b space-y-2">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold">model logs</h2>
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={handleClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm text-muted-foreground">{modelName}</span>
            <Badge variant="outline">{runType}</Badge>
            <Badge variant={statusVariant}>{statusLabel}</Badge>
          </div>
          <p className="text-xs text-muted-foreground font-mono">{runId.slice(0, 8)}</p>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-4 space-y-1">
            {loading && logs.length === 0 && (
              <p className="text-sm text-muted-foreground">loading logs...</p>
            )}
            {!loading && logs.length === 0 && (
              <p className="text-sm text-muted-foreground">
                {isRunning ? 'waiting for logs...' : 'no logs recorded for this run'}
              </p>
            )}
            {logs.map((log) => (
              <div key={log.id} className="flex gap-2 py-1 border-b border-border/50 last:border-0">
                <span className="text-[10px] text-muted-foreground font-mono shrink-0 pt-0.5 w-[60px]">
                  {new Date(log.createdAt).toLocaleTimeString()}
                </span>
                <span className={`text-[10px] font-mono uppercase shrink-0 pt-0.5 w-[50px] ${getLevelColor(log.level)}`}>
                  {log.level}
                </span>
                <span className="text-xs font-mono whitespace-pre-wrap break-all">
                  {log.message}
                </span>
              </div>
            ))}
            {isRunning && logs.length > 0 && (
              <div className="flex items-center gap-2 py-2">
                <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
                <span className="text-xs text-muted-foreground">listening for new logs...</span>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>
    </>
  )
}

/* ── inline keyframes ──────────────────────────────── */
const logsSheetStyles = `
@keyframes slideInRight {
    from { transform: translateX(100%); }
    to { transform: translateX(0); }
}
@keyframes slideOutRight {
    from { transform: translateX(0); }
    to { transform: translateX(100%); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
@keyframes fadeOut {
    from { opacity: 1; }
    to { opacity: 0; }
}
`
if (typeof document !== 'undefined' && !document.getElementById('model-logs-sheet-keyframes')) {
  const style = document.createElement('style')
  style.id = 'model-logs-sheet-keyframes'
  style.textContent = logsSheetStyles
  document.head.appendChild(style)
}
