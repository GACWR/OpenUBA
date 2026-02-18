'use client'

import { useState, useMemo } from 'react'
import { useQuery, useMutation } from '@apollo/client'
import { GET_ANOMALIES } from '@/lib/graphql/queries'
import { ACKNOWLEDGE_ANOMALY, CREATE_CASE, LINK_ANOMALY_TO_CASE } from '@/lib/graphql/mutations'
import { AnomaliesTable } from '@/components/anomalies/anomalies-table'
import { AnomaliesFilters } from '@/components/anomalies/anomalies-filters'
import { AnomalyDetailDrawer } from '@/components/anomalies/anomaly-detail-drawer'
import { DonutChart } from '@/components/charts/donut-chart'
import { TimeseriesChart } from '@/components/charts/timeseries-chart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useToast } from '@/components/global/toast-provider'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Loader2, X, AlertTriangle, ShieldAlert, Eye, TrendingUp,
  CheckCircle
} from 'lucide-react'

/* ── types ─────────────────────────────────────────── */

interface Anomaly {
  id: string
  entityId: string
  entityType: string
  riskScore: number
  anomalyType?: string
  timestamp: string
  acknowledged: boolean
  acknowledgedAt?: string
  acknowledgedBy?: string
  modelId?: string
  modelByModelId?: { name: string; version: string }
  details?: any
  createdAt?: string
}

/* ── page ──────────────────────────────────────────── */

