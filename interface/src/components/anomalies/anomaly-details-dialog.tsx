'use client'

import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'

interface Anomaly {
    id: string
    entityId: string
    entityType: string
    riskScore: number
    anomalyType?: string
    timestamp: string
    acknowledged: boolean
    modelId?: string
    details?: any
}

interface AnomalyDetailsDialogProps {
    anomaly: Anomaly | null
    open: boolean
    onOpenChange: (open: boolean) => void
}

export function AnomalyDetailsDialog({ anomaly, open, onOpenChange }: AnomalyDetailsDialogProps) {
    if (!anomaly) return null

    const getScoreColor = (score: number) => {
        if (score >= 80) return 'text-red-500'
        if (score >= 50) return 'text-orange-500'
        return 'text-green-500'
    }

    const formatDetails = (details: any) => {
        if (!details) return 'No additional details available.'
        try {
            if (typeof details === 'string') {
                const parsed = JSON.parse(details)
                return JSON.stringify(parsed, null, 2)
            }
            return JSON.stringify(details, null, 2)
        } catch {
            return String(details)
        }
    }

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-2xl max-h-[85vh] flex flex-col">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-3 text-xl">
                        Anomaly Details
                        <Badge variant={anomaly.riskScore >= 80 ? 'destructive' : 'default'} className="ml-2">
                            Score: {anomaly.riskScore}
                        </Badge>
                    </DialogTitle>
                </DialogHeader>

                <ScrollArea className="flex-1 pr-4">
                    <div className="space-y-6 py-4">
                        {/* key information */}
                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-1">
                                <p className="text-sm font-medium text-muted-foreground">Entity ID</p>
                                <p className="text-lg font-mono">{anomaly.entityId}</p>
                            </div>
                            <div className="space-y-1">
                                <p className="text-sm font-medium text-muted-foreground">Entity Type</p>
                                <p className="capitalize">{anomaly.entityType}</p>
                            </div>
                            <div className="space-y-1">
                                <p className="text-sm font-medium text-muted-foreground">Anomaly Type</p>
                                <Badge variant="secondary">{anomaly.anomalyType || 'Unknown'}</Badge>
                            </div>
                            <div className="space-y-1">
                                <p className="text-sm font-medium text-muted-foreground">Timestamp</p>
                                <p>{new Date(anomaly.timestamp).toLocaleString()}</p>
                            </div>
                        </div>

                        {/* details section */}
                        <div className="space-y-2">
                            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">Detailed Analysis</h3>
                            <Card className="bg-slate-950 border-slate-800">
                                <CardContent className="p-4">
                                    <pre className="text-xs font-mono text-slate-300 overflow-auto whitespace-pre-wrap">
                                        {formatDetails(anomaly.details)}
                                    </pre>
                                </CardContent>
                            </Card>
                        </div>
                    </div>
                </ScrollArea>
            </DialogContent>
        </Dialog>
    )
}
