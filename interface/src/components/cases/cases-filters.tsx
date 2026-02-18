'use client'

import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent } from '@/components/ui/card'
import { Search } from 'lucide-react'

interface CasesFiltersProps {
  searchText: string
  onSearchChange: (value: string) => void
  statusFilter: string
  onStatusFilterChange: (value: string) => void
  severityFilter: string
  onSeverityFilterChange: (value: string) => void
}

export function CasesFilters({
  searchText,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  severityFilter,
  onSeverityFilterChange,
}: CasesFiltersProps) {
  return (
    <Card>
      <CardContent className="pt-4 pb-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="search cases..."
              value={searchText}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select value={statusFilter} onValueChange={onStatusFilterChange}>
            <SelectTrigger>
              <SelectValue placeholder="status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">all statuses</SelectItem>
              <SelectItem value="open">open</SelectItem>
              <SelectItem value="investigating">investigating</SelectItem>
              <SelectItem value="resolved">resolved</SelectItem>
              <SelectItem value="closed">closed</SelectItem>
            </SelectContent>
          </Select>
          <Select value={severityFilter} onValueChange={onSeverityFilterChange}>
            <SelectTrigger>
              <SelectValue placeholder="severity" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">all severities</SelectItem>
              <SelectItem value="critical">critical</SelectItem>
              <SelectItem value="high">high</SelectItem>
              <SelectItem value="medium">medium</SelectItem>
              <SelectItem value="low">low</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  )
}
