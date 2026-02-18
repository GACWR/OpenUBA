'use client'

import { DataTable, ColumnDef } from '@/components/tables/data-table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

interface Case {
  id: string
  title: string
  status: string
  severity: string
  description?: string
  createdAt: string
}

interface CasesTableProps {
  cases: Case[]
  onViewDetails?: (id: string) => void
}

export function CasesTable({ cases, onViewDetails }: CasesTableProps) {
  const getSeverityVariant = (severity: string): 'error' | 'warning' | 'info' | 'success' => {
    if (severity === 'critical') return 'error'
    if (severity === 'high') return 'warning'
    if (severity === 'medium') return 'info'
    return 'success'
  }
  
  const getStatusVariant = (status: string): 'default' | 'info' | 'success' | 'warning' => {
    if (status === 'resolved' || status === 'closed') return 'success'
    if (status === 'investigating') return 'warning'
    if (status === 'open') return 'info'
    return 'default'
  }

  const columns: ColumnDef<Case>[] = [
    {
      accessorKey: 'title',
      header: 'title',
      cell: ({ row }) => (
        <span className="font-medium">{row.original.title}</span>
      )
    },
    {
      accessorKey: 'status',
      header: 'status',
      cell: ({ row }) => (
        <Badge variant={getStatusVariant(row.original.status)} size="sm">
          {row.original.status}
        </Badge>
      )
    },
    {
      accessorKey: 'severity',
      header: 'severity',
      cell: ({ row }) => (
        <Badge variant={getSeverityVariant(row.original.severity)} size="sm">
          {row.original.severity}
        </Badge>
      )
    },
    {
      accessorKey: 'createdAt',
      header: 'created',
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">
          {new Date(row.original.createdAt).toLocaleString()}
        </span>
      )
    },
    {
      header: 'actions',
      cell: ({ row }) => (
        <Button 
          size="sm" 
          variant="outline" 
          onClick={() => onViewDetails?.(row.original.id)}
          className="hover:bg-purple-500/10 hover:border-purple-500/50"
        >
          view
        </Button>
      )
    }
  ]

  return (
    <div className="rounded-lg border bg-card/50 backdrop-blur-sm">
      <DataTable columns={columns} data={cases} hideSearch />
    </div>
  )
}

