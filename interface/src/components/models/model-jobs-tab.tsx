import { useState, useRef, useEffect } from 'react'
import { useQuery } from '@apollo/client'
import { GET_MODEL_RUNS } from '@/lib/graphql/queries'
import { useToast } from '@/components/global/toast-provider'
import { DataTable, ColumnDef } from '@/components/tables/data-table'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { FileText } from 'lucide-react'
import { ModelLogsSheet } from './model-logs-sheet'

interface ModelRun {
  id: string
  runType: string
  status: string
  startedAt: string
  finishedAt?: string
  errorMessage?: string
  resultSummary?: any
  modelVersionByModelVersionId?: {
    version: string
    modelByModelId?: {
      id: string
      name: string
    }
  }
  errorLogs?: { totalCount: number }
  warningLogs?: { totalCount: number }
}

function getStatusVariant(status: string, errorCount = 0, warningCount = 0) {
  if (status === 'failed') return 'destructive' as const
  if (status === 'succeeded' && errorCount > 0) return 'destructive' as const
  if (status === 'succeeded' && warningCount > 0) return 'warning' as const
  if (status === 'succeeded') return 'success' as const
  if (status === 'running') return 'default' as const
  return 'secondary' as const
}

function getStatusLabel(status: string, errorCount = 0, warningCount = 0) {
  if (status === 'succeeded' && errorCount > 0) return `errors (${errorCount})`
  if (status === 'succeeded' && warningCount > 0) return `warnings (${warningCount})`
  return status
}

function formatDuration(startedAt: string, finishedAt?: string) {
  if (!startedAt || !finishedAt) return '-'
  const ms = new Date(finishedAt).getTime() - new Date(startedAt).getTime()
  return `${(ms / 1000).toFixed(1)}s`
}

export function ModelJobsTab({ modelId }: { modelId?: string }) {
  const { addToast } = useToast()
  const [selectedRun, setSelectedRun] = useState<ModelRun | null>(null)
  const prevStatusMap = useRef<Map<string, string>>(new Map())
  const isFirstLoad = useRef(true)

  const { loading, error, data } = useQuery(GET_MODEL_RUNS, {
    pollInterval: 5000
  })

  /* detect status transitions and fire toasts */
  useEffect(() => {
    if (!data?.allModelRuns?.nodes) return
    const runs: ModelRun[] = data.allModelRuns.nodes

    if (isFirstLoad.current) {
      runs.forEach(r => prevStatusMap.current.set(r.id, r.status))
      isFirstLoad.current = false
      return
    }

    runs.forEach(r => {
      const prev = prevStatusMap.current.get(r.id)
      if (prev !== r.status) {
        const name = r.modelVersionByModelVersionId?.modelByModelId?.name || 'unknown model'
        if (!prev && (r.status === 'pending' || r.status === 'dispatched')) {
          addToast(`${name} ${r.runType} queued`, { type: 'info', description: `run ${r.id.slice(0, 8)} dispatched` })
        } else if (r.status === 'running') {
          addToast(`${name} ${r.runType} running`, { type: 'info', description: `run ${r.id.slice(0, 8)} is now running` })
        } else if (r.status === 'succeeded') {
          addToast(`${name} ${r.runType} succeeded`, { type: 'success', description: `run ${r.id.slice(0, 8)} completed` })
        } else if (r.status === 'failed') {
          addToast(`${name} ${r.runType} failed`, { type: 'error', description: r.errorMessage || `run ${r.id.slice(0, 8)} failed`, duration: 15000 })
        }
      }
      prevStatusMap.current.set(r.id, r.status)
    })
  }, [data, addToast])

  let jobs: ModelRun[] = data?.allModelRuns?.nodes || []

  if (modelId) {
    jobs = jobs.filter((job) => job.modelVersionByModelVersionId?.modelByModelId?.id === modelId)
  }

  const columns: ColumnDef<ModelRun>[] = [
    {
      accessorKey: 'modelId',
      header: 'model',
      cell: ({ row }) => {
        const mv = row.original.modelVersionByModelVersionId
        return (
          <div className="flex flex-col">
            <span className="font-medium">{mv?.modelByModelId?.name || 'unknown'}</span>
            <span className="text-xs text-muted-foreground">{row.original.id.slice(0, 8)}</span>
          </div>
        )
      }
    },
    {
      accessorKey: 'runType',
      header: 'type',
      cell: ({ row }) => (
        <Badge variant="outline" className="text-xs">
          {row.original.runType}
        </Badge>
      )
    },
    {
      accessorKey: 'status',
      header: 'status',
      cell: ({ row }) => {
        const status = row.original.status
        const errorCount = row.original.errorLogs?.totalCount || 0
        const warningCount = row.original.warningLogs?.totalCount || 0
        return (
          <Badge variant={getStatusVariant(status, errorCount, warningCount)}>
            {getStatusLabel(status, errorCount, warningCount)}
          </Badge>
        )
      }
    },
    {
      accessorKey: 'startedAt',
      header: 'started',
      cell: ({ row }) => (
        <span className="text-xs">{row.original.startedAt
          ? new Date(row.original.startedAt).toLocaleString()
          : '-'}</span>
      )
    },
    {
      accessorKey: 'duration',
      header: 'duration',
      cell: ({ row }) => (
        <span className="text-xs tabular-nums">{formatDuration(row.original.startedAt, row.original.finishedAt)}</span>
      )
    },
    {
      header: '',
      accessorKey: 'logs',
      cell: ({ row }) => (
        <Button
          size="sm"
          variant="ghost"
          className="h-7 px-2 text-xs"
          onClick={() => setSelectedRun(row.original)}
        >
          <FileText className="h-3.5 w-3.5 mr-1" /> logs
        </Button>
      )
    }
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>model execution jobs</CardTitle>
      </CardHeader>
      <CardContent>
        {loading && !data && (
          <div className="space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4">
                <Skeleton className="h-4 w-28" />
                <Skeleton className="h-5 w-14 rounded-full" />
                <Skeleton className="h-5 w-16 rounded-full" />
                <Skeleton className="h-4 w-36" />
                <Skeleton className="h-4 w-36" />
                <Skeleton className="h-4 w-16" />
              </div>
            ))}
          </div>
        )}
        {error && <p className="text-red-500">error: {error.message}</p>}
        {!(loading && !data) && !error && (
          <DataTable columns={columns} data={jobs} />
        )}
      </CardContent>

      {selectedRun && (
        <ModelLogsSheet
          runId={selectedRun.id}
          runType={selectedRun.runType}
          status={selectedRun.status}
          modelName={selectedRun.modelVersionByModelVersionId?.modelByModelId?.name || 'unknown'}
          onClose={() => setSelectedRun(null)}
        />
      )}
    </Card>
  )
}