export default function AnomaliesPage() {
  const { addToast } = useToast()
  const { data, loading, error, refetch } = useQuery(GET_ANOMALIES, { pollInterval: 5000 })
  const anomalies: Anomaly[] = data?.allAnomalies?.nodes || []

  /* mutations */
  const [acknowledgeAnomaly] = useMutation(ACKNOWLEDGE_ANOMALY)
  const [createCase] = useMutation(CREATE_CASE)
  const [linkAnomalyToCase] = useMutation(LINK_ANOMALY_TO_CASE)

  /* filter state */
  const [searchText, setSearchText] = useState('')
  const [riskFilter, setRiskFilter] = useState('all')
  const [ackFilter, setAckFilter] = useState('all')
  const [modelFilter, setModelFilter] = useState('all')

  /* panel state */
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(null)
  const [panelClosing, setPanelClosing] = useState(false)

  /* acknowledge dialog state */
  const [ackDialog, setAckDialog] = useState<{ anomaly: Anomaly } | null>(null)
  const [ackNotes, setAckNotes] = useState('')
  const [ackCreateCase, setAckCreateCase] = useState(false)
  const [ackLoading, setAckLoading] = useState(false)

  /* available models for filter */
  const availableModels = useMemo(() => {
    const map = new Map<string, string>()
    anomalies.forEach((a) => {
      if (a.modelId && !map.has(a.modelId)) {
        map.set(a.modelId, a.modelByModelId?.name || a.modelId.slice(0, 8))
      }
    })
    return Array.from(map.entries()).map(([id, name]) => ({ id, name }))
  }, [anomalies])

  /* filtered anomalies */
  const filteredAnomalies = useMemo(() => {
    return anomalies.filter((a) => {
      if (searchText && !a.entityId.toLowerCase().includes(searchText.toLowerCase())) return false
      if (riskFilter === 'high' && a.riskScore < 80) return false
      if (riskFilter === 'medium' && (a.riskScore < 50 || a.riskScore >= 80)) return false
      if (riskFilter === 'low' && a.riskScore >= 50) return false
      if (ackFilter === 'true' && !a.acknowledged) return false
      if (ackFilter === 'false' && a.acknowledged) return false
      if (modelFilter !== 'all' && a.modelId !== modelFilter) return false
      return true
    })
  }, [anomalies, searchText, riskFilter, ackFilter, modelFilter])

  /* ── summary metrics ─────────────────────────────── */
  const totalCount = data?.allAnomalies?.totalCount ?? anomalies.length
  const highRiskCount = anomalies.filter((a) => a.riskScore >= 80).length
  const unackedCount = anomalies.filter((a) => !a.acknowledged).length
  const avgRisk = totalCount > 0
    ? Math.round(anomalies.reduce((sum, a) => sum + (a.riskScore || 0), 0) / totalCount)
    : 0

  /* donut: severity distribution */
  const severityData = useMemo(() => {
    const high = anomalies.filter((a) => a.riskScore >= 80).length
    const medium = anomalies.filter((a) => a.riskScore >= 50 && a.riskScore < 80).length
    const low = anomalies.filter((a) => a.riskScore < 50).length
    return [
      { name: 'high (80+)', value: high },
      { name: 'medium (50-79)', value: medium },
      { name: 'low (0-49)', value: low },
    ]
  }, [anomalies])

  /* timeseries: anomalies by day */
  const timeseriesData = useMemo(() => {
    const byDay = new Map<string, { total: number; high: number }>()
    anomalies.forEach((a) => {
      const day = new Date(a.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      const entry = byDay.get(day) || { total: 0, high: 0 }
      entry.total++
      if (a.riskScore >= 80) entry.high++
      byDay.set(day, entry)
    })
    return Array.from(byDay.entries())
      .slice(-14)
      .map(([day, counts]) => ({ day, total: counts.total, high: counts.high }))
  }, [anomalies])

  /* ── acknowledge flow ────────────────────────────── */
  const openAckDialog = (anomalyId: string) => {
    const anomaly = anomalies.find((a) => a.id === anomalyId)
    if (!anomaly) return
    setAckDialog({ anomaly })
    setAckNotes('')
    setAckCreateCase(anomaly.riskScore >= 80)
  }

  const handleAcknowledge = async () => {
    if (!ackDialog) return
    setAckLoading(true)
    try {
      await acknowledgeAnomaly({
        variables: { id: ackDialog.anomaly.id, acknowledgedBy: 'analyst' }
      })

      if (ackCreateCase) {
        const caseResult = await createCase({
          variables: {
            input: {
              case: {
                title: `anomaly: ${ackDialog.anomaly.entityId} (risk ${ackDialog.anomaly.riskScore})`,
                description: ackNotes || `auto-created from anomaly acknowledgement`,
                status: 'open',
                severity: ackDialog.anomaly.riskScore >= 80 ? 'critical' : ackDialog.anomaly.riskScore >= 50 ? 'high' : 'medium',
                analystNotes: ackNotes || null,
              }
            }
          }
        })
        const newCaseId = caseResult.data?.createCase?.case?.id
        if (newCaseId) {
          await linkAnomalyToCase({
            variables: { caseId: newCaseId, anomalyId: ackDialog.anomaly.id }
          })
          addToast('Case Created', {
            type: 'success',
            description: `case linked to anomaly ${ackDialog.anomaly.entityId}`,
          })
        }
      }

      addToast('Anomaly Acknowledged', {
        type: 'success',
        description: `${ackDialog.anomaly.entityId} marked as acknowledged`,
      })
      setAckDialog(null)
      setSelectedAnomaly(null)
      refetch()
    } catch (err: any) {
      addToast('Error', {
        type: 'error',
        description: err.message,
        duration: 15000,
      })
    } finally {
      setAckLoading(false)
    }
  }

  /* ── create case from panel ──────────────────────── */
  const handleCreateCase = (anomalyId: string) => {
    const anomaly = anomalies.find((a) => a.id === anomalyId)
    if (!anomaly) return
    setAckDialog({ anomaly })
    setAckNotes('')
    setAckCreateCase(true)
  }

  const hasPanels = !!selectedAnomaly
  const closePanel = () => setPanelClosing(true)
  const onPanelAnimationEnd = () => {
    if (panelClosing) { setSelectedAnomaly(null); setPanelClosing(false) }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">Anomalies</h1>

      {/* ── KPI cards ──────────────────────────────── */}
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
          <KpiCard icon={<AlertTriangle className="h-4 w-4" />} label="total anomalies" value={totalCount} color="text-foreground" />
          <KpiCard icon={<ShieldAlert className="h-4 w-4" />} label="high risk" value={highRiskCount} color="text-red-400" />
          <KpiCard icon={<Eye className="h-4 w-4" />} label="unacknowledged" value={unackedCount} color="text-orange-400" />
          <KpiCard icon={<TrendingUp className="h-4 w-4" />} label="avg risk score" value={avgRisk} color="text-yellow-400" />
        </div>
      )}

      {/* ── charts ─────────────────────────────────── */}
      {totalCount > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">severity distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <DonutChart
                data={severityData}
                colors={['#ef4444', '#f59e0b', '#22c55e']}
                height={220}
                centerLabel={`${highRiskCount}`}
              />
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">anomalies over time</CardTitle>
            </CardHeader>
            <CardContent>
              <TimeseriesChart
                data={timeseriesData}
                xKey="day"
                yKeys={[
                  { key: 'total', name: 'total', color: '#6366f1' },
                  { key: 'high', name: 'high risk', color: '#ef4444' },
                ]}
                height={220}
              />
            </CardContent>
          </Card>
        </div>
      )}

      {/* ── filters ────────────────────────────────── */}
      <AnomaliesFilters
        searchText={searchText}
        onSearchChange={setSearchText}
        riskFilter={riskFilter}
        onRiskFilterChange={setRiskFilter}
        ackFilter={ackFilter}
        onAckFilterChange={setAckFilter}
        modelFilter={modelFilter}
        onModelFilterChange={setModelFilter}
        availableModels={availableModels}
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
        <div className="text-red-500">error loading anomalies: {error.message}</div>
      ) : (
        <AnomaliesTable
          anomalies={filteredAnomalies}
          onAcknowledge={openAckDialog}
          onViewDetails={(id) => {
            const a = anomalies.find((x) => x.id === id)
            if (a) setSelectedAnomaly(a)
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
                <AlertTriangle className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-sm font-semibold">anomaly details</h2>
              </div>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={closePanel}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-4">
              <AnomalyDetailDrawer
                anomaly={selectedAnomaly!}
                onAcknowledge={openAckDialog}
                onCreateCase={handleCreateCase}
              />
            </div>
          </div>
        </>
      )}

      {/* ── acknowledge confirmation dialog ────────── */}
      <Dialog open={!!ackDialog} onOpenChange={(open) => !open && setAckDialog(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-orange-400" />
              acknowledge anomaly
            </DialogTitle>
          </DialogHeader>
          {ackDialog && (
            <div className="space-y-4 py-2">
              <div className="space-y-2">
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40">
                  <span className="text-sm text-muted-foreground">entity</span>
                  <span className="text-sm font-mono font-medium">{ackDialog.anomaly.entityId}</span>
                </div>
                <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40">
                  <span className="text-sm text-muted-foreground">risk score</span>
                  <Badge variant={ackDialog.anomaly.riskScore >= 80 ? 'error' : ackDialog.anomaly.riskScore >= 50 ? 'warning' : 'success'} size="sm">
                    {ackDialog.anomaly.riskScore}
                  </Badge>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">analyst notes</label>
                <Textarea
                  placeholder="optional notes about this anomaly..."
                  value={ackNotes}
                  onChange={(e) => setAckNotes(e.target.value)}
                  rows={3}
                />
              </div>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={ackCreateCase}
                  onChange={(e) => setAckCreateCase(e.target.checked)}
                  className="rounded border-border"
                />
                <span className="text-sm">also create a case</span>
                {ackDialog.anomaly.riskScore >= 80 && (
                  <Badge variant="error" size="sm">recommended</Badge>
                )}
              </label>
            </div>
          )}
          <DialogFooter>
            <Button variant="ghost" onClick={() => setAckDialog(null)} disabled={ackLoading}>
              cancel
            </Button>
            <Button onClick={handleAcknowledge} disabled={ackLoading}>
              {ackLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              {ackCreateCase ? 'acknowledge & create case' : 'acknowledge'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
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

/* ── inline keyframes ──────────────────────────────── */
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
if (typeof document !== 'undefined' && !document.getElementById('anomaly-sheet-keyframes')) {
  const style = document.createElement('style')
  style.id = 'anomaly-sheet-keyframes'
  style.textContent = sheetStyles
  document.head.appendChild(style)
}
