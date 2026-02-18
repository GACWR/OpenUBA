import React, { useState } from 'react';
import { useQuery, gql } from '@apollo/client';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Play, Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { IngestionRunDetails } from './ingestion-run-details';
import { useAuth } from '@/lib/auth-provider';

function timeAgo(date: string | Date): string {
    const seconds = Math.floor((new Date().getTime() - new Date(date).getTime()) / 1000);
    let interval = seconds / 31536000;
    if (interval > 1) return Math.floor(interval) + "y ago";
    interval = seconds / 2592000;
    if (interval > 1) return Math.floor(interval) + "mo ago";
    interval = seconds / 86400;
    if (interval > 1) return Math.floor(interval) + "d ago";
    interval = seconds / 3600;
    if (interval > 1) return Math.floor(interval) + "h ago";
    interval = seconds / 60;
    if (interval > 1) return Math.floor(interval) + "m ago";
    return Math.floor(seconds) + "s ago";
}

const GET_INGESTION_RUNS = gql`
  query GetDataIngestionRuns {
    allDataIngestionRuns(orderBy: CREATED_AT_DESC, first: 10) {
      nodes {
        id
        datasetName
        status
        startedAt
        completedAt
        details
        errorMessage
        createdAt
      }
    }
  }
`;

export function IngestionManager() {
    const { data, loading, error, refetch } = useQuery(GET_INGESTION_RUNS, {
        pollInterval: 5000,
    });
    const [isIngesting, setIsIngesting] = useState(false);
    const [ingestError, setIngestError] = useState<string | null>(null);
    const [expandedRun, setExpandedRun] = useState<string | null>(null);
    const { authFetch } = useAuth();

    const handleIngest = async () => {
        setIsIngesting(true);
        setIngestError(null);
        try {
            const response = await authFetch('/api/v1/data/ingest', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ingest_all: true,
                    ingest_to_spark: true,
                    ingest_to_es: true
                })
            });

            if (!response.ok) {
                throw new Error('Failed to start ingestion');
            }

            setTimeout(() => refetch(), 1000);
        } catch (err: any) {
            setIngestError(err.message);
        } finally {
            setIsIngesting(false);
        }
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'completed':
                return <Badge variant="success" size="sm" className="flex items-center gap-1"><CheckCircle className="h-3 w-3" /> Done</Badge>;
            case 'failed':
                return <Badge variant="error" size="sm" className="flex items-center gap-1"><XCircle className="h-3 w-3" /> Failed</Badge>;
            case 'running':
                return <Badge variant="info" size="sm" className="flex items-center gap-1"><Loader2 className="h-3 w-3 animate-spin" /> Running</Badge>;
            default:
                return <Badge variant="secondary" size="sm">{status}</Badge>;
        }
    };

    const toggleExpand = (runId: string) => {
        setExpandedRun(prev => prev === runId ? null : runId);
    };

    return (
        <Card className="h-full flex flex-col">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div>
                    <CardTitle className="text-lg font-semibold">Ingestion Jobs</CardTitle>
                    <p className="text-xs text-muted-foreground mt-1">Recent ingestion runs</p>
                </div>
                <Button
                    onClick={handleIngest}
                    disabled={isIngesting}
                    size="sm"
                >
                    {isIngesting ? (
                        <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Starting...
                        </>
                    ) : (
                        <>
                            <Play className="mr-2 h-4 w-4" />
                            Run Ingestion
                        </>
                    )}
                </Button>
            </CardHeader>
            <CardContent className="flex-1 overflow-hidden flex flex-col">
                {ingestError && (
                    <div className="bg-red-500/15 text-red-500 p-2 rounded-md text-xs mb-3">
                        <span className="font-semibold">Error: </span>{ingestError}
                    </div>
                )}

                <ScrollArea className="flex-1 pr-2">
                    <div className="space-y-2">
                        {loading && !data ? (
                            <div className="flex justify-center p-4">
                                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                            </div>
                        ) : error ? (
                            <div className="text-red-500 text-sm">Failed to load history</div>
                        ) : (
                            data?.allDataIngestionRuns?.nodes.map((run: any) => (
                                <div
                                    key={run.id}
                                    className="flex flex-col rounded-lg border bg-card/50 overflow-hidden"
                                >
                                    {/* Run header - always visible, clickable to expand */}
                                    <div
                                        className="flex items-center justify-between px-3 py-2 cursor-pointer hover:bg-muted/30 transition-colors"
                                        onClick={() => toggleExpand(run.id)}
                                    >
                                        <div className="flex items-center gap-2 min-w-0">
                                            <span className="font-medium text-sm truncate">{run.datasetName}</span>
                                            {getStatusBadge(run.status)}
                                        </div>
                                        <div className="flex items-center text-xs text-muted-foreground shrink-0 ml-2">
                                            <Clock className="mr-1 h-3 w-3" />
                                            {timeAgo(run.createdAt)}
                                        </div>
                                    </div>

                                    {/* Error message - always shown if present */}
                                    {run.errorMessage && (
                                        <div className="text-xs text-red-400 bg-red-950/20 px-3 py-1.5 border-t">
                                            {run.errorMessage}
                                        </div>
                                    )}

                                    {/* Expanded details - parsed per engine */}
                                    {expandedRun === run.id && run.details && (
                                        <div className="px-3 py-2 border-t bg-muted/20">
                                            <IngestionRunDetails details={run.details} />
                                        </div>
                                    )}

                                    {/* Compact summary when collapsed */}
                                    {expandedRun !== run.id && run.details && run.status === 'completed' && (
                                        <CompactSummary details={run.details} />
                                    )}
                                </div>
                            ))
                        )}

                        {data?.allDataIngestionRuns?.nodes.length === 0 && (
                            <div className="text-center text-muted-foreground py-8 text-sm">
                                No ingestion runs found.
                            </div>
                        )}
                    </div>
                </ScrollArea>
            </CardContent>
        </Card>
    );
}

/** Compact one-line summary of a completed run */
function CompactSummary({ details }: { details: string | any }) {
    try {
        const parsed = typeof details === 'string' ? JSON.parse(details) : details;
        const sparkEntries = parsed.spark ? Object.entries(parsed.spark) : [];
        const esEntries = parsed.elasticsearch ? Object.entries(parsed.elasticsearch) : [];
        const sparkRows = sparkEntries.reduce((sum: number, [, v]: any) => sum + (v.row_count || 0), 0);
        const esDocs = esEntries.reduce((sum: number, [, v]: any) => sum + (v.document_count || 0), 0);
        const esFailed = esEntries.reduce((sum: number, [, v]: any) => sum + (v.failed || 0), 0);

        return (
            <div className="flex items-center gap-3 px-3 py-1.5 border-t text-[11px] text-muted-foreground">
                {sparkEntries.length > 0 && (
                    <span>{sparkEntries.length} tables / {sparkRows.toLocaleString()} rows</span>
                )}
                {esEntries.length > 0 && (
                    <>
                        <span className="text-border">|</span>
                        <span>
                            {esEntries.length} indices / {esDocs.toLocaleString()} docs
                            {esFailed > 0 && <span className="text-red-400 ml-1">({esFailed} failed)</span>}
                        </span>
                    </>
                )}
            </div>
        );
    } catch {
        return null;
    }
}
