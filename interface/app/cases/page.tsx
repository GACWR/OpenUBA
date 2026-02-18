'use client'

import { useState, useMemo } from 'react'
import { useQuery } from '@apollo/client'
import { GET_CASES } from '@/lib/graphql/queries'
import { CasesTable } from '@/components/cases/cases-table'
import { CasesFilters } from '@/components/cases/cases-filters'
import { CaseDetailView } from '@/components/cases/case-detail-view'
import { DonutChart } from '@/components/charts/donut-chart'
import { BarChartComponent } from '@/components/charts/bar-chart'
import { TimeseriesChart } from '@/components/charts/timeseries-chart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Loader2, X, Briefcase, ShieldAlert, CheckCircle
} from 'lucide-react'

/* ── types ─────────────────────────────────────────── */

interface CaseItem {
  id: string
  title: string
  status: string
  severity: string
  description?: string
  assignedTo?: string
  analystNotes?: string
  createdAt: string
  updatedAt?: string
  resolvedAt?: string
  caseAnomaliesByCaseId?: {
    nodes: Array<{
      anomalyByAnomalyId: {
        id: string
        entityId: string
        entityType: string
        riskScore: number
        anomalyType?: string
        timestamp: string
        acknowledged: boolean
      }
    }>
  }
}

/* ── page ──────────────────────────────────────────── */

