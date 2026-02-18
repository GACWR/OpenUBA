'use client'

import * as React from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

// Simple column definition type
export type ColumnDef<TData, TValue = unknown> = {
  accessorKey?: keyof TData | string
  header: string | ((props: any) => React.ReactNode)
  cell?: (props: { row: { original: TData } }) => React.ReactNode
}

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[]
  data: TData[]
  searchKey?: string
  hideSearch?: boolean
  onRowClick?: (row: TData) => void
}

export function DataTable<TData, TValue>({
  columns,
  data,
  searchKey,
  hideSearch,
  onRowClick,
}: DataTableProps<TData, TValue>) {
  const [globalFilter, setGlobalFilter] = React.useState('')
  const [currentPage, setCurrentPage] = React.useState(0)
  const pageSize = 10

  const filteredData = React.useMemo(() => {
    if (!globalFilter) return data
    return data.filter((row) =>
      Object.values(row as any).some((value) =>
        String(value).toLowerCase().includes(globalFilter.toLowerCase())
      )
    )
  }, [data, globalFilter])

  const paginatedData = filteredData.slice(
    currentPage * pageSize,
    (currentPage + 1) * pageSize
  )

  const totalPages = Math.ceil(filteredData.length / pageSize)

  // reset page when data changes
  React.useEffect(() => {
    setCurrentPage(0)
  }, [data])

  return (
    <div className="space-y-4">
      {searchKey && !hideSearch && (
        <Input
          placeholder={`Search ${searchKey}...`}
          value={globalFilter}
          onChange={(e) => {
            setGlobalFilter(e.target.value)
            setCurrentPage(0)
          }}
          className="max-w-sm"
        />
      )}
      <div className="rounded-md border">
        <table className="w-full">
          <thead>
            <tr>
              {columns.map((column, index) => (
                <th
                  key={index}
                  className="h-12 px-4 text-left align-middle font-medium text-muted-foreground"
                >
                  {typeof column.header === 'function'
                    ? column.header({})
                    : column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedData.length > 0 ? (
              paginatedData.map((row, rowIndex) => (
                <tr
                  key={rowIndex}
                  className={`border-b transition-colors hover:bg-muted/50 ${onRowClick ? 'cursor-pointer' : ''}`}
                  onClick={() => onRowClick?.(row)}
                >
                  {columns.map((column, colIndex) => (
                    <td key={colIndex} className="p-4 align-middle">
                      {column.cell
                        ? column.cell({ row: { original: row } })
                        : column.accessorKey
                          ? String((row as any)[column.accessorKey] ?? '')
                          : ''}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
              <tr>
                <td
                  colSpan={columns.length}
                  className="h-24 text-center text-muted-foreground"
                >
                  No results.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            {filteredData.length} total
          </span>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.max(0, p - 1))}
              disabled={currentPage === 0}
            >
              Previous
            </Button>
            <span className="text-sm text-muted-foreground">
              Page {currentPage + 1} of {totalPages || 1}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={currentPage >= totalPages - 1}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
