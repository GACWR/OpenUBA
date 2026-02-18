'use client'

import { DataTable, ColumnDef } from '@/components/tables/data-table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface EntityItem {
  id: string
  entityId: string
  entityType: string
  displayName?: string
  riskScore: number
  anomalyCount: number
  firstSeen?: string
  lastSeen?: string
}

interface EntitiesTableProps {
  entities: EntityItem[]
  onViewDetails?: (id: string) => void
}

function riskColor(score: number) {
  if (score >= 80) return 'text-red-400'
  if (score >= 50) return 'text-orange-400'
  if (score >= 20) return 'text-yellow-400'
  return 'text-green-400'
}

function formatRelativeTime(dateStr?: string) {
  if (!dateStr) return '-'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export function EntitiesTable({ entities, onViewDetails }: EntitiesTableProps) {
  const columns: ColumnDef<EntityItem>[] = [
    {
      accessorKey: 'entityId',
      header: 'entity',
      cell: ({ row }) => (
        <button
          className="font-medium hover:text-blue-400 transition-colors text-left"
          onClick={() => onViewDetails?.(row.original.id)}
        >
          {row.original.displayName || row.original.entityId}
          {row.original.displayName && (
            <span className="block text-xs text-muted-foreground">{row.original.entityId}</span>
          )}
        </button>
      )
    },
    {
      accessorKey: 'entityType',
      header: 'type',
      cell: ({ row }) => (
        <Badge variant="outline" size="sm">
          {row.original.entityType}
        </Badge>
      )
    },
    {
      accessorKey: 'riskScore',
      header: 'risk score',
      cell: ({ row }) => (
        <span className={`font-bold tabular-nums ${riskColor(row.original.riskScore)}`}>
          {row.original.riskScore}
        </span>
      )
    },
    {
      accessorKey: 'anomalyCount',
      header: 'anomalies',
      cell: ({ row }) => (
        <span className="text-sm tabular-nums">{row.original.anomalyCount}</span>
      )
    },
    {
      accessorKey: 'lastSeen',
      header: 'last seen',
      cell: ({ row }) => (
        <span className="text-xs text-muted-foreground">
          {formatRelativeTime(row.original.lastSeen)}
        </span>
      )
    },
    {
      header: 'actions',
      cell: ({ row }) => (
        <Button
          size="sm"
          variant="outline"
          className="h-7 px-2 text-xs hover:bg-purple-500/10 hover:border-purple-500/50"
          onClick={() => onViewDetails?.(row.original.id)}
        >
          details
        </Button>
      )
    }
  ]

  return (
    <div className="rounded-lg border bg-card/50 backdrop-blur-sm">
      <DataTable columns={columns} data={entities} hideSearch />
    </div>
  )
}
