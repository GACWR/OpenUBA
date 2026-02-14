'use client'

import { DataTable, ColumnDef } from '@/components/tables/data-table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'

interface RuleItem {
  id: string
  name: string
  description?: string
  ruleType: string
  severity?: string
  score: number
  enabled: boolean
  lastTriggeredAt?: string
}

interface RulesTableProps {
  rules: RuleItem[]
  onViewDetails?: (id: string) => void
  onEdit?: (id: string) => void
}

function severityVariant(severity?: string) {
  switch (severity) {
    case 'critical': return 'error'
    case 'high': return 'warning'
    case 'medium': return 'info'
    case 'low': return 'success'
    default: return 'outline'
  }
}

function formatRelativeTime(dateStr?: string) {
  if (!dateStr) return 'never'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

export function RulesTable({ rules, onViewDetails, onEdit }: RulesTableProps) {
  const columns: ColumnDef<RuleItem>[] = [
    {
      accessorKey: 'name',
      header: 'rule',
      cell: ({ row }) => (
        <button
          className="font-medium hover:text-blue-400 transition-colors text-left"
          onClick={() => onViewDetails?.(row.original.id)}
        >
          {row.original.name}
          {row.original.description && (
            <span className="block text-xs text-muted-foreground truncate max-w-[250px]">{row.original.description}</span>
          )}
        </button>
      )
    },
    {
      accessorKey: 'ruleType',
      header: 'type',
      cell: ({ row }) => (
        <Badge variant="outline" size="sm">
          {row.original.ruleType}
        </Badge>
      )
    },
    {
      accessorKey: 'severity',
      header: 'severity',
      cell: ({ row }) => (
        <Badge variant={severityVariant(row.original.severity) as any} size="sm">
          {row.original.severity || 'medium'}
        </Badge>
      )
    },
    {
      accessorKey: 'score',
      header: 'score',
      cell: ({ row }) => (
        <span className="text-sm tabular-nums font-bold">{row.original.score}</span>
      )
    },
    {
      accessorKey: 'enabled',
      header: 'status',
      cell: ({ row }) => (
        <Badge variant={row.original.enabled ? 'success' : 'secondary'} size="sm">
          {row.original.enabled ? 'active' : 'disabled'}
        </Badge>
      )
    },
    {
      accessorKey: 'lastTriggeredAt',
      header: 'last triggered',
      cell: ({ row }) => (
        <span className="text-xs text-muted-foreground">
          {formatRelativeTime(row.original.lastTriggeredAt)}
        </span>
      )
    },
    {
      header: 'actions',
      cell: ({ row }) => (
        <div className="flex items-center gap-1">
          {row.original.ruleType === 'flow' && (
            <Button
              size="sm"
              variant="outline"
              className="h-7 px-2 text-xs hover:bg-orange-500/10 hover:border-orange-500/50"
              onClick={() => onEdit?.(row.original.id)}
            >
              edit
            </Button>
          )}
          <Button
            size="sm"
            variant="outline"
            className="h-7 px-2 text-xs hover:bg-purple-500/10 hover:border-purple-500/50"
            onClick={() => onViewDetails?.(row.original.id)}
          >
            details
          </Button>
        </div>
      )
    }
  ]

  return (
    <div className="rounded-lg border bg-card/50 backdrop-blur-sm">
      <DataTable columns={columns} data={rules} hideSearch />
    </div>
  )
}