export default function CasesPage() {
  const { data, loading, error, refetch } = useQuery(GET_CASES, { pollInterval: 5000 })
  const cases: CaseItem[] = data?.allCases?.nodes || []

  /* filter state */
  const [searchText, setSearchText] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [severityFilter, setSeverityFilter] = useState('all')

  /* panel state */
  const [selectedCase, setSelectedCase] = useState<CaseItem | null>(null)
  const [panelClosing, setPanelClosing] = useState(false)

  /* filtered cases */
  const filteredCases = useMemo(() => {
    return cases.filter((c) => {
      if (searchText && !c.title.toLowerCase().includes(searchText.toLowerCase())) return false
      if (statusFilter !== 'all' && c.status !== statusFilter) return false
      if (severityFilter !== 'all' && c.severity !== severityFilter) return false
      return true
    })
  }, [cases, searchText, statusFilter, severityFilter])

  /* ── summary metrics ─────────────────────────────── */
  const totalCount = data?.allCases?.totalCount ?? cases.length
  const openCount = cases.filter((c) => c.status === 'open' || c.status === 'investigating').length
  const critHighCount = cases.filter((c) => c.severity === 'critical' || c.severity === 'high').length
  const resolvedCount = cases.filter((c) => c.status === 'resolved' || c.status === 'closed').length

  /* donut: status distribution */
  const statusData = useMemo(() => {
    const counts: Record<string, number> = {}
    cases.forEach((c) => { counts[c.status] = (counts[c.status] || 0) + 1 })
    return Object.entries(counts).map(([name, value]) => ({ name, value }))
  }, [cases])

  /* bar: severity breakdown */
  const severityBarData = useMemo(() => {
    const counts: Record<string, number> = { critical: 0, high: 0, medium: 0, low: 0 }
    cases.forEach((c) => { if (counts[c.severity] !== undefined) counts[c.severity]++ })
    return Object.entries(counts).map(([severity, count]) => ({ severity, count }))
  }, [cases])

  /* timeseries: cases by day */
  const timeseriesData = useMemo(() => {
    const byDay = new Map<string, number>()
    cases.forEach((c) => {
      const day = new Date(c.createdAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      byDay.set(day, (byDay.get(day) || 0) + 1)
    })
    return Array.from(byDay.entries())
      .slice(-14)
      .map(([day, count]) => ({ day, cases: count }))
  }, [cases])

  const hasPanels = !!selectedCase
  const closePanel = () => setPanelClosing(true)
  const onPanelAnimationEnd = () => {
    if (panelClosing) { setSelectedCase(null); setPanelClosing(false) }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">Cases</h1>

      {/* ── KPI cards ──────────────────────────────── */}
      {loading && !data ? (
        <div className="grid grid-cols-3 gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Card key={i}><CardContent className="pt-4 pb-4">
              <Skeleton className="h-3 w-24 mb-2" />
              <Skeleton className="h-7 w-14" />
            </CardContent></Card>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-3">
          <KpiCard icon={<Briefcase className="h-4 w-4" />} label="open cases" value={openCount} color="text-blue-400" />
          <KpiCard icon={<ShieldAlert className="h-4 w-4" />} label="critical / high" value={critHighCount} color="text-red-400" />
          <KpiCard icon={<CheckCircle className="h-4 w-4" />} label="resolved" value={resolvedCount} color="text-green-400" />
        </div>
      )}

      {/* ── charts ─────────────────────────────────── */}
      {totalCount > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">status distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <DonutChart
                data={statusData}
                colors={['#3b82f6', '#f59e0b', '#22c55e', '#6b7280']}
                height={200}
                centerLabel={`${openCount}`}
              />
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">severity breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              <BarChartComponent
                data={severityBarData}
                xKey="severity"
                yKeys={[{ key: 'count', name: 'cases', color: '#8b5cf6' }]}
                height={200}
              />
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">cases over time</CardTitle>
            </CardHeader>
            <CardContent>
              <TimeseriesChart
                data={timeseriesData}
                xKey="day"
                yKeys={[{ key: 'cases', name: 'cases', color: '#06b6d4' }]}
                height={200}
              />
            </CardContent>
          </Card>
        </div>
      )}

      {/* ── filters ────────────────────────────────── */}
      <CasesFilters
        searchText={searchText}
        onSearchChange={setSearchText}
        statusFilter={statusFilter}
        onStatusFilterChange={setStatusFilter}
        severityFilter={severityFilter}
        onSeverityFilterChange={setSeverityFilter}
      />

      {/* ── table ──────────────────────────────────── */}
      {loading && !data ? (
        <Card><CardContent className="pt-4 space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-5 w-16 rounded-full" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 flex-1" />
            </div>
          ))}
        </CardContent></Card>
      ) : error ? (
        <div className="text-red-500">error loading cases: {error.message}</div>
      ) : (
        <CasesTable
          cases={filteredCases}
          onViewDetails={(id) => {
            const c = cases.find((x) => x.id === id)
            if (c) setSelectedCase(c)
          }}
        />
      )}

      {/* ── slide-out detail panel ─────────────────── */}
      {hasPanels && (
        <>
          <div
            className="fixed inset-0 bg-black/30 z-40"
            style={{ animation: panelClosing ? 'fadeOut 150ms ease-in forwards' : 'fadeIn 150ms ease-out' }}
            onClick={closePanel}
          />
          <div
            className="fixed top-0 right-0 h-full w-[440px] z-50 border-l bg-background shadow-2xl flex flex-col"
            style={{ animation: panelClosing ? 'slideOutRight 200ms ease-in forwards' : 'slideInRight 200ms ease-out' }}
            onAnimationEnd={onPanelAnimationEnd}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b shrink-0">
              <div className="flex items-center gap-2">
                <Briefcase className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-sm font-semibold">case details</h2>
              </div>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={closePanel}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-4">
              <CaseDetailView
                caseItem={selectedCase!}
                onStatusChanged={() => refetch()}
              />
            </div>
          </div>
        </>
      )}
    </div>
  )
}

/* ── KPI card ──────────────────────────────────────── */

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

/* ── inline keyframes (shared id guard) ────────────── */
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
if (typeof document !== 'undefined' && !document.getElementById('case-sheet-keyframes')) {
  const style = document.createElement('style')
  style.id = 'case-sheet-keyframes'
  style.textContent = sheetStyles
  document.head.appendChild(style)
}
