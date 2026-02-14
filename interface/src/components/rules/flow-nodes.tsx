'use client'

import { memo } from 'react'
import { Handle, Position, type NodeProps } from '@xyflow/react'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  Boxes, AlertTriangle, Briefcase, GitCompareArrows,
  CircleDot, CircleOff, Ban, Bell
} from 'lucide-react'

/* -- shared node wrapper ----------------------------------- */

function NodeShell({ accent, icon, label, children, hasInput = true, hasOutput = true, selected = false }: {
  accent: string
  icon: React.ReactNode
  label: string
  children: React.ReactNode
  hasInput?: boolean
  hasOutput?: boolean
  selected?: boolean
}) {
  return (
    <div
      className={`min-w-[200px] rounded-lg border bg-card shadow-lg transition-all ${
        selected ? 'ring-2 shadow-xl' : ''
      }`}
      style={{
        borderTopColor: accent,
        borderTopWidth: 3,
        ...(selected ? { ringColor: accent, boxShadow: `0 0 0 2px ${accent}40, 0 8px 25px -5px ${accent}30` } : {}),
      }}
    >
      {hasInput && (
        <Handle type="target" position={Position.Left} className="!w-3 !h-3 !border-2" style={{ background: accent }} />
      )}
      <div className="flex items-center gap-1.5 px-3 py-2 border-b">
        <span style={{ color: accent }}>{icon}</span>
        <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</span>
      </div>
      <div className="px-3 py-2 space-y-2">
        {children}
      </div>
      {hasOutput && (
        <Handle type="source" position={Position.Right} className="!w-3 !h-3 !border-2" style={{ background: accent }} />
      )}
    </div>
  )
}

/* -- 1. Model Output Node ---------------------------------- */

