'use client'

import React, { useState, useEffect, useCallback } from 'react'
import { useQuery, gql } from '@apollo/client'
import { DataSourcesTable, type DataSource } from '@/components/data/data-sources-table'
import { IngestionManager } from '@/components/data/ingestion-manager'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import {
    X, Database, Activity, Zap, Server,
    RefreshCw, Loader2
} from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useAuth } from '@/lib/auth-provider'

/* ── types ─────────────────────────────────────────── */

interface DetailPanel {
    id: string
    type: 'pipeline' | 'source'
    title: string
    data: any
}

/* ── gql: latest run for ingestion badge ───────────── */

const GET_LATEST_RUN = gql`
  query GetLatestRun {
    allDataIngestionRuns(orderBy: CREATED_AT_DESC, first: 1) {
      nodes { id status completedAt createdAt }
    }
  }
`

/* ── page ──────────────────────────────────────────── */

export default function DataPage() {
    /* metrics state */
    const [sources, setSources] = useState<DataSource[]>([])
    const [sparkStatus, setSparkStatus] = useState<'connected' | 'error' | 'loading'>('loading')
    const [esStatus, setEsStatus] = useState<'connected' | 'error' | 'loading'>('loading')
    const [sparkMeta, setSparkMeta] = useState<any>(null)
    const [esMeta, setEsMeta] = useState<any>(null)
    const [metricsLoading, setMetricsLoading] = useState(true)
    const [history, setHistory] = useState<any[]>([])
    const { authFetch } = useAuth()

    /* detail panels (stack) */
    const [panels, setPanels] = useState<DetailPanel[]>([])
    const [panelsClosing, setPanelsClosing] = useState(false)

    /* ingestion badge data */
    const { data: runData } = useQuery(GET_LATEST_RUN, { pollInterval: 10000 })
    const latestRun = runData?.allDataIngestionRuns?.nodes?.[0]
    const ingestionStatus: string = latestRun?.status || 'idle'

    /* ── fetch metrics ─────────────────────────────── */
    const fetchMetrics = useCallback(async () => {
        setMetricsLoading(true)
        try {
            const [metricsRes, historyRes] = await Promise.all([
                authFetch('/api/v1/data/metrics'),
                authFetch('/api/v1/data/history')
            ])

            const next: DataSource[] = []

            if (metricsRes.ok) {
                const data = await metricsRes.json()

                /* spark tables */
                if (data.spark?.tables) {
                    setSparkStatus('connected')
                    setSparkMeta(data.spark)
                    for (const [name, info] of Object.entries(data.spark.tables)) {
                        next.push({
                            name,
                            type: 'spark',
                            rowCount: (info as any).row_count,
                            size: (info as any).partition_count != null
                                ? `${(info as any).partition_count} partitions`
                                : undefined,
                            lastUpdated: new Date().toISOString()
                        })
                    }
                } else {
                    setSparkStatus('error')
                }

                /* elasticsearch indices */
                if (data.elasticsearch?.indices) {
                    setEsStatus('connected')
                    setEsMeta(data.elasticsearch)
                    for (const [name, info] of Object.entries(data.elasticsearch.indices)) {
                        const i = info as any
                        next.push({
                            name,
                            type: 'elasticsearch',
                            rowCount: i.document_count ?? i.primaries?.docs?.count ?? 0,
                            size: i.size_in_bytes
                                ? `${Math.round(i.size_in_bytes / 1024)} KB`
                                : i.total?.store?.size_in_bytes
                                    ? `${(i.total.store.size_in_bytes / 1024 / 1024).toFixed(2)} MB`
                                    : '0 KB',
                            lastUpdated: new Date().toISOString()
                        })
                    }
                } else {
                    setEsStatus('error')
                }
            } else {
                setSparkStatus('error')
                setEsStatus('error')
            }

            setSources(next)

            if (historyRes.ok) {
                const hd = await historyRes.json()
                setHistory(hd.history || [])
            }
        } catch {
            setSparkStatus('error')
            setEsStatus('error')
        } finally {
            setMetricsLoading(false)
        }
    }, [authFetch])

    useEffect(() => {
        fetchMetrics()
        const iv = setInterval(fetchMetrics, 30000)
        return () => clearInterval(iv)
    }, [fetchMetrics])

    /* ── panel helpers ─────────────────────────────── */
    const openPanel = (p: DetailPanel) =>
        setPanels(prev => [...prev.filter(x => x.id !== p.id), p])

    const closePanel = (id: string) =>
        setPanels(prev => prev.filter(x => x.id !== id))

    /* ── summary numbers ──────────────────────────── */
    const sparkSources = sources.filter(s => s.type === 'spark')
    const esSources = sources.filter(s => s.type === 'elasticsearch')
    const sparkRows = sparkSources.reduce((a, s) => a + (s.rowCount || 0), 0)
    const esRows = esSources.reduce((a, s) => a + (s.rowCount || 0), 0)

    /* ── badge click handlers ─────────────────────── */
    const handleSparkClick = () => openPanel({
        id: 'spark-health', type: 'pipeline', title: 'Spark Status',
        data: { engine: 'spark', status: sparkStatus, meta: sparkMeta, sources: sparkSources }
    })

    const handleEsClick = () => openPanel({
        id: 'es-health', type: 'pipeline', title: 'Elasticsearch Status',
        data: { engine: 'elasticsearch', status: esStatus, meta: esMeta, sources: esSources }
    })

    const handleIngestionClick = () => openPanel({
        id: 'ingestion-health', type: 'pipeline', title: 'Ingestion Pipeline',
        data: { status: ingestionStatus, lastRun: latestRun }
    })

    const handleSourceClick = (source: DataSource) => openPanel({
        id: `source-${source.type}-${source.name}`, type: 'source', title: source.name, data: source
    })

    const isFirstLoad = metricsLoading && sources.length === 0 && history.length === 0

    const hasPanels = panels.length > 0
    const closeAllPanels = () => setPanelsClosing(true)
    const onPanelsAnimationEnd = () => {
        if (panelsClosing) { setPanels([]); setPanelsClosing(false) }
    }

    return (
        <div className="space-y-4">

            {/* ── header row: title + badges + refresh ── */}
            <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-3 flex-wrap">
                    <h1 className="text-2xl font-bold tracking-tight">Data Management</h1>

                    <div className="flex items-center gap-2">
                        {isFirstLoad ? (
                            <>
                                <Skeleton className="h-6 w-20 rounded-full" />
                                <Skeleton className="h-6 w-28 rounded-full" />
                                <Skeleton className="h-6 w-22 rounded-full" />
                            </>
                        ) : (
                        <>
                        <PipelineBadge
                            icon={<Zap className="h-3 w-3" />}
                            label="Spark"
                            variant={sparkStatus === 'connected' ? 'success' : sparkStatus === 'error' ? 'error' : 'secondary'}
                            tooltip={sparkStatus === 'connected' ? `${sparkSources.length} tables, ${sparkRows.toLocaleString()} rows` : sparkStatus === 'error' ? 'Connection error' : 'Connecting...'}
                            onClick={handleSparkClick}
                        />
                        <PipelineBadge
                            icon={<Database className="h-3 w-3" />}
                            label="Elasticsearch"
                            variant={esStatus === 'connected' ? 'success' : esStatus === 'error' ? 'error' : 'secondary'}
                            tooltip={esStatus === 'connected' ? `${esSources.length} indices, ${esRows.toLocaleString()} docs` : esStatus === 'error' ? 'Connection error' : 'Connecting...'}
                            onClick={handleEsClick}
                        />
                        <PipelineBadge
                            icon={<Activity className="h-3 w-3" />}
                            label="Ingestion"
                            variant={ingestionStatus === 'completed' ? 'success' : ingestionStatus === 'running' ? 'info' : ingestionStatus === 'failed' ? 'error' : 'secondary'}
                            tooltip={ingestionStatus === 'running' ? 'Ingestion running...' : latestRun ? `Last run: ${ingestionStatus}` : 'No runs yet'}
                            onClick={handleIngestionClick}
                            spinning={ingestionStatus === 'running'}
                        />
                        </>
                        )}
                    </div>
                </div>

                <Button variant="ghost" size="icon" onClick={fetchMetrics} disabled={metricsLoading} className="h-8 w-8">
                    <RefreshCw className={`h-4 w-4 ${metricsLoading ? 'animate-spin' : ''}`} />
                </Button>
            </div>

            {/* ── body: always full-width, panels overlay from right ── */}
            <div className="space-y-4">
                {/* skeleton while first load */}
                {isFirstLoad && (
                    <>
                        <Card>
                            <CardHeader className="pb-2">
                                <Skeleton className="h-4 w-32" />
                                <Skeleton className="h-3 w-48 mt-1" />
                            </CardHeader>
                            <CardContent>
                                <Skeleton className="h-[160px] w-full" />
                            </CardContent>
                        </Card>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <Card className="h-full">
                                <CardHeader className="pb-2"><Skeleton className="h-4 w-28" /></CardHeader>
                                <CardContent className="space-y-3">
                                    {Array.from({ length: 5 }).map((_, i) => (
                                        <Skeleton key={i} className="h-8 w-full" />
                                    ))}
                                </CardContent>
                            </Card>
                            <Card className="min-h-[420px]">
                                <CardHeader className="pb-2"><Skeleton className="h-4 w-36" /></CardHeader>
                                <CardContent className="space-y-3">
                                    {Array.from({ length: 4 }).map((_, i) => (
                                        <Skeleton key={i} className="h-10 w-full" />
                                    ))}
                                </CardContent>
                            </Card>
                        </div>
                    </>
                )}

                {/* data volume history chart — top summary */}
                {!isFirstLoad && history.length > 0 && (
                    <Card>
                        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                            <div>
                                <CardTitle className="text-sm font-semibold">Data Volume</CardTitle>
                                <p className="text-xs text-muted-foreground">Ingestion volume over the last 7 days</p>
                            </div>
                            <div className="flex items-center gap-4 text-xs">
                                <div className="flex items-center gap-1.5">
                                    <span className="inline-block w-3 h-[3px] rounded-full bg-[#f59e0b]" />
                                    <span className="text-muted-foreground">Spark</span>
                                </div>
                                <div className="flex items-center gap-1.5">
                                    <span className="inline-block w-3 h-[3px] rounded-full bg-[#3b82f6]" />
                                    <span className="text-muted-foreground">Elasticsearch</span>
                                </div>
                            </div>
                        </CardHeader>
                        <CardContent>
                            <div className="h-[160px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={history}>
                                        <defs>
                                            <linearGradient id="colorSpark" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.25} />
                                                <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                                            </linearGradient>
                                            <linearGradient id="colorEs" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                                                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <XAxis dataKey="name" stroke="#888888" fontSize={11} tickLine={false} axisLine={false} />
                                        <YAxis stroke="#888888" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}MB`} />
                                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#1f2937', border: 'none', borderRadius: '8px' }}
                                            itemStyle={{ color: '#fff' }}
                                            labelStyle={{ color: '#9ca3af', marginBottom: 4 }}
                                            formatter={(value: number, name: string) => [
                                                `${value} MB`,
                                                name === 'spark' ? 'Spark' : name === 'elasticsearch' ? 'Elasticsearch' : name
                                            ]}
                                        />
                                        <Area type="monotone" dataKey="spark" stroke="#f59e0b" strokeWidth={2} fillOpacity={1} fill="url(#colorSpark)" />
                                        <Area type="monotone" dataKey="elasticsearch" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorEs)" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* data sources + ingestion jobs side by side */}
                {!isFirstLoad && <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <DataSourcesTable
                        sources={sources}
                        loading={metricsLoading}
                        onRefresh={fetchMetrics}
                        onSourceClick={handleSourceClick}
                    />
                    <div className="min-h-[420px]">
                        <IngestionManager />
                    </div>
                </div>}
            </div>

            {/* ── right-side sheet stack ── */}
            {hasPanels && (
                <>
                    {/* backdrop */}
                    <div
                        className="fixed inset-0 bg-black/30 z-40"
                        style={{ animation: panelsClosing ? 'fadeOut 150ms ease-in forwards' : 'fadeIn 150ms ease-out' }}
                        onClick={closeAllPanels}
                    />

                    {/* stacked full-height sheets sliding in from right */}
                    {panels.map((p, i) => {
                        const depth = panels.length - 1 - i
                        const isTop = depth === 0
                        /* each deeper sheet peeks out 16px to the left */
                        const rightOffset = depth * 16
                        return (
                            <div
                                key={p.id}
                                className="fixed top-0 right-0 h-full w-[400px] z-50 border-l bg-background shadow-2xl flex flex-col"
                                style={{
                                    transform: panelsClosing ? undefined : `translateX(-${rightOffset}px)`,
                                    zIndex: 50 + i,
                                    opacity: isTop && !panelsClosing ? 1 : panelsClosing ? undefined : 0.45,
                                    transition: panelsClosing ? undefined : 'transform 200ms ease-out, opacity 200ms ease-out',
                                    animation: panelsClosing ? 'slideOutRight 200ms ease-in forwards' : isTop ? 'slideInRight 200ms ease-out' : undefined,
                                }}
                                onAnimationEnd={isTop ? onPanelsAnimationEnd : undefined}
                            >
                                {/* sheet header */}
                                <div className="flex items-center justify-between px-5 py-4 border-b shrink-0">
                                    <div className="flex items-center gap-2 min-w-0">
                                        <SheetIcon panel={p} />
                                        <h2 className="text-sm font-semibold truncate">{p.title}</h2>
                                    </div>
                                    <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={() => closePanel(p.id)}>
                                        <X className="h-4 w-4" />
                                    </Button>
                                </div>

                                {/* sheet body — scrollable */}
                                <div className="flex-1 overflow-y-auto px-5 py-4">
                                    <SheetBody panel={p} />
                                </div>
                            </div>
                        )
                    })}
                </>
            )}
        </div>
    )
}

/* ── pipeline badge with tooltip ──────────────────── */

function PipelineBadge({ icon, label, variant, tooltip, onClick, spinning }: {
    icon: React.ReactNode
    label: string
    variant: 'success' | 'error' | 'secondary' | 'info' | 'warning'
    tooltip: string
    onClick: () => void
    spinning?: boolean
}) {
    return (
        <div className="group/badge relative">
            <Badge
                variant={variant}
                className="cursor-pointer flex items-center gap-1.5 hover:ring-2 hover:ring-ring/20 transition-all select-none"
                onClick={onClick}
            >
                {icon}
                {label}
                {spinning
                    ? <Loader2 className="h-3 w-3 animate-spin" />
                    : <span className="inline-block w-1.5 h-1.5 rounded-full bg-current opacity-60" />
                }
            </Badge>

            {/* tooltip */}
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-1.5 bg-popover border rounded-md shadow-md text-xs text-popover-foreground whitespace-nowrap opacity-0 group-hover/badge:opacity-100 pointer-events-none transition-opacity duration-150 z-50">
                {tooltip}
                <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px border-4 border-transparent border-t-popover" />
            </div>
        </div>
    )
}

/* ── sheet icon (for the header) ───────────────────── */

function SheetIcon({ panel }: { panel: DetailPanel }) {
    if (panel.type === 'source') return <Server className="h-4 w-4 text-muted-foreground" />
    const d = panel.data
    if (d.engine === 'spark') return <Zap className="h-4 w-4 text-yellow-500" />
    if (d.engine === 'elasticsearch') return <Database className="h-4 w-4 text-blue-500" />
    return <Activity className="h-4 w-4 text-muted-foreground" />
}

/* ── sheet body content ───────────────────────────── */

function SheetBody({ panel }: { panel: DetailPanel }) {
    if (panel.type === 'source') return <SourceBody data={panel.data} />
    if (panel.data.engine) return <EngineBody data={panel.data} />
    return <IngestionBody data={panel.data} />
}

/* engine detail (spark / elasticsearch) */
function EngineBody({ data }: { data: any }) {
    const ok = data.status === 'connected'
    return (
        <div className="space-y-4">
            <Row label="Status">
                <Badge variant={ok ? 'success' : 'error'} size="sm">{ok ? 'Connected' : 'Error'}</Badge>
            </Row>

            {data.sources?.length > 0 && (
                <div className="space-y-2">
                    <div className="text-[11px] text-muted-foreground font-medium uppercase tracking-wide">
                        {data.engine === 'spark' ? 'Tables' : 'Indices'}
                    </div>
                    <div className="space-y-1.5">
                        {data.sources.map((s: DataSource) => (
                            <div key={s.name} className="flex items-center justify-between p-2.5 rounded-lg bg-muted/30 text-sm">
                                <span className="font-medium truncate mr-3">{s.name}</span>
                                <div className="flex items-center gap-2 text-muted-foreground shrink-0 text-xs">
                                    <span className="tabular-nums font-medium text-foreground">{s.rowCount?.toLocaleString() || 0}</span>
                                    {s.size && <span className="opacity-60">{s.size}</span>}
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="border-t pt-3 mt-3">
                        <Row label="Total">
                            <span className="font-semibold text-sm tabular-nums">
                                {data.sources.reduce((a: number, s: DataSource) => a + (s.rowCount || 0), 0).toLocaleString()} rows
                            </span>
                        </Row>
                    </div>
                </div>
            )}
        </div>
    )
}

/* ingestion pipeline detail */
function IngestionBody({ data }: { data: any }) {
    return (
        <div className="space-y-3">
            <Row label="Status">
                <Badge
                    variant={data.status === 'completed' ? 'success' : data.status === 'running' ? 'info' : data.status === 'failed' ? 'error' : 'secondary'}
                    size="sm"
                >
                    {data.status}
                </Badge>
            </Row>
            {data.lastRun?.completedAt && (
                <Row label="Completed">
                    <span className="text-sm">{new Date(data.lastRun.completedAt).toLocaleString()}</span>
                </Row>
            )}
            {data.lastRun?.createdAt && (
                <Row label="Started">
                    <span className="text-sm">{new Date(data.lastRun.createdAt).toLocaleString()}</span>
                </Row>
            )}
        </div>
    )
}

/* data source detail */
function SourceBody({ data }: { data: DataSource }) {
    return (
        <div className="space-y-3">
            <Row label="Engine">
                <Badge variant={data.type === 'spark' ? 'warning' : 'info'} size="sm">{data.type}</Badge>
            </Row>
            <Row label="Rows / Docs">
                <span className="text-sm font-semibold tabular-nums">{data.rowCount?.toLocaleString() || '-'}</span>
            </Row>
            {data.size && (
                <Row label="Size">
                    <span className="text-sm">{data.size}</span>
                </Row>
            )}
            {data.lastUpdated && (
                <Row label="Last Updated">
                    <span className="text-sm">{new Date(data.lastUpdated).toLocaleString()}</span>
                </Row>
            )}
        </div>
    )
}

/* ── tiny row helper ──────────────────────────────── */

function Row({ label, children }: { label: string; children: React.ReactNode }) {
    return (
        <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40">
            <span className="text-sm text-muted-foreground">{label}</span>
            {children}
        </div>
    )
}

/* ── inline keyframes for the sheet ───────────────── */
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
/* inject once */
if (typeof document !== 'undefined' && !document.getElementById('sheet-keyframes')) {
    const style = document.createElement('style')
    style.id = 'sheet-keyframes'
    style.textContent = sheetStyles
    document.head.appendChild(style)
}
