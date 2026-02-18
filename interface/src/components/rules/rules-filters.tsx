'use client'

import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent } from '@/components/ui/card'
import { Search } from 'lucide-react'

interface RulesFiltersProps {
  searchText: string
  onSearchChange: (value: string) => void
  typeFilter: string
  onTypeFilterChange: (value: string) => void
  severityFilter: string
  onSeverityFilterChange: (value: string) => void
  enabledFilter: string
  onEnabledFilterChange: (value: string) => void
}

export function RulesFilters({
  searchText,
  onSearchChange,
  typeFilter,
  onTypeFilterChange,
  severityFilter,
  onSeverityFilterChange,
  enabledFilter,
  onEnabledFilterChange,
}: RulesFiltersProps) {
  return (
    <Card>
      <CardContent className="pt-4 pb-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="search rules..."
              value={searchText}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select value={typeFilter} onValueChange={onTypeFilterChange}>
            <SelectTrigger>
              <SelectValue placeholder="rule type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">all types</SelectItem>
              <SelectItem value="single-fire">single-fire</SelectItem>
              <SelectItem value="deviation">deviation</SelectItem>
              <SelectItem value="flow">flow</SelectItem>
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
          <Select value={enabledFilter} onValueChange={onEnabledFilterChange}>
            <SelectTrigger>
              <SelectValue placeholder="status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">all statuses</SelectItem>
              <SelectItem value="active">active</SelectItem>
              <SelectItem value="disabled">disabled</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  )
}
