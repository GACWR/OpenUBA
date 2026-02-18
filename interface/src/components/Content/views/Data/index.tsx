import React, { useState, useEffect, useCallback } from 'react';
import { useQuery, gql } from '@apollo/client';
import { IngestionManager } from '@/components/data/ingestion-manager';
import { DataSourcesTable, type DataSource } from '@/components/data/data-sources-table';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    X, Database, Activity, Zap, Server,
    RefreshCw, Loader2
} from 'lucide-react';
import { useAuth } from '@/lib/auth-provider';

/* ── types ─────────────────────────────────────────── */

interface DetailPanel {
    id: string;
    type: 'pipeline' | 'source';
    title: string;
    data: any;
}

/* ── gql: latest run for ingestion badge ───────────── */

const GET_LATEST_RUN = gql`
  query GetLatestRun {
    allDataIngestionRuns(orderBy: CREATED_AT_DESC, first: 1) {
      nodes { id status completedAt createdAt }
    }
  }
`;

/* ── page ──────────────────────────────────────────── */

const Data = () => {
    /* metrics state */
    const [sources, setSources] = useState<DataSource[]>([]);
    const [sparkStatus, setSparkStatus] = useState<'connected' | 'error' | 'loading'>('loading');
    const [esStatus, setEsStatus] = useState<'connected' | 'error' | 'loading'>('loading');
    const [sparkMeta, setSparkMeta] = useState<any>(null);
    const [esMeta, setEsMeta] = useState<any>(null);
    const [metricsLoading, setMetricsLoading] = useState(true);
    const { authFetch } = useAuth();

    /* detail panels (stack) */
    const [panels, setPanels] = useState<DetailPanel[]>([]);

    /* ingestion badge data */
    const { data: runData } = useQuery(GET_LATEST_RUN, { pollInterval: 10000 });
    const latestRun = runData?.allDataIngestionRuns?.nodes?.[0];
    const ingestionStatus: string = latestRun?.status || 'idle';

    /* ── fetch metrics ─────────────────────────────── */
    const fetchMetrics = useCallback(async () => {
        setMetricsLoading(true);
        try {
            const [sparkRes, esRes] = await Promise.all([
                authFetch('/api/v1/data/metrics/spark'),
                authFetch('/api/v1/data/metrics/elasticsearch')
            ]);

            const next: DataSource[] = [];

            if (sparkRes.ok) {
                const d = await sparkRes.json();
                setSparkMeta(d);
                setSparkStatus('connected');
                if (d.tables) {
                    Object.entries(d.tables).forEach(([name, info]: [string, any]) => {
                        next.push({
                            name,
                            type: 'spark',
                            rowCount: info.count,
                            size: info.partition_count != null ? `${info.partition_count} partitions` : undefined,
                            lastUpdated: new Date().toISOString()
                        });
                    });
                }
            } else {
                setSparkStatus('error');
            }

            if (esRes.ok) {
                const d = await esRes.json();
                setEsMeta(d);
                setEsStatus('connected');
                if (d.indices) {
                    Object.entries(d.indices).forEach(([name, info]: [string, any]) => {
                        let count = 0;
                        let sizeBytes = 0;
                        if (info.primaries?.docs) count = info.primaries.docs.count;
                        else if (info.total?.docs) count = info.total.docs.count;
                        if (info.total?.store) sizeBytes = info.total.store.size_in_bytes;
                        next.push({
                            name,
                            type: 'elasticsearch',
                            rowCount: count,
                            size: sizeBytes ? `${(sizeBytes / 1024 / 1024).toFixed(2)} MB` : undefined,
                            lastUpdated: new Date().toISOString()
                        });
                    });
                }
            } else {
                setEsStatus('error');
            }

            setSources(next);
        } catch {
            setSparkStatus('error');
            setEsStatus('error');
        } finally {
            setMetricsLoading(false);
        }
    }, [authFetch]);

    useEffect(() => {
        fetchMetrics();
        const iv = setInterval(fetchMetrics, 30000);
        return () => clearInterval(iv);
    }, [fetchMetrics]);

    /* ── panel helpers ─────────────────────────────── */
    const openPanel = (p: DetailPanel) =>
        setPanels(prev => [...prev.filter(x => x.id !== p.id), p]);

    const closePanel = (id: string) =>
        setPanels(prev => prev.filter(x => x.id !== id));

    /* ── summary numbers ──────────────────────────── */
    const sparkSources = sources.filter(s => s.type === 'spark');
    const esSources = sources.filter(s => s.type === 'elasticsearch');
    const sparkRows = sparkSources.reduce((a, s) => a + (s.rowCount || 0), 0);
    const esRows = esSources.reduce((a, s) => a + (s.rowCount || 0), 0);

    /* ── badge click handlers ─────────────────────── */
    const handleSparkClick = () => openPanel({
        id: 'spark-health', type: 'pipeline', title: 'Spark Status',
        data: { engine: 'spark', status: sparkStatus, meta: sparkMeta, sources: sparkSources }
    });

    const handleEsClick = () => openPanel({
        id: 'es-health', type: 'pipeline', title: 'Elasticsearch Status',
        data: { engine: 'elasticsearch', status: esStatus, meta: esMeta, sources: esSources }
    });

    const handleIngestionClick = () => openPanel({
        id: 'ingestion-health', type: 'pipeline', title: 'Ingestion Pipeline',
        data: { status: ingestionStatus, lastRun: latestRun }
    });

    const handleSourceClick = (source: DataSource) => openPanel({
        id: `source-${source.type}-${source.name}`, type: 'source', title: source.name, data: source
    });

    const hasPanels = panels.length > 0;

    return (
        <div className="container mx-auto p-4 space-y-4">

            {/* ── header row ───────────────────────── */}
            <div className="flex items-center justify-between flex-wrap gap-2">
                <div className="flex items-center gap-3 flex-wrap">
                    <h1 className="text-2xl font-bold">Data Management</h1>

                    <div className="flex items-center gap-2">
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
                    </div>
                </div>

                <Button variant="ghost" size="icon" onClick={fetchMetrics} disabled={metricsLoading} className="h-8 w-8">
                    <RefreshCw className={`h-4 w-4 ${metricsLoading ? 'animate-spin' : ''}`} />
                </Button>
            </div>

            {/* ── body ─────────────────────────────── */}
            <div className="flex gap-4">
                {/* main content: data sources + ingestion jobs side by side */}
                <div className={`flex-1 grid grid-cols-1 ${hasPanels ? 'xl:grid-cols-2' : 'md:grid-cols-2'} gap-4 min-w-0`}>
                    <DataSourcesTable
                        sources={sources}
                        loading={metricsLoading}
                        onRefresh={fetchMetrics}
                        onSourceClick={handleSourceClick}
                    />
                    <div className="min-h-[500px]">
                        <IngestionManager />
                    </div>
                </div>

                {/* stackable detail panels */}
                {hasPanels && (
                    <div className="w-[360px] flex-shrink-0 space-y-3">
                        {panels.map(p => (
                            <DetailCard key={p.id} panel={p} onClose={() => closePanel(p.id)} />
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

/* ── pipeline badge with tooltip ──────────────────── */

function PipelineBadge({ icon, label, variant, tooltip, onClick, spinning }: {
    icon: React.ReactNode;
    label: string;
    variant: 'success' | 'error' | 'secondary' | 'info' | 'warning';
    tooltip: string;
    onClick: () => void;
    spinning?: boolean;
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
    );
}

/* ── detail card dispatcher ───────────────────────── */

function DetailCard({ panel, onClose }: { panel: DetailPanel; onClose: () => void }) {
    return panel.type === 'pipeline'
        ? <PipelineDetail panel={panel} onClose={onClose} />
        : <SourceDetail panel={panel} onClose={onClose} />;
}

/* ── pipeline detail panel ────────────────────────── */

function PipelineDetail({ panel, onClose }: { panel: DetailPanel; onClose: () => void }) {
    const { data } = panel;

    /* engine-specific (spark or elasticsearch) */
    if (data.engine) {
        const ok = data.status === 'connected';
        const icon = data.engine === 'spark'
            ? <Zap className="h-4 w-4 text-yellow-500" />
            : <Database className="h-4 w-4 text-blue-500" />;

        return (
            <Card className="animate-fade-in">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <div className="flex items-center gap-2">
                        {icon}
                        <CardTitle className="text-sm font-semibold">{panel.title}</CardTitle>
                    </div>
                    <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClose}>
                        <X className="h-3.5 w-3.5" />
                    </Button>
                </CardHeader>
                <CardContent className="space-y-2 pt-0">
                    <Row label="Status">
                        <Badge variant={ok ? 'success' : 'error'} size="sm">{ok ? 'Connected' : 'Error'}</Badge>
                    </Row>

                    {data.sources?.length > 0 && (
                        <>
                            <div className="text-[11px] text-muted-foreground font-medium uppercase tracking-wide pt-1">
                                {data.engine === 'spark' ? 'Tables' : 'Indices'}
                            </div>
                            <div className="space-y-1">
                                {data.sources.map((s: DataSource) => (
                                    <div key={s.name} className="flex items-center justify-between p-2 rounded bg-muted/30 text-xs">
                                        <span className="font-medium truncate mr-2">{s.name}</span>
                                        <div className="flex items-center gap-1.5 text-muted-foreground shrink-0">
                                            <span className="tabular-nums">{s.rowCount?.toLocaleString() || 0}</span>
                                            {s.size && <span className="opacity-60">({s.size})</span>}
                                        </div>
                                    </div>
                                ))}
                            </div>
                            <Row label="Total">
                                <span className="font-medium text-xs tabular-nums">
                                    {data.sources.reduce((a: number, s: DataSource) => a + (s.rowCount || 0), 0).toLocaleString()} rows
                                </span>
                            </Row>
                        </>
                    )}
                </CardContent>
            </Card>
        );
    }

    /* ingestion pipeline */
    return (
        <Card className="animate-fade-in">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    <CardTitle className="text-sm font-semibold">{panel.title}</CardTitle>
                </div>
                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClose}>
                    <X className="h-3.5 w-3.5" />
                </Button>
            </CardHeader>
            <CardContent className="space-y-2 pt-0">
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
                        <span className="text-xs">{new Date(data.lastRun.completedAt).toLocaleString()}</span>
                    </Row>
                )}
                {data.lastRun?.createdAt && (
                    <Row label="Started">
                        <span className="text-xs">{new Date(data.lastRun.createdAt).toLocaleString()}</span>
                    </Row>
                )}
            </CardContent>
        </Card>
    );
}

/* ── source detail panel ──────────────────────────── */

function SourceDetail({ panel, onClose }: { panel: DetailPanel; onClose: () => void }) {
    const s: DataSource = panel.data;
    return (
        <Card className="animate-fade-in">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="flex items-center gap-2 min-w-0">
                    <Server className="h-4 w-4 shrink-0" />
                    <CardTitle className="text-sm font-semibold truncate">{panel.title}</CardTitle>
                </div>
                <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClose}>
                    <X className="h-3.5 w-3.5" />
                </Button>
            </CardHeader>
            <CardContent className="space-y-2 pt-0">
                <Row label="Engine">
                    <Badge variant={s.type === 'spark' ? 'warning' : 'info'} size="sm">{s.type}</Badge>
                </Row>
                <Row label="Rows / Docs">
                    <span className="text-xs font-medium tabular-nums">{s.rowCount?.toLocaleString() || '-'}</span>
                </Row>
                {s.size && (
                    <Row label="Size">
                        <span className="text-xs">{s.size}</span>
                    </Row>
                )}
                {s.lastUpdated && (
                    <Row label="Last Updated">
                        <span className="text-xs">{new Date(s.lastUpdated).toLocaleString()}</span>
                    </Row>
                )}
            </CardContent>
        </Card>
    );
}

/* ── tiny row helper ──────────────────────────────── */

function Row({ label, children }: { label: string; children: React.ReactNode }) {
    return (
        <div className="flex items-center justify-between p-2 rounded bg-muted/40">
            <span className="text-xs text-muted-foreground">{label}</span>
            {children}
        </div>
    );
}

export default Data;
