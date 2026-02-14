'use client'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { AlertTriangle, Shield, User, Clock, Cpu, FileText } from 'lucide-react'

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

interface AnomalyDetailDrawerProps {
  anomaly: Anomaly
  onAcknowledge?: (id: string) => void
  onCreateCase?: (id: string) => void
}

function getRiskLevel(score: number) {
  if (score >= 80) return { label: 'critical', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/20', description: 'immediate investigation recommended' }
  if (score >= 60) return { label: 'high', color: 'text-orange-400', bg: 'bg-orange-500/10', border: 'border-orange-500/20', description: 'elevated risk — review soon' }
  if (score >= 40) return { label: 'medium', color: 'text-yellow-400', bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', description: 'moderate deviation from baseline' }
  return { label: 'low', color: 'text-green-400', bg: 'bg-green-500/10', border: 'border-green-500/20', description: 'minor deviation detected' }
}

function parseDetails(details: any): Array<{ label: string; value: string }> {
  if (!details) return []
  let obj = details
  if (typeof obj === 'string') {
    try { obj = JSON.parse(obj) } catch { return [{ label: 'raw', value: String(obj) }] }
  }
  if (typeof obj !== 'object' || Array.isArray(obj)) {
    return [{ label: 'value', value: JSON.stringify(obj) }]
  }

  const entries: Array<{ label: string; value: string }> = []
  for (const [key, val] of Object.entries(obj)) {
    const label = key.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').toLowerCase().trim()
    let value: string
    if (typeof val === 'number') {
      value = Number.isInteger(val) ? String(val) : val.toFixed(4)
    } else if (typeof val === 'boolean') {
      value = val ? 'yes' : 'no'
    } else if (val === null || val === undefined) {
      value = '—'
    } else if (typeof val === 'object') {
      value = JSON.stringify(val)
    } else {
      value = String(val)
    }
    entries.push({ label, value })
  }
  return entries
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40">
      <span className="text-sm text-muted-foreground">{label}</span>
      {children}
    </div>
  )
}

export function AnomalyDetailDrawer({ anomaly, onAcknowledge, onCreateCase }: AnomalyDetailDrawerProps) {
  const risk = getRiskLevel(anomaly.riskScore)
  const detailEntries = parseDetails(anomaly.details)

  return (
    <div className="space-y-5">
      {/* risk assessment */}
      <div className={`rounded-xl border ${risk.border} ${risk.bg} p-4`}>
        <div className="flex items-center gap-2 mb-3">
          <AlertTriangle className={`h-4 w-4 ${risk.color}`} />
          <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">risk assessment</span>
        </div>
        <div className="flex items-baseline gap-3">
          <span className={`text-4xl font-bold tabular-nums ${risk.color}`}>{anomaly.riskScore}</span>
          <div>
            <Badge variant={anomaly.riskScore >= 80 ? 'error' : anomaly.riskScore >= 50 ? 'warning' : 'success'} size="sm">
              {risk.label}
            </Badge>
            <p className="text-xs text-muted-foreground mt-1">{risk.description}</p>
          </div>
        </div>
      </div>

      {/* entity info */}
      <div>
        <div className="flex items-center gap-2 mb-2.5">
          <User className="h-4 w-4 text-muted-foreground" />
          <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">entity information</span>
        </div>
        <div className="space-y-1.5">
          <Row label="entity id">
            <span className="text-sm font-mono font-medium">{anomaly.entityId}</span>
          </Row>
          <Row label="entity type">
            <Badge variant="info" size="sm">{anomaly.entityType || 'unknown'}</Badge>
          </Row>
          <Row label="anomaly type">
            <Badge variant="secondary" size="sm">{anomaly.anomalyType || 'unknown'}</Badge>
          </Row>
        </div>
      </div>

      {/* timestamps */}
      <div>
        <div className="flex items-center gap-2 mb-2.5">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">timeline</span>
        </div>
        <div className="space-y-1.5">
          <Row label="detected">
            <span className="text-sm">{new Date(anomaly.timestamp).toLocaleString()}</span>
          </Row>
          {anomaly.createdAt && (
            <Row label="recorded">
              <span className="text-sm">{new Date(anomaly.createdAt).toLocaleString()}</span>
            </Row>
          )}
          {anomaly.acknowledged && anomaly.acknowledgedAt && (
            <Row label="acknowledged">
              <span className="text-sm">{new Date(anomaly.acknowledgedAt).toLocaleString()}</span>
            </Row>
          )}
          {anomaly.acknowledgedBy && (
            <Row label="acknowledged by">
              <span className="text-sm font-medium">{anomaly.acknowledgedBy}</span>
            </Row>
          )}
        </div>
      </div>

      {/* model attribution */}
      {anomaly.modelId && (
        <div>
          <div className="flex items-center gap-2 mb-2.5">
            <Cpu className="h-4 w-4 text-muted-foreground" />
            <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">model attribution</span>
          </div>
          <div className="space-y-1.5">
            {anomaly.modelByModelId?.name && (
              <Row label="model">
                <span className="text-sm font-medium">{anomaly.modelByModelId.name}</span>
              </Row>
            )}
            {anomaly.modelByModelId?.version && (
              <Row label="version">
                <span className="text-sm font-mono">{anomaly.modelByModelId.version}</span>
              </Row>
            )}
            <Row label="model id">
              <span className="text-sm font-mono">{anomaly.modelId.slice(0, 8)}...</span>
            </Row>
          </div>
        </div>
      )}

      {/* detection details */}
      {detailEntries.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2.5">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">detection details</span>
          </div>
          <div className="space-y-1.5">
            {detailEntries.map((entry, i) => (
              <Row key={i} label={entry.label}>
                <span className="text-sm font-mono text-right max-w-[200px] truncate" title={entry.value}>
                  {entry.value}
                </span>
              </Row>
            ))}
          </div>
        </div>
      )}

      {/* status */}
      <div>
        <div className="flex items-center gap-2 mb-2.5">
          <Shield className="h-4 w-4 text-muted-foreground" />
          <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">status</span>
        </div>
        <Row label="status">
          <Badge variant={anomaly.acknowledged ? 'success' : 'warning'} size="sm">
            {anomaly.acknowledged ? 'acknowledged' : 'new'}
          </Badge>
        </Row>
      </div>

      {/* actions */}
      <div className="flex gap-2 pt-2">
        {!anomaly.acknowledged && onAcknowledge && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => onAcknowledge(anomaly.id)}
            className="flex-1 hover:bg-orange-500/10 hover:border-orange-500/50"
          >
            acknowledge
          </Button>
        )}
        {onCreateCase && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => onCreateCase(anomaly.id)}
            className="flex-1 hover:bg-purple-500/10 hover:border-purple-500/50"
          >
            open case
          </Button>
        )}
      </div>
    </div>
  )
}
