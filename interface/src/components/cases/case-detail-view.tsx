'use client'

import { useState } from 'react'
import { useMutation } from '@apollo/client'
import { UPDATE_CASE } from '@/lib/graphql/mutations'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useToast } from '@/components/global/toast-provider'
import { Briefcase, Clock, User, AlertTriangle, FileText } from 'lucide-react'

interface LinkedAnomaly {
  id: string
  entityId: string
  entityType: string
  riskScore: number
  anomalyType?: string
  timestamp: string
  acknowledged: boolean
}

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
      anomalyByAnomalyId: LinkedAnomaly
    }>
  }
}

interface CaseDetailViewProps {
  caseItem: CaseItem
  onStatusChanged?: () => void
}

function getSeverityVariant(severity: string): 'error' | 'warning' | 'info' | 'success' {
  if (severity === 'critical') return 'error'
  if (severity === 'high') return 'warning'
  if (severity === 'medium') return 'info'
  return 'success'
}

function getStatusVariant(status: string): 'info' | 'warning' | 'success' | 'secondary' {
  if (status === 'resolved' || status === 'closed') return 'success'
  if (status === 'investigating') return 'warning'
  if (status === 'open') return 'info'
  return 'secondary'
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40">
      <span className="text-sm text-muted-foreground">{label}</span>
      {children}
    </div>
  )
}

export function CaseDetailView({ caseItem, onStatusChanged }: CaseDetailViewProps) {
  const { addToast } = useToast()
  const [updateCase] = useMutation(UPDATE_CASE)
  const [updatingStatus, setUpdatingStatus] = useState(false)

  const linkedAnomalies = caseItem.caseAnomaliesByCaseId?.nodes
    ?.map((n) => n.anomalyByAnomalyId)
    .filter(Boolean) || []

  const handleStatusChange = async (newStatus: string) => {
    setUpdatingStatus(true)
    try {
      await updateCase({
        variables: {
          id: caseItem.id,
          input: { status: newStatus }
        }
      })
      addToast('Case Updated', {
        type: 'success',
        description: `status changed to ${newStatus}`,
      })
      onStatusChanged?.()
    } catch (err: any) {
      addToast('Update Failed', {
        type: 'error',
        description: err.message,
      })
    } finally {
      setUpdatingStatus(false)
    }
  }

  return (
    <div className="space-y-5">
      {/* case header */}
      <div>
        <h3 className="text-lg font-semibold mb-2">{caseItem.title}</h3>
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant={getSeverityVariant(caseItem.severity)} size="sm">
            {caseItem.severity}
          </Badge>
          <Badge variant={getStatusVariant(caseItem.status)} size="sm">
            {caseItem.status}
          </Badge>
        </div>
      </div>

      {/* status control */}
      <div>
        <div className="flex items-center gap-2 mb-2.5">
          <Briefcase className="h-4 w-4 text-muted-foreground" />
          <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">case management</span>
        </div>
        <div className="space-y-1.5">
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40">
            <span className="text-sm text-muted-foreground">status</span>
            <Select value={caseItem.status} onValueChange={handleStatusChange}>
              <SelectTrigger className="w-[140px] h-7 text-xs" disabled={updatingStatus}>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="open">open</SelectItem>
                <SelectItem value="investigating">investigating</SelectItem>
                <SelectItem value="resolved">resolved</SelectItem>
                <SelectItem value="closed">closed</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Row label="severity">
            <Badge variant={getSeverityVariant(caseItem.severity)} size="sm">{caseItem.severity}</Badge>
          </Row>
          {caseItem.assignedTo && (
            <Row label="assigned to">
              <span className="text-sm font-medium">{caseItem.assignedTo}</span>
            </Row>
          )}
        </div>
      </div>

      {/* description & notes */}
      {(caseItem.description || caseItem.analystNotes) && (
        <div>
          <div className="flex items-center gap-2 mb-2.5">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">notes</span>
          </div>
          <div className="space-y-2">
            {caseItem.description && (
              <div className="p-3 rounded-lg bg-muted/40 text-sm">
                {caseItem.description}
              </div>
            )}
            {caseItem.analystNotes && (
              <div className="p-3 rounded-lg bg-muted/40 text-sm">
                <span className="text-muted-foreground text-xs block mb-1">analyst notes</span>
                {caseItem.analystNotes}
              </div>
            )}
          </div>
        </div>
      )}

      {/* linked anomalies */}
      {linkedAnomalies.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2.5">
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
              linked anomalies ({linkedAnomalies.length})
            </span>
          </div>
          <div className="space-y-1.5">
            {linkedAnomalies.map((a) => (
              <div key={a.id} className="flex items-center justify-between p-2.5 rounded-lg bg-muted/40">
                <div className="min-w-0">
                  <span className="text-sm font-mono font-medium truncate block">{a.entityId}</span>
                  <span className="text-xs text-muted-foreground">{a.anomalyType || 'unknown'}</span>
                </div>
                <Badge variant={a.riskScore >= 80 ? 'error' : a.riskScore >= 50 ? 'warning' : 'success'} size="sm">
                  {a.riskScore}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* timeline */}
      <div>
        <div className="flex items-center gap-2 mb-2.5">
          <Clock className="h-4 w-4 text-muted-foreground" />
          <span className="text-[11px] font-medium uppercase tracking-wide text-muted-foreground">timeline</span>
        </div>
        <div className="space-y-1.5">
          <Row label="created">
            <span className="text-sm">{new Date(caseItem.createdAt).toLocaleString()}</span>
          </Row>
          {caseItem.updatedAt && (
            <Row label="updated">
              <span className="text-sm">{new Date(caseItem.updatedAt).toLocaleString()}</span>
            </Row>
          )}
          {caseItem.resolvedAt && (
            <Row label="resolved">
              <span className="text-sm">{new Date(caseItem.resolvedAt).toLocaleString()}</span>
            </Row>
          )}
        </div>
      </div>
    </div>
  )
}
