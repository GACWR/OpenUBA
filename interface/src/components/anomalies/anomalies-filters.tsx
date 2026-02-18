'use client'

import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Card, CardContent } from '@/components/ui/card'
import { Search } from 'lucide-react'

interface AnomaliesFiltersProps {
  searchText: string
  onSearchChange: (value: string) => void
  riskFilter: string
  onRiskFilterChange: (value: string) => void
  ackFilter: string
  onAckFilterChange: (value: string) => void
  modelFilter: string
  onModelFilterChange: (value: string) => void
  availableModels: Array<{ id: string; name: string }>
}

export function AnomaliesFilters({
  searchText,
  onSearchChange,
  riskFilter,
  onRiskFilterChange,
  ackFilter,
  onAckFilterChange,
  modelFilter,
  onModelFilterChange,
  availableModels,
}: AnomaliesFiltersProps) {
  return (
    <Card>
      <CardContent className="pt-4 pb-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="search entity id..."
              value={searchText}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select value={riskFilter} onValueChange={onRiskFilterChange}>
            <SelectTrigger>
              <SelectValue placeholder="risk score" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">all risks</SelectItem>
              <SelectItem value="high">high (80+)</SelectItem>
              <SelectItem value="medium">medium (50-79)</SelectItem>
              <SelectItem value="low">low (0-49)</SelectItem>
            </SelectContent>
          </Select>
          <Select value={ackFilter} onValueChange={onAckFilterChange}>
            <SelectTrigger>
              <SelectValue placeholder="status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">all</SelectItem>
              <SelectItem value="false">unacknowledged</SelectItem>
              <SelectItem value="true">acknowledged</SelectItem>
            </SelectContent>
          </Select>
          <Select value={modelFilter} onValueChange={onModelFilterChange}>
            <SelectTrigger>
              <SelectValue placeholder="model" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">all models</SelectItem>
              {availableModels.map((m) => (
                <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  )
}
