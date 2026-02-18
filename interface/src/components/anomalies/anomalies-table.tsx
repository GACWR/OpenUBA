'use client'

import { DataTable, ColumnDef } from '@/components/tables/data-table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface Anomaly {
  id: string
  entityId: string
  entityType: string
  riskScore: number
  anomalyType?: string
  timestamp: string
  acknowledged: boolean
  modelId?: string
  details?: any
}

interface AnomaliesTableProps {
  anomalies: Anomaly[]
  onAcknowledge?: (id: string) => void
  onViewDetails?: (id: string) => void
}

export function AnomaliesTable({ anomalies, onAcknowledge, onViewDetails }: AnomaliesTableProps) {

  const columns: ColumnDef<Anomaly>[] = [
    {
      accessorKey: 'entityId',
      header: 'entity id',
      cell: ({ row }) => (
        <span className="font-medium">{row.original.entityId}</span>
      )
    },
    {
      accessorKey: 'riskScore',
      header: 'risk score',
      cell: ({ row }) => {
        const score = row.original.riskScore
        const variant = score >= 80 ? 'error' : score >= 50 ? 'warning' : 'success'

        return (
          <div className="flex items-center gap-2">
            <Badge variant={variant} size="sm">
              {score}
            </Badge>
          </div>
        )
      }
    },
    {
      accessorKey: 'anomalyType',
      header: 'type',
      cell: ({ row }) => (
        <Badge variant="info" size="sm">
          {row.original.anomalyType || 'unknown'}
        </Badge>
      )
    },
    {
      accessorKey: 'timestamp',
      header: 'timestamp',
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">
          {new Date(row.original.timestamp).toLocaleString()}
        </span>
      )
    },
    {
      accessorKey: 'acknowledged',
      header: 'status',
      cell: ({ row }) => (
        <Badge
          variant={row.original.acknowledged ? 'success' : 'warning'}
          size="sm"
        >
          {row.original.acknowledged ? 'acknowledged' : 'new'}
        </Badge>
      )
    },
    {
      header: 'actions',
      cell: ({ row }) => (
        <div className="flex gap-2">
          {!row.original.acknowledged && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => onAcknowledge?.(row.original.id)}
              className="hover:bg-orange-500/10 hover:border-orange-500/50"
            >
              acknowledge
            </Button>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={() => onViewDetails?.(row.original.id)}
            className="hover:bg-purple-500/10 hover:border-purple-500/50"
          >
            details
          </Button>
        </div>
      )
    }
  ]

  return (
    <div className="rounded-lg border bg-card/50 backdrop-blur-sm">
      <DataTable columns={columns} data={anomalies} hideSearch />
    </div>
  )
}
