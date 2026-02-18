'use client'

import { useState, useMemo, useCallback } from 'react'
import { useQuery, useMutation } from '@apollo/client'
import { GET_RULES, GET_ALERTS } from '@/lib/graphql/queries'
import { CREATE_RULE, UPDATE_RULE } from '@/lib/graphql/mutations'
import { RulesFilters } from '@/components/rules/rules-filters'
import { RulesTable } from '@/components/rules/rules-table'
import { DonutChart } from '@/components/charts/donut-chart'
import { BarChartComponent } from '@/components/charts/bar-chart'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useToast } from '@/components/global/toast-provider'
import dynamic from 'next/dynamic'
import {
  X, Shield, CheckCircle, Zap, Bell, Plus
} from 'lucide-react'

const FlowCanvas = dynamic(() => import('@/components/rules/flow-canvas').then(m => m.FlowCanvas), {
  ssr: false,
  loading: () => null,
})

/* -- types ------------------------------------------------- */

interface RuleItem {
  id: string
  name: string
  description?: string
  ruleType: string
  condition: string
  features?: string
  score: number
  enabled: boolean
  severity?: string
  flowGraph?: any
  lastTriggeredAt?: string
  createdAt?: string
  updatedAt?: string
}

interface AlertItem {
  id: string
  ruleId: string
  severity: string
  message: string
  entityId?: string
  entityType?: string
  acknowledged: boolean
  createdAt: string
  ruleByRuleId?: { name: string }
}

/* -- page -------------------------------------------------- */

