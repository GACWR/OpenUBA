'use client'

import { useState, useMemo } from 'react'
import { useQuery } from '@apollo/client'
import { GET_ENTITIES } from '@/lib/graphql/queries'
import { EntitiesTable } from '@/components/entities/entities-table'
import { EntitiesFilters } from '@/components/entities/entities-filters'
import { DonutChart } from '@/components/charts/donut-chart'
import { BarChartComponent } from '@/components/charts/bar-chart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  X, Users, Monitor, ShieldAlert, Activity
} from 'lucide-react'

/* -- types ------------------------------------------------- */

interface EntityItem {
  id: string
  entityId: string
  entityType: string
  displayName?: string
  riskScore: number
  anomalyCount: number
  firstSeen?: string
  lastSeen?: string
  metadata?: any
  createdAt?: string
}

/* -- page -------------------------------------------------- */

export default function EntitiesPage() {
  const { data, loading, error } = useQuery(GET_ENTITIES, { pollInterval: 10000 })
  const entities: EntityItem[] = data?.allEntities?.nodes || []

  /* filter state */
  const [searchText, setSearchText] = useState('')
  const [typeFilter, setTypeFilter] = useState('all')
  const [riskFilter, setRiskFilter] = useState('all')

  /* panel state */
  const [selectedEntity, setSelectedEntity] = useState<EntityItem | null>(null)
  const [panelClosing, setPanelClosing] = useState(false)

  /* filtered entities */
  const filteredEntities = useMemo(() => {
    return entities.filter((e) => {
      if (searchText && !e.entityId.toLowerCase().includes(searchText.toLowerCase())) return false
      if (typeFilter !== 'all' && e.entityType !== typeFilter) return false
      if (riskFilter === 'critical' && e.riskScore < 80) return false
      if (riskFilter === 'high' && (e.riskScore < 50 || e.riskScore >= 80)) return false
      if (riskFilter === 'medium' && (e.riskScore < 20 || e.riskScore >= 50)) return false
      if (riskFilter === 'low' && e.riskScore >= 20) return false
      return true
    })
  }, [entities, searchText, typeFilter, riskFilter])

  /* -- summary metrics -------------------------------------- */
  const totalCount = data?.allEntities?.totalCount ?? entities.length
  const userCount = entities.filter((e) => e.entityType === 'user').length
  const otherCount = entities.filter((e) => e.entityType !== 'user').length
  const highRiskCount = entities.filter((e) => e.riskScore >= 70).length

  /* donut: entity type distribution */
  const typeDistData = useMemo(() => {
    const counts: Record<string, number> = {}
    entities.forEach((e) => { counts[e.entityType] = (counts[e.entityType] || 0) + 1 })
    return Object.entries(counts).map(([name, value]) => ({ name, value }))
  }, [entities])

  /* bar: risk score distribution */
  const riskDistData = useMemo(() => {
    const buckets = { critical: 0, high: 0, medium: 0, low: 0 }
    entities.forEach((e) => {
      if (e.riskScore >= 80) buckets.critical++
      else if (e.riskScore >= 50) buckets.high++
      else if (e.riskScore >= 20) buckets.medium++
      else buckets.low++
    })
    return Object.entries(buckets).map(([risk, count]) => ({ risk, count }))
  }, [entities])

  const hasPanels = !!selectedEntity
  const closePanel = () => setPanelClosing(true)
  const onPanelAnimationEnd = () => {
    if (panelClosing) { setSelectedEntity(null); setPanelClosing(false) }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">Entities</h1>

      {/* -- KPI cards ---------------------------------------- */}
      {loading && !data ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}><CardContent className="pt-4 pb-4">
              <Skeleton className="h-3 w-24 mb-2" />
              <Skeleton className="h-7 w-14" />
            </CardContent></Card>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <KpiCard icon={<Activity className="h-4 w-4" />} label="total entities" value={totalCount} color="text-foreground" />
          <KpiCard icon={<Users className="h-4 w-4" />} label="users" value={userCount} color="text-blue-400" />
          <KpiCard icon={<Monitor className="h-4 w-4" />} label="devices / other" value={otherCount} color="text-cyan-400" />
          <KpiCard icon={<ShieldAlert className="h-4 w-4" />} label="high risk" value={highRiskCount} color="text-red-400" />
        </div>
      )}

      {/* -- charts ------------------------------------------- */}
      {totalCount > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">entity type distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <DonutChart
                data={typeDistData}
                colors={['#3b82f6', '#06b6d4', '#f59e0b', '#10b981', '#8b5cf6']}
                height={220}
                centerLabel={`${totalCount}`}
              />
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">risk score distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <BarChartComponent
                data={riskDistData}
                xKey="risk"
                yKeys={[{ key: 'count', name: 'entities', color: '#8b5cf6' }]}
                height={220}
              />
            </CardContent>
          </Card>
        </div>
      )}

      {/* -- filters ------------------------------------------ */}
      <EntitiesFilters
        searchText={searchText}
        onSearchChange={setSearchText}
        typeFilter={typeFilter}
        onTypeFilterChange={setTypeFilter}
        riskFilter={riskFilter}
        onRiskFilterChange={setRiskFilter}
      />

      {/* -- table --------------------------------------------- */}
      {loading && !data ? (
        <Card><CardContent className="pt-4 space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4">
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-5 w-14 rounded-full" />
              <Skeleton className="h-4 w-12" />
              <Skeleton className="h-4 w-12" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </CardContent></Card>
      ) : error ? (
        <div className="text-red-500">error loading entities: {error.message}</div>
      ) : (
        <EntitiesTable
          entities={filteredEntities}
          onViewDetails={(id) => {
            const e = entities.find((x) => x.id === id)
            if (e) setSelectedEntity(e)
          }}
        />
      )}

      {/* -- slide-out detail panel ---------------------------- */}
      {hasPanels && (
        <>
          <div
            className="fixed inset-0 bg-black/30 z-40"
            style={{ animation: panelClosing ? 'fadeOut 150ms ease-in forwards' : 'fadeIn 150ms ease-out' }}
            onClick={closePanel}
          />
          <div
            className="fixed top-0 right-0 h-full w-[420px] z-50 border-l bg-background shadow-2xl flex flex-col"
            style={{ animation: panelClosing ? 'slideOutRight 200ms ease-in forwards' : 'slideInRight 200ms ease-out' }}
            onAnimationEnd={onPanelAnimationEnd}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b shrink-0">
              <div className="flex items-center gap-2">
                <Users className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-sm font-semibold">entity details</h2>
              </div>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={closePanel}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
              <div>
                <h3 className="text-lg font-bold">{selectedEntity!.displayName || selectedEntity!.entityId}</h3>
                {selectedEntity!.displayName && (
                  <p className="text-sm text-muted-foreground font-mono mt-0.5">{selectedEntity!.entityId}</p>
                )}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <DetailField label="type">
                  <Badge variant="outline" size="sm">{selectedEntity!.entityType}</Badge>
                </DetailField>
                <DetailField label="risk score">
                  <Badge
                    variant={selectedEntity!.riskScore >= 80 ? 'error' : selectedEntity!.riskScore >= 50 ? 'warning' : 'success'}
                    size="sm"
                  >
                    {selectedEntity!.riskScore}
                  </Badge>
                </DetailField>
                <DetailField label="anomalies" value={String(selectedEntity!.anomalyCount)} />
                <DetailField
                  label="first seen"
                  value={selectedEntity!.firstSeen ? new Date(selectedEntity!.firstSeen).toLocaleDateString() : '-'}
                />
                <DetailField
                  label="last seen"
                  value={selectedEntity!.lastSeen ? new Date(selectedEntity!.lastSeen).toLocaleString() : '-'}
                />
                <DetailField
                  label="created"
                  value={selectedEntity!.createdAt ? new Date(selectedEntity!.createdAt).toLocaleDateString() : '-'}
                />
              </div>
              {selectedEntity!.metadata && (
                <div>
                  <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">metadata</span>
                  <pre className="text-xs mt-1 p-2 rounded bg-muted/40 overflow-x-auto">
                    {JSON.stringify(selectedEntity!.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

/* -- KPI card ---------------------------------------------- */

function KpiCard({ icon, label, value, color }: {
  icon: React.ReactNode
  label: string
  value: number
  color: string
}) {
  return (
    <Card>
      <CardContent className="pt-4 pb-4">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-muted-foreground">{icon}</span>
          <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">{label}</span>
        </div>
        <span className={`text-2xl font-bold tabular-nums ${color}`}>{value.toLocaleString()}</span>
      </CardContent>
    </Card>
  )
}

/* -- detail field helper ----------------------------------- */

function DetailField({ label, value, children }: {
  label: string
  value?: string
  children?: React.ReactNode
}) {
  return (
    <div>
      <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">{label}</span>
      <div className="text-sm mt-0.5">{children || value}</div>
    </div>
  )
}

/* -- inline keyframes (shared id guard) -------------------- */
const sheetStyles = `
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
if (typeof document !== 'undefined' && !document.getElementById('entity-sheet-keyframes')) {
  const style = document.createElement('style')
  style.id = 'entity-sheet-keyframes'
  style.textContent = sheetStyles
  document.head.appendChild(style)
}