export const ModelOutputNode = memo((props: NodeProps) => {
  const { data, id, selected } = props as any
  const d = data as any
  return (
    <NodeShell accent="#9333ea" icon={<Boxes className="h-3.5 w-3.5" />} label="model output" hasInput={false} selected={!!selected}>
      <Select value={d.modelId || ''} onValueChange={(v) => d.onChange?.(id, 'modelId', v)}>
        <SelectTrigger className="h-7 text-xs">
          <SelectValue placeholder="select model" />
        </SelectTrigger>
        <SelectContent>
          {(d.models || []).map((m: any) => (
            <SelectItem key={m.id} value={m.id}>{m.name}</SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Select value={d.output || 'risk_score'} onValueChange={(v) => d.onChange?.(id, 'output', v)}>
        <SelectTrigger className="h-7 text-xs">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="risk_score">risk score (number)</SelectItem>
          <SelectItem value="has_anomaly">has anomaly (boolean)</SelectItem>
        </SelectContent>
      </Select>
    </NodeShell>
  )
})
ModelOutputNode.displayName = 'ModelOutputNode'

/* -- 2. Anomaly Condition Node ----------------------------- */

export const AnomalyConditionNode = memo((props: NodeProps) => {
  const { data, id, selected } = props as any
  const d = data as any
  return (
    <NodeShell accent="#f97316" icon={<AlertTriangle className="h-3.5 w-3.5" />} label="anomaly condition" hasInput={false} selected={!!selected}>
      <Input
        className="h-7 text-xs"
        type="number"
        placeholder="min risk score"
        value={d.minRiskScore ?? ''}
        onChange={(e) => d.onChange?.(id, 'minRiskScore', e.target.value)}
      />
      <Select value={d.entityType || 'any'} onValueChange={(v) => d.onChange?.(id, 'entityType', v)}>
        <SelectTrigger className="h-7 text-xs">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="any">any entity type</SelectItem>
          <SelectItem value="user">user</SelectItem>
          <SelectItem value="device">device</SelectItem>
          <SelectItem value="ip">ip</SelectItem>
        </SelectContent>
      </Select>
      <Input
        className="h-7 text-xs"
        placeholder="anomaly type filter"
        value={d.anomalyType ?? ''}
        onChange={(e) => d.onChange?.(id, 'anomalyType', e.target.value)}
      />
    </NodeShell>
  )
})
AnomalyConditionNode.displayName = 'AnomalyConditionNode'

/* -- 3. Case Condition Node -------------------------------- */

export const CaseConditionNode = memo((props: NodeProps) => {
  const { data, id, selected } = props as any
  const d = data as any
  return (
    <NodeShell accent="#3b82f6" icon={<Briefcase className="h-3.5 w-3.5" />} label="case condition" hasInput={false} selected={!!selected}>
      <Select value={d.caseEvent || 'created'} onValueChange={(v) => d.onChange?.(id, 'caseEvent', v)}>
        <SelectTrigger className="h-7 text-xs">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="created">case created</SelectItem>
          <SelectItem value="severity_match">case severity matches</SelectItem>
        </SelectContent>
      </Select>
      {d.caseEvent === 'severity_match' && (
        <Select value={d.caseSeverity || 'high'} onValueChange={(v) => d.onChange?.(id, 'caseSeverity', v)}>
          <SelectTrigger className="h-7 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="critical">critical</SelectItem>
            <SelectItem value="high">high</SelectItem>
            <SelectItem value="medium">medium</SelectItem>
            <SelectItem value="low">low</SelectItem>
          </SelectContent>
        </Select>
      )}
    </NodeShell>
  )
})
CaseConditionNode.displayName = 'CaseConditionNode'

/* -- 4. Comparison Node ------------------------------------ */

export const ComparisonNode = memo((props: NodeProps) => {
  const { data, id, selected } = props as any
  const d = data as any
  return (
    <NodeShell accent="#06b6d4" icon={<GitCompareArrows className="h-3.5 w-3.5" />} label="comparison" selected={!!selected}>
      <Select value={d.operator || '>'} onValueChange={(v) => d.onChange?.(id, 'operator', v)}>
        <SelectTrigger className="h-7 text-xs">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value=">">{'>'} greater than</SelectItem>
          <SelectItem value="<">{'<'} less than</SelectItem>
          <SelectItem value=">=">{'>='} greater or equal</SelectItem>
          <SelectItem value="<=">{'<='} less or equal</SelectItem>
          <SelectItem value="==">{'=='} equal</SelectItem>
          <SelectItem value="!=">{'!='} not equal</SelectItem>
        </SelectContent>
      </Select>
      <Input
        className="h-7 text-xs"
        type="number"
        placeholder="threshold value"
        value={d.value ?? ''}
        onChange={(e) => d.onChange?.(id, 'value', e.target.value)}
      />
    </NodeShell>
  )
})
ComparisonNode.displayName = 'ComparisonNode'

/* -- 5. AND Gate Node -------------------------------------- */

export const AndGateNode = memo((props: NodeProps) => {
  const { selected } = props as any
  return (
    <NodeShell accent="#6366f1" icon={<CircleDot className="h-3.5 w-3.5" />} label="AND gate" selected={!!selected}>
      <div className="text-xs text-muted-foreground text-center py-1">all inputs must be true</div>
    </NodeShell>
  )
})
AndGateNode.displayName = 'AndGateNode'

/* -- 6. OR Gate Node --------------------------------------- */

export const OrGateNode = memo((props: NodeProps) => {
  const { selected } = props as any
  return (
    <NodeShell accent="#6366f1" icon={<CircleOff className="h-3.5 w-3.5" />} label="OR gate" selected={!!selected}>
      <div className="text-xs text-muted-foreground text-center py-1">any input must be true</div>
    </NodeShell>
  )
})
OrGateNode.displayName = 'OrGateNode'

/* -- 7. NOT Gate Node -------------------------------------- */

export const NotGateNode = memo((props: NodeProps) => {
  const { selected } = props as any
  return (
    <NodeShell accent="#6366f1" icon={<Ban className="h-3.5 w-3.5" />} label="NOT gate" selected={!!selected}>
      <div className="text-xs text-muted-foreground text-center py-1">inverts boolean input</div>
    </NodeShell>
  )
})
NotGateNode.displayName = 'NotGateNode'

/* -- 8. Alert Output Node ---------------------------------- */

export const AlertOutputNode = memo((props: NodeProps) => {
  const { data, id, selected } = props as any
  const d = data as any
  return (
    <NodeShell accent="#ef4444" icon={<Bell className="h-3.5 w-3.5" />} label="alert output" hasOutput={false} selected={!!selected}>
      <Select value={d.severity || 'high'} onValueChange={(v) => d.onChange?.(id, 'severity', v)}>
        <SelectTrigger className="h-7 text-xs">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="critical">critical</SelectItem>
          <SelectItem value="high">high</SelectItem>
          <SelectItem value="medium">medium</SelectItem>
          <SelectItem value="low">low</SelectItem>
        </SelectContent>
      </Select>
      <Input
        className="h-7 text-xs"
        placeholder="alert message"
        value={d.message ?? ''}
        onChange={(e) => d.onChange?.(id, 'message', e.target.value)}
      />
      <Select value={d.action || 'fire_alert'} onValueChange={(v) => d.onChange?.(id, 'action', v)}>
        <SelectTrigger className="h-7 text-xs">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="fire_alert">fire alert only</SelectItem>
          <SelectItem value="open_case">open case</SelectItem>
          <SelectItem value="fire_alert_and_open_case">fire alert + open case</SelectItem>
          <SelectItem value="notify">send notification</SelectItem>
        </SelectContent>
      </Select>
    </NodeShell>
  )
})
AlertOutputNode.displayName = 'AlertOutputNode'

/* -- node type registry ------------------------------------ */

export const nodeTypes = {
  model: ModelOutputNode,
  anomaly: AnomalyConditionNode,
  case: CaseConditionNode,
  comparison: ComparisonNode,
  and: AndGateNode,
  or: OrGateNode,
  not: NotGateNode,
  alert: AlertOutputNode,
}

/* -- palette items ----------------------------------------- */

export const paletteItems = [
  { category: 'data sources', items: [
    { type: 'model', label: 'model output', icon: Boxes, accent: '#9333ea' },
    { type: 'anomaly', label: 'anomaly condition', icon: AlertTriangle, accent: '#f97316' },
    { type: 'case', label: 'case condition', icon: Briefcase, accent: '#3b82f6' },
  ]},
  { category: 'logic', items: [
    { type: 'comparison', label: 'comparison', icon: GitCompareArrows, accent: '#06b6d4' },
    { type: 'and', label: 'AND gate', icon: CircleDot, accent: '#6366f1' },
    { type: 'or', label: 'OR gate', icon: CircleOff, accent: '#6366f1' },
    { type: 'not', label: 'NOT gate', icon: Ban, accent: '#6366f1' },
  ]},
  { category: 'output', items: [
    { type: 'alert', label: 'alert output', icon: Bell, accent: '#ef4444' },
  ]},
]
