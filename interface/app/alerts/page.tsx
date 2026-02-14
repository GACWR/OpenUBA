'use client'

import { useState, useMemo } from 'react'
import { useQuery, useMutation } from '@apollo/client'
import { GET_ALERTS } from '@/lib/graphql/queries'
import { ACKNOWLEDGE_ALERT } from '@/lib/graphql/mutations'
import { DataTable, ColumnDef } from '@/components/tables/data-table'
import { DonutChart } from '@/components/charts/donut-chart'
import { TimeseriesChart } from '@/components/charts/timeseries-chart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/global/toast-provider'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Loader2, X, Bell, ShieldAlert, Eye, CheckCircle,
  Search, AlertTriangle
} from 'lucide-react'

/* -- types ------------------------------------------------- */

interface AlertItem {
  id: string
  ruleId: string
  severity: string
  message: string
  entityId?: string
  entityType?: string
  context?: any
  acknowledged: boolean
  acknowledgedAt?: string
  acknowledgedBy?: string
  createdAt: string
  ruleByRuleId?: { name: string }
}

/* -- helpers ------------------------------------------------ */

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
  if (!dateStr) return '-'
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

/* -- page -------------------------------------------------- */

export default function AlertsPage() {
  const { addToast } = useToast()
  const { data, loading, error, refetch } = useQuery(GET_ALERTS, { pollInterval: 5000 })
  const alerts: AlertItem[] = data?.allAlerts?.nodes || []

  const [acknowledgeAlert] = useMutation(ACKNOWLEDGE_ALERT)

  /* filter state */
  const [searchText, setSearchText] = useState('')
  const [severityFilter, setSeverityFilter] = useState('all')
  const [ackFilter, setAckFilter] = useState('all')
  const [ruleFilter, setRuleFilter] = useState('all')

  /* panel state */
  const [selectedAlert, setSelectedAlert] = useState<AlertItem | null>(null)
  const [panelClosing, setPanelClosing] = useState(false)

  /* ack dialog state */
  const [ackDialog, setAckDialog] = useState<{ alert: AlertItem } | null>(null)
  const [ackLoading, setAckLoading] = useState(false)

  /* available rules for filter */
  const availableRules = useMemo(() => {
    const map = new Map<string, string>()
    alerts.forEach((a) => {
      if (a.ruleId && !map.has(a.ruleId)) {
        map.set(a.ruleId, a.ruleByRuleId?.name || a.ruleId.slice(0, 8))
      }
    })
    return Array.from(map.entries()).map(([id, name]) => ({ id, name }))
  }, [alerts])

  /* filtered alerts */
  const filteredAlerts = useMemo(() => {
    return alerts.filter((a) => {
      if (searchText) {
        const q = searchText.toLowerCase()
        const matchMsg = a.message?.toLowerCase().includes(q)
        const matchEntity = a.entityId?.toLowerCase().includes(q)
        const matchRule = a.ruleByRuleId?.name?.toLowerCase().includes(q)
        if (!matchMsg && !matchEntity && !matchRule) return false
      }
      if (severityFilter !== 'all' && a.severity !== severityFilter) return false
      if (ackFilter === 'true' && !a.acknowledged) return false
      if (ackFilter === 'false' && a.acknowledged) return false
      if (ruleFilter !== 'all' && a.ruleId !== ruleFilter) return false
      return true
    })
  }, [alerts, searchText, severityFilter, ackFilter, ruleFilter])

  /* -- summary metrics -------------------------------------- */
  const totalCount = data?.allAlerts?.totalCount ?? alerts.length
  const criticalCount = alerts.filter((a) => a.severity === 'critical').length
  const unackedCount = alerts.filter((a) => !a.acknowledged).length
  const now = new Date()
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const firedToday = alerts.filter((a) => new Date(a.createdAt).getTime() >= todayStart).length

  /* donut: severity distribution */
  const severityData = useMemo(() => {
    const counts = { critical: 0, high: 0, medium: 0, low: 0 }
    alerts.forEach((a) => {
      const sev = a.severity as keyof typeof counts
      if (sev in counts) counts[sev]++
    })
    return Object.entries(counts).map(([name, value]) => ({ name, value }))
  }, [alerts])

  /* timeseries: alerts by day */
  const timeseriesData = useMemo(() => {
    const byDay = new Map<string, { total: number; critical: number }>()
    alerts.forEach((a) => {
      const day = new Date(a.createdAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      const entry = byDay.get(day) || { total: 0, critical: 0 }
      entry.total++
      if (a.severity === 'critical' || a.severity === 'high') entry.critical++
      byDay.set(day, entry)
    })
    return Array.from(byDay.entries())
      .slice(-14)
      .map(([day, counts]) => ({ day, total: counts.total, critical: counts.critical }))
  }, [alerts])

  /* -- acknowledge flow ------------------------------------- */
  const openAckDialog = (alertId: string) => {
    const alert = alerts.find((a) => a.id === alertId)
    if (!alert) return
    setAckDialog({ alert })
  }

  const handleAcknowledge = async () => {
    if (!ackDialog) return
    setAckLoading(true)
    try {
      await acknowledgeAlert({
        variables: { id: ackDialog.alert.id, acknowledgedBy: 'analyst' }
      })
      addToast('alert acknowledged', {
        type: 'success',
        description: `alert for ${ackDialog.alert.entityId || 'entity'} acknowledged`,
      })
      setAckDialog(null)
      setSelectedAlert(null)
      refetch()
    } catch (err: any) {
      addToast('error', {
        type: 'error',
        description: err.message,
        duration: 15000,
      })
    } finally {
      setAckLoading(false)
    }
  }

  /* -- panel ------------------------------------------------ */
  const hasPanels = !!selectedAlert
  const closePanel = () => setPanelClosing(true)
  const onPanelAnimationEnd = () => {
    if (panelClosing) { setSelectedAlert(null); setPanelClosing(false) }
  }

  /* -- table columns ---------------------------------------- */
  const columns: ColumnDef<AlertItem>[] = [
    {
      accessorKey: 'createdAt',
      header: 'time',
      cell: ({ row }) => (
        <span className="text-xs text-muted-foreground whitespace-nowrap">
          {formatRelativeTime(row.original.createdAt)}
        </span>
      )
    },
    {
      accessorKey: 'severity',
      header: 'severity',
      cell: ({ row }) => (
        <Badge variant={severityVariant(row.original.severity) as any} size="sm">
          {row.original.severity}
        </Badge>
      )
    },
    {
      accessorKey: 'message',
      header: 'message',
      cell: ({ row }) => (
        <span className="text-sm truncate max-w-[300px] block">{row.original.message}</span>
      )
    },
    {
      accessorKey: 'entityId',
      header: 'entity',
      cell: ({ row }) => (
        <span className="text-xs font-mono">{row.original.entityId || '-'}</span>
      )
    },
    {
      accessorKey: 'ruleId',
      header: 'rule',
      cell: ({ row }) => (
        <span className="text-xs text-muted-foreground">
          {row.original.ruleByRuleId?.name || '-'}
        </span>
      )
    },
    {
      accessorKey: 'acknowledged',
      header: 'status',
      cell: ({ row }) => (
        <Badge variant={row.original.acknowledged ? 'secondary' : 'warning'} size="sm">
          {row.original.acknowledged ? 'acknowledged' : 'open'}
        </Badge>
      )
    },
    {
      header: 'actions',
      cell: ({ row }) => (
        <div className="flex items-center gap-1">
          {!row.original.acknowledged && (
            <Button
              size="sm"
              variant="outline"
              className="h-7 px-2 text-xs hover:bg-emerald-500/10 hover:border-emerald-500/50"
              onClick={() => openAckDialog(row.original.id)}
            >
              acknowledge
            </Button>
          )}
          <Button
            size="sm"
            variant="outline"
            className="h-7 px-2 text-xs hover:bg-purple-500/10 hover:border-purple-500/50"
            onClick={() => setSelectedAlert(row.original)}
          >
            details
          </Button>
        </div>
      )
    }
  ]

  const isInitialLoad = loading && !data

  /* -- context parsing helper ------------------------------- */
  function parseContext(ctx: any): any {
    if (!ctx) return null
    if (typeof ctx === 'string') {
      try { return JSON.parse(ctx) } catch { return ctx }
    }
    return ctx
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold tracking-tight">Alerts</h1>

      {/* -- KPI cards ---------------------------------------- */}
      {isInitialLoad ? (
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
          <KpiCard icon={<Bell className="h-4 w-4" />} label="total alerts" value={totalCount} color="text-foreground" />
          <KpiCard icon={<ShieldAlert className="h-4 w-4" />} label="critical" value={criticalCount} color="text-red-400" />
          <KpiCard icon={<Eye className="h-4 w-4" />} label="unacknowledged" value={unackedCount} color="text-orange-400" />
          <KpiCard icon={<AlertTriangle className="h-4 w-4" />} label="fired today" value={firedToday} color="text-yellow-400" />
        </div>
      )}

      {/* -- charts ------------------------------------------- */}
      {!isInitialLoad && totalCount > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">severity distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <DonutChart
                data={severityData.some(d => d.value > 0) ? severityData : [{ name: 'none', value: 0 }]}
                colors={['#ef4444', '#f97316', '#eab308', '#22c55e']}
                height={220}
                centerLabel={`${totalCount}`}
              />
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">alerts over time</CardTitle>
            </CardHeader>
            <CardContent>
              <TimeseriesChart
                data={timeseriesData}
                xKey="day"
                yKeys={[
                  { key: 'total', name: 'total', color: '#6366f1' },
                  { key: 'critical', name: 'critical/high', color: '#ef4444' },
                ]}
                height={220}
              />
            </CardContent>
          </Card>
        </div>
      )}

      {/* -- filters ------------------------------------------ */}
      <Card>
        <CardContent className="pt-4 pb-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                className="pl-9 h-9"
                placeholder="search alerts..."
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
              />
            </div>
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger className="h-9">
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
            <Select value={ackFilter} onValueChange={setAckFilter}>
              <SelectTrigger className="h-9">
                <SelectValue placeholder="status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">all statuses</SelectItem>
                <SelectItem value="false">open</SelectItem>
                <SelectItem value="true">acknowledged</SelectItem>
              </SelectContent>
            </Select>
            <Select value={ruleFilter} onValueChange={setRuleFilter}>
              <SelectTrigger className="h-9">
                <SelectValue placeholder="rule" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">all rules</SelectItem>
                {availableRules.map((r) => (
                  <SelectItem key={r.id} value={r.id}>{r.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* -- table --------------------------------------------- */}
      {isInitialLoad ? (
        <Card><CardContent className="pt-4 space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4">
              <Skeleton className="h-4 w-16" />
              <Skeleton className="h-5 w-14 rounded-full" />
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-5 w-14 rounded-full" />
              <Skeleton className="h-7 w-16" />
            </div>
          ))}
        </CardContent></Card>
      ) : error ? (
        <div className="text-red-500">error loading alerts: {error.message}</div>
      ) : (
        <div className="rounded-lg border bg-card/50 backdrop-blur-sm">
          <DataTable columns={columns} data={filteredAlerts} hideSearch />
        </div>
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
            className="fixed top-0 right-0 h-full w-[440px] z-50 border-l bg-background shadow-2xl flex flex-col"
            style={{ animation: panelClosing ? 'slideOutRight 200ms ease-in forwards' : 'slideInRight 200ms ease-out' }}
            onAnimationEnd={onPanelAnimationEnd}
          >
            <div className="flex items-center justify-between px-5 py-4 border-b shrink-0">
              <div className="flex items-center gap-2">
                <Bell className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-sm font-semibold">alert details</h2>
              </div>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={closePanel}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
              <div>
                <h3 className="text-lg font-bold">{selectedAlert!.message}</h3>
                <p className="text-sm text-muted-foreground mt-0.5">
                  rule: {selectedAlert!.ruleByRuleId?.name || selectedAlert!.ruleId?.slice(0, 8)}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <DetailField label="severity">
                  <Badge variant={severityVariant(selectedAlert!.severity) as any} size="sm">
                    {selectedAlert!.severity}
                  </Badge>
                </DetailField>
                <DetailField label="status">
                  <Badge variant={selectedAlert!.acknowledged ? 'secondary' : 'warning'} size="sm">
                    {selectedAlert!.acknowledged ? 'acknowledged' : 'open'}
                  </Badge>
                </DetailField>
                <DetailField label="entity">
                  <span className="text-sm font-mono">{selectedAlert!.entityId || '-'}</span>
                </DetailField>
                <DetailField label="entity type" value={selectedAlert!.entityType || '-'} />
                <DetailField
                  label="fired at"
                  value={new Date(selectedAlert!.createdAt).toLocaleString()}
                />
                {selectedAlert!.acknowledgedAt && (
                  <DetailField
                    label="acknowledged at"
                    value={new Date(selectedAlert!.acknowledgedAt).toLocaleString()}
                  />
                )}
                {selectedAlert!.acknowledgedBy && (
                  <DetailField label="acknowledged by" value={selectedAlert!.acknowledgedBy} />
                )}
              </div>

              {/* context */}
              {selectedAlert!.context && (
                <div>
                  <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">context</span>
                  <pre className="text-xs mt-1 p-2 rounded bg-muted/40 overflow-x-auto whitespace-pre-wrap">
                    {JSON.stringify(parseContext(selectedAlert!.context), null, 2)}
                  </pre>
                </div>
              )}

              {/* acknowledge button */}
              {!selectedAlert!.acknowledged && (
                <Button
                  size="sm"
                  className="w-full gap-1.5"
                  onClick={() => {
                    openAckDialog(selectedAlert!.id)
                  }}
                >
                  <CheckCircle className="h-3.5 w-3.5" />
                  acknowledge alert
                </Button>
              )}
            </div>
          </div>
        </>
      )}

      {/* -- acknowledge confirmation dialog ------------------- */}
      <Dialog open={!!ackDialog} onOpenChange={(open) => !open && setAckDialog(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-orange-400" />
              acknowledge alert
            </DialogTitle>
          </DialogHeader>
          {ackDialog && (
            <div className="space-y-3 py-2">
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40">
                <span className="text-sm text-muted-foreground">message</span>
                <span className="text-sm font-medium truncate max-w-[250px]">{ackDialog.alert.message}</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40">
                <span className="text-sm text-muted-foreground">severity</span>
                <Badge variant={severityVariant(ackDialog.alert.severity) as any} size="sm">
                  {ackDialog.alert.severity}
                </Badge>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40">
                <span className="text-sm text-muted-foreground">entity</span>
                <span className="text-sm font-mono">{ackDialog.alert.entityId || '-'}</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40">
                <span className="text-sm text-muted-foreground">rule</span>
                <span className="text-sm">{ackDialog.alert.ruleByRuleId?.name || '-'}</span>
              </div>
            </div>
          )}
          <DialogFooter>
            <Button variant="ghost" onClick={() => setAckDialog(null)} disabled={ackLoading}>
              cancel
            </Button>
            <Button onClick={handleAcknowledge} disabled={ackLoading}>
              {ackLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
              acknowledge
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
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
if (typeof document !== 'undefined' && !document.getElementById('alert-sheet-keyframes')) {
  const style = document.createElement('style')
  style.id = 'alert-sheet-keyframes'
  style.textContent = sheetStyles
  document.head.appendChild(style)
}