export function RulesPageShell() {
  const { data: rulesData, loading: rulesLoading, error: rulesError, refetch: refetchRules } = useQuery(GET_RULES, { pollInterval: 10000 })
  const { data: alertsData, loading: alertsLoading } = useQuery(GET_ALERTS, { pollInterval: 10000 })
  const [createRule] = useMutation(CREATE_RULE)
  const [updateRule] = useMutation(UPDATE_RULE)
  const { addToast } = useToast()

  const rules: RuleItem[] = rulesData?.allRules?.nodes || []
  const alerts: AlertItem[] = alertsData?.allAlerts?.nodes || []

  /* filter state */
  const [searchText, setSearchText] = useState('')
  const [typeFilter, setTypeFilter] = useState('all')
  const [severityFilter, setSeverityFilter] = useState('all')
  const [enabledFilter, setEnabledFilter] = useState('all')

  /* panel state */
  const [selectedRule, setSelectedRule] = useState<RuleItem | null>(null)
  const [panelClosing, setPanelClosing] = useState(false)

  /* canvas state */
  const [canvasOpen, setCanvasOpen] = useState(false)
  const [editingRule, setEditingRule] = useState<RuleItem | null>(null)

  /* filtered rules */
  const filteredRules = useMemo(() => {
    return rules.filter((r) => {
      if (searchText && !r.name.toLowerCase().includes(searchText.toLowerCase())) return false
      if (typeFilter !== 'all' && r.ruleType !== typeFilter) return false
      if (severityFilter !== 'all' && r.severity !== severityFilter) return false
      if (enabledFilter === 'active' && !r.enabled) return false
      if (enabledFilter === 'disabled' && r.enabled) return false
      return true
    })
  }, [rules, searchText, typeFilter, severityFilter, enabledFilter])

  /* -- summary metrics -------------------------------------- */
  const totalRules = rules.length
  const activeRules = rules.filter((r) => r.enabled).length
  const now = new Date()
  const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const triggeredToday = rules.filter((r) => r.lastTriggeredAt && new Date(r.lastTriggeredAt).getTime() >= todayStart).length
  const totalAlerts = alerts.length

  /* donut: rules by type */
  const typeDistData = useMemo(() => {
    const counts: Record<string, number> = {}
    rules.forEach((r) => { counts[r.ruleType] = (counts[r.ruleType] || 0) + 1 })
    return Object.entries(counts).map(([name, value]) => ({ name, value }))
  }, [rules])

  /* bar: alerts by severity */
  const alertSevData = useMemo(() => {
    const buckets = { critical: 0, high: 0, medium: 0, low: 0 }
    alerts.forEach((a) => {
      const sev = a.severity as keyof typeof buckets
      if (sev in buckets) buckets[sev]++
    })
    return Object.entries(buckets).map(([severity, count]) => ({ severity, count }))
  }, [alerts])

  const hasPanels = !!selectedRule
  const closePanel = () => setPanelClosing(true)
  const onPanelAnimationEnd = () => {
    if (panelClosing) { setSelectedRule(null); setPanelClosing(false) }
  }

  const handleCreateRule = () => {
    setEditingRule(null)
    setCanvasOpen(true)
  }

  const handleEditRule = (id: string) => {
    const r = rules.find((x) => x.id === id)
    if (r) {
      /* parse flowGraph if it's a JSON string from PostGraphile */
      let parsedFlowGraph = r.flowGraph
      if (typeof parsedFlowGraph === 'string') {
        try { parsedFlowGraph = JSON.parse(parsedFlowGraph) } catch { /* leave as-is */ }
      }
      setEditingRule({ ...r, flowGraph: parsedFlowGraph })
      setCanvasOpen(true)
    }
  }

  const handleSaveRule = useCallback(async (name: string, severity: string, flowGraph: any, condition: string, editId?: string) => {
    const serializedGraph = typeof flowGraph === 'string' ? flowGraph : JSON.stringify(flowGraph)
    try {
      if (editId) {
        await updateRule({
          variables: {
            id: editId,
            patch: {
              name,
              severity,
              flowGraph: serializedGraph,
              condition,
              ruleType: 'flow',
            }
          }
        })
      } else {
        await createRule({
          variables: {
            input: {
              rule: {
                name,
                severity,
                flowGraph: serializedGraph,
                condition,
                ruleType: 'flow',
                score: 0,
                enabled: true,
              }
            }
          }
        })
      }
      setCanvasOpen(false)
      setEditingRule(null)
      refetchRules()
      addToast(editId ? 'rule updated' : 'rule created', {
        type: 'success',
        description: `"${name}" saved successfully`,
      })
    } catch (err: any) {
      const reason = err?.graphQLErrors?.[0]?.message || err?.message || 'unknown error'
      addToast('failed to save rule', {
        type: 'error',
        description: reason,
      })
    }
  }, [createRule, updateRule, refetchRules, addToast])

  const loading = rulesLoading && !rulesData

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Rules</h1>
        <Button size="sm" className="gap-1.5" onClick={handleCreateRule}>
          <Plus className="h-4 w-4" />
          create rule
        </Button>
      </div>

      {/* -- KPI cards ---------------------------------------- */}
      {loading ? (
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
          <KpiCard icon={<Shield className="h-4 w-4" />} label="total rules" value={totalRules} color="text-foreground" />
          <KpiCard icon={<CheckCircle className="h-4 w-4" />} label="active" value={activeRules} color="text-green-400" />
          <KpiCard icon={<Zap className="h-4 w-4" />} label="triggered today" value={triggeredToday} color="text-orange-400" />
          <KpiCard icon={<Bell className="h-4 w-4" />} label="total alerts" value={totalAlerts} color="text-red-400" />
        </div>
      )}

      {/* -- charts ------------------------------------------- */}
      {(totalRules > 0 || totalAlerts > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">rules by type</CardTitle>
            </CardHeader>
            <CardContent>
              <DonutChart
                data={typeDistData.length > 0 ? typeDistData : [{ name: 'none', value: 0 }]}
                colors={['#f97316', '#8b5cf6', '#06b6d4', '#10b981']}
                height={220}
                centerLabel={`${totalRules}`}
              />
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold">alerts by severity</CardTitle>
            </CardHeader>
            <CardContent>
              <BarChartComponent
                data={alertSevData}
                xKey="severity"
                yKeys={[{ key: 'count', name: 'alerts', color: '#ef4444' }]}
                height={220}
              />
            </CardContent>
          </Card>
        </div>
      )}

      {/* -- filters ------------------------------------------ */}
      <RulesFilters
        searchText={searchText}
        onSearchChange={setSearchText}
        typeFilter={typeFilter}
        onTypeFilterChange={setTypeFilter}
        severityFilter={severityFilter}
        onSeverityFilterChange={setSeverityFilter}
        enabledFilter={enabledFilter}
        onEnabledFilterChange={setEnabledFilter}
      />

      {/* -- table --------------------------------------------- */}
      {loading ? (
        <Card><CardContent className="pt-4 space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4">
              <Skeleton className="h-4 w-28" />
              <Skeleton className="h-5 w-14 rounded-full" />
              <Skeleton className="h-5 w-14 rounded-full" />
              <Skeleton className="h-4 w-12" />
              <Skeleton className="h-5 w-14 rounded-full" />
              <Skeleton className="h-4 w-16" />
            </div>
          ))}
        </CardContent></Card>
      ) : rulesError ? (
        <div className="text-red-500">error loading rules: {rulesError.message}</div>
      ) : (
        <RulesTable
          rules={filteredRules}
          onViewDetails={(id) => {
            const r = rules.find((x) => x.id === id)
            if (r) setSelectedRule(r)
          }}
          onEdit={handleEditRule}
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
                <Shield className="h-4 w-4 text-muted-foreground" />
                <h2 className="text-sm font-semibold">rule details</h2>
              </div>
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={closePanel}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
              <div>
                <h3 className="text-lg font-bold">{selectedRule!.name}</h3>
                {selectedRule!.description && (
                  <p className="text-sm text-muted-foreground mt-0.5">{selectedRule!.description}</p>
                )}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <DetailField label="type">
                  <Badge variant="outline" size="sm">{selectedRule!.ruleType}</Badge>
                </DetailField>
                <DetailField label="severity">
                  <Badge
                    variant={
                      selectedRule!.severity === 'critical' ? 'error' :
                      selectedRule!.severity === 'high' ? 'warning' :
                      selectedRule!.severity === 'medium' ? 'info' : 'success'
                    }
                    size="sm"
                  >
                    {selectedRule!.severity || 'medium'}
                  </Badge>
                </DetailField>
                <DetailField label="score" value={String(selectedRule!.score)} />
                <DetailField label="status">
                  <Badge variant={selectedRule!.enabled ? 'success' : 'secondary'} size="sm">
                    {selectedRule!.enabled ? 'active' : 'disabled'}
                  </Badge>
                </DetailField>
                <DetailField
                  label="last triggered"
                  value={selectedRule!.lastTriggeredAt ? new Date(selectedRule!.lastTriggeredAt).toLocaleString() : 'never'}
                />
                <DetailField
                  label="created"
                  value={selectedRule!.createdAt ? new Date(selectedRule!.createdAt).toLocaleDateString() : '-'}
                />
              </div>
              <div>
                <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">condition</span>
                <pre className="text-xs mt-1 p-2 rounded bg-muted/40 overflow-x-auto whitespace-pre-wrap">
                  {selectedRule!.condition}
                </pre>
              </div>
              {selectedRule!.flowGraph && (
                <div>
                  <span className="text-[10px] font-medium uppercase tracking-wide text-muted-foreground">flow graph</span>
                  <pre className="text-xs mt-1 p-2 rounded bg-muted/40 overflow-x-auto">
                    {JSON.stringify(
                      typeof selectedRule!.flowGraph === 'string'
                        ? (() => { try { return JSON.parse(selectedRule!.flowGraph) } catch { return selectedRule!.flowGraph } })()
                        : selectedRule!.flowGraph,
                      null, 2
                    )}
                  </pre>
                </div>
              )}
              {selectedRule!.ruleType === 'flow' && (
                <Button
                  size="sm"
                  className="w-full gap-1.5"
                  onClick={() => {
                    closePanel()
                    setTimeout(() => handleEditRule(selectedRule!.id), 250)
                  }}
                >
                  edit in canvas
                </Button>
              )}
            </div>
          </div>
        </>
      )}

      {/* -- flow canvas overlay -------------------------------- */}
      {canvasOpen && (
        <FlowCanvas
          open={canvasOpen}
          onClose={() => { setCanvasOpen(false); setEditingRule(null) }}
          onSave={handleSaveRule}
          initialRule={editingRule || undefined}
        />
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
if (typeof document !== 'undefined' && !document.getElementById('rule-sheet-keyframes')) {
  const style = document.createElement('style')
  style.id = 'rule-sheet-keyframes'
  style.textContent = sheetStyles
  document.head.appendChild(style)
}
