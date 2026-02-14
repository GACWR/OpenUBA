'use client'

import { useState, useCallback, useRef, useMemo, useEffect, DragEvent, MouseEvent } from 'react'
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  type Connection,
  type Edge,
  type Node,
  BackgroundVariant,
  type ReactFlowInstance,
} from '@xyflow/react'
import { useQuery } from '@apollo/client'
import { GET_MODELS } from '@/lib/graphql/queries'
import { nodeTypes, paletteItems } from '@/components/rules/flow-nodes'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  X, Save, FlaskConical, ChevronRight, Trash2, Copy, MousePointer2,
  Maximize, Eraser, CheckCircle, AlertTriangle, XCircle,
  Boxes, Briefcase, GitCompareArrows, CircleDot, CircleOff, Ban, Bell
} from 'lucide-react'

/* -- types ------------------------------------------------- */

interface FlowCanvasProps {
  open: boolean
  onClose: () => void
  onSave: (name: string, severity: string, flowGraph: any, condition: string, editId?: string) => void
  initialRule?: {
    id: string
    name: string
    severity?: string
    flowGraph?: any
  }
}

interface ContextMenuState {
  x: number
  y: number
  type: 'canvas' | 'node' | 'edge'
  targetId?: string
}

interface TestResult {
  type: 'error' | 'warning' | 'success'
  text: string
}

/* -- helpers ------------------------------------------------ */

let nodeIdCounter = 0
function getNextNodeId() {
  nodeIdCounter++
  return `n${nodeIdCounter}`
}

function serializeGraph(nodes: Node[], edges: Edge[], viewport: { x: number; y: number; zoom: number }) {
  const sortedNodes = [...nodes]
    .sort((a, b) => a.id.localeCompare(b.id))
    .map((n) => ({
      id: n.id,
      type: n.type,
      position: { x: Math.round(n.position.x), y: Math.round(n.position.y) },
      data: (() => {
        const { onChange, models, ...rest } = (n.data || {}) as any
        return rest
      })(),
    }))

  const sortedEdges = [...edges]
    .sort((a, b) => a.id.localeCompare(b.id))
    .map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      sourceHandle: e.sourceHandle || null,
      targetHandle: e.targetHandle || null,
    }))

  return {
    nodes: sortedNodes,
    edges: sortedEdges,
    viewport: {
      x: Math.round(viewport.x),
      y: Math.round(viewport.y),
      zoom: Math.round(viewport.zoom * 100) / 100,
    },
  }
}

function generateConditionSummary(nodes: Node[], edges: Edge[]): string {
  const nodeMap = new Map(nodes.map((n) => [n.id, n]))
  const parts: string[] = []

  const alertNodes = nodes.filter((n) => n.type === 'alert')
  for (const alert of alertNodes) {
    const ad = alert.data as any
    const incomingEdges = edges.filter((e) => e.target === alert.id)
    const sources: string[] = []
    for (const edge of incomingEdges) {
      const src = nodeMap.get(edge.source)
      if (src) sources.push(describeNode(src, edges, nodeMap))
    }
    const trigger = sources.length > 0 ? sources.join(' AND ') : '(no input)'
    const action = ad.action && ad.action !== 'fire_alert' ? `, action=${ad.action}` : ''
    parts.push(`${trigger} → ALERT(${ad.severity || 'high'}: ${ad.message || 'triggered'}${action})`)
  }

  return parts.length > 0 ? parts.join('; ') : 'empty rule'
}

function describeNode(node: Node, edges: Edge[], nodeMap: Map<string, Node>): string {
  const d = node.data as any
  switch (node.type) {
    case 'model':
      return `model.${d.output || 'risk_score'}`
    case 'anomaly':
      return `anomaly(risk>=${d.minRiskScore || 0})`
    case 'case':
      return `case.${d.caseEvent || 'created'}`
    case 'comparison': {
      const inEdges = edges.filter((e) => e.target === node.id)
      const src = inEdges[0] ? nodeMap.get(inEdges[0].source) : null
      const srcDesc = src ? describeNode(src, edges, nodeMap) : '?'
      return `${srcDesc} ${d.operator || '>'} ${d.value || '?'}`
    }
    case 'and': {
      const inEdges = edges.filter((e) => e.target === node.id)
      const descs = inEdges.map((e) => {
        const s = nodeMap.get(e.source)
        return s ? describeNode(s, edges, nodeMap) : '?'
      })
      return `(${descs.join(' AND ')})`
    }
    case 'or': {
      const inEdges = edges.filter((e) => e.target === node.id)
      const descs = inEdges.map((e) => {
        const s = nodeMap.get(e.source)
        return s ? describeNode(s, edges, nodeMap) : '?'
      })
      return `(${descs.join(' OR ')})`
    }
    case 'not': {
      const inEdges = edges.filter((e) => e.target === node.id)
      const src = inEdges[0] ? nodeMap.get(inEdges[0].source) : null
      return `NOT(${src ? describeNode(src, edges, nodeMap) : '?'})`
    }
    default:
      return node.type || '?'
  }
}

/* -- validation -------------------------------------------- */

function validateFlow(nodes: Node[], edges: Edge[]): TestResult[] {
  const messages: TestResult[] = []

  if (nodes.length === 0) {
    messages.push({ type: 'error', text: 'canvas is empty — add some nodes' })
    return messages
  }

  const alertNodes = nodes.filter((n) => n.type === 'alert')
  if (alertNodes.length === 0) {
    messages.push({ type: 'error', text: 'no alert output node — rule needs at least one' })
  }

  for (const alert of alertNodes) {
    const d = alert.data as any
    if (!d.message?.trim()) {
      messages.push({ type: 'warning', text: 'alert node is missing a message' })
    }
    const hasInput = edges.some((e) => e.target === alert.id)
    if (!hasInput) {
      messages.push({ type: 'error', text: 'alert node has no input connection' })
    }
  }

  const sourceTypes = ['model', 'anomaly', 'case']
  const sourceNodes = nodes.filter((n) => sourceTypes.includes(n.type || ''))
  if (sourceNodes.length === 0) {
    messages.push({ type: 'error', text: 'no data source — add a model, anomaly, or case node' })
  }

  for (const node of sourceNodes) {
    const d = node.data as any
    if (node.type === 'model' && !d.modelId) {
      messages.push({ type: 'warning', text: 'model node: no model selected' })
    }
    const hasOutput = edges.some((e) => e.source === node.id)
    if (!hasOutput) {
      messages.push({ type: 'warning', text: `${node.type} node is not connected to anything` })
    }
  }

  const logicNodes = nodes.filter((n) => ['comparison', 'and', 'or', 'not'].includes(n.type || ''))
  for (const node of logicNodes) {
    const hasInput = edges.some((e) => e.target === node.id)
    const hasOutput = edges.some((e) => e.source === node.id)
    if (!hasInput) messages.push({ type: 'warning', text: `${node.type} node has no input` })
    if (!hasOutput) messages.push({ type: 'warning', text: `${node.type} node has no output` })
  }

  if (messages.length === 0) {
    messages.push({ type: 'success', text: 'flow is valid — all paths connected correctly' })
  }

  return messages
}

/* -- add-node submenu items -------------------------------- */

const addNodeItems = [
  { type: 'model', label: 'model output', icon: Boxes, accent: '#9333ea' },
  { type: 'anomaly', label: 'anomaly condition', icon: AlertTriangle, accent: '#f97316' },
  { type: 'case', label: 'case condition', icon: Briefcase, accent: '#3b82f6' },
  { type: 'comparison', label: 'comparison', icon: GitCompareArrows, accent: '#06b6d4' },
  { type: 'and', label: 'AND gate', icon: CircleDot, accent: '#6366f1' },
  { type: 'or', label: 'OR gate', icon: CircleOff, accent: '#6366f1' },
  { type: 'not', label: 'NOT gate', icon: Ban, accent: '#6366f1' },
  { type: 'alert', label: 'alert output', icon: Bell, accent: '#ef4444' },
]

/* -- component --------------------------------------------- */

export function FlowCanvas({ open, onClose, onSave, initialRule }: FlowCanvasProps) {
  const { data: modelsData } = useQuery(GET_MODELS)
  const models = modelsData?.allModels?.nodes || []

  const [ruleName, setRuleName] = useState(initialRule?.name || '')
  const [severity, setSeverity] = useState(initialRule?.severity || 'medium')
  const reactFlowInstance = useRef<ReactFlowInstance | null>(null)
  const setNodesRef = useRef<any>(null)

  /* context menu state */
  const [contextMenu, setContextMenu] = useState<ContextMenuState | null>(null)
  const [addNodeSubmenuOpen, setAddNodeSubmenuOpen] = useState(false)

  /* test results state */
  const [testResults, setTestResults] = useState<TestResult[] | null>(null)

  /* node data change handler (uses ref to avoid hook ordering issues) */
  const handleNodeDataChange = useCallback((nodeId: string, key: string, value: any) => {
    setNodesRef.current?.((nds: Node[]) =>
      nds.map((n) => {
        if (n.id === nodeId) {
          return { ...n, data: { ...n.data, [key]: value } }
        }
        return n
      })
    )
  }, [])

  /* deserialize initial flow graph */
  const initialNodes = useMemo(() => {
    if (initialRule?.flowGraph?.nodes) {
      const maxId = initialRule.flowGraph.nodes.reduce((max: number, n: any) => {
        const num = parseInt(n.id.replace('n', ''), 10)
        return isNaN(num) ? max : Math.max(max, num)
      }, 0)
      nodeIdCounter = maxId
      return initialRule.flowGraph.nodes.map((n: any) => ({
        ...n,
        data: { ...n.data, onChange: handleNodeDataChange, models },
      }))
    }
    return []
  }, [initialRule, handleNodeDataChange, models])

  const initialEdges = useMemo(() => {
    if (initialRule?.flowGraph?.edges) {
      return initialRule.flowGraph.edges.map((e: any) => ({
        ...e,
        type: 'smoothstep',
        animated: true,
      }))
    }
    return []
  }, [initialRule])

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  /* assign ref so handleNodeDataChange can access setNodes */
  setNodesRef.current = setNodes

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((eds) =>
        addEdge({ ...params, type: 'smoothstep', animated: true }, eds)
      )
    },
    [setEdges]
  )

  const onInit = useCallback((instance: ReactFlowInstance) => {
    reactFlowInstance.current = instance
  }, [])

  /* -- close context menu on any click ---------------------- */
  useEffect(() => {
    if (!contextMenu) return
    const handler = () => { setContextMenu(null); setAddNodeSubmenuOpen(false) }
    document.addEventListener('click', handler)
    return () => document.removeEventListener('click', handler)
  }, [contextMenu])

  /* -- context menu handlers -------------------------------- */

  const onPaneContextMenu = useCallback((event: MouseEvent | globalThis.MouseEvent) => {
    event.preventDefault()
    setContextMenu({ x: (event as any).clientX, y: (event as any).clientY, type: 'canvas' })
    setTestResults(null)
  }, [])

  const onNodeContextMenu = useCallback((event: MouseEvent | globalThis.MouseEvent, node: Node) => {
    event.preventDefault()
    setContextMenu({ x: (event as any).clientX, y: (event as any).clientY, type: 'node', targetId: node.id })
  }, [])

  const onEdgeContextMenu = useCallback((event: MouseEvent | globalThis.MouseEvent, edge: Edge) => {
    event.preventDefault()
    setContextMenu({ x: (event as any).clientX, y: (event as any).clientY, type: 'edge', targetId: edge.id })
  }, [])

  /* -- context menu actions --------------------------------- */

  const addNodeAtPosition = useCallback((nodeType: string) => {
    if (!contextMenu || !reactFlowInstance.current) return
    const position = reactFlowInstance.current.screenToFlowPosition({
      x: contextMenu.x,
      y: contextMenu.y,
    })
    const newNode: Node = {
      id: getNextNodeId(),
      type: nodeType,
      position,
      data: { onChange: handleNodeDataChange, models },
    }
    setNodes((nds) => [...nds, newNode])
    setContextMenu(null)
  }, [contextMenu, handleNodeDataChange, models, setNodes])

  const duplicateNode = useCallback((nodeId?: string) => {
    if (!nodeId) return
    const original = nodes.find((n) => n.id === nodeId)
    if (!original) return
    const { onChange, models: m, ...cleanData } = (original.data || {}) as any
    const newNode: Node = {
      id: getNextNodeId(),
      type: original.type,
      position: { x: original.position.x + 30, y: original.position.y + 30 },
      data: { ...cleanData, onChange: handleNodeDataChange, models },
    }
    setNodes((nds) => [...nds, newNode])
    setContextMenu(null)
  }, [nodes, handleNodeDataChange, models, setNodes])

  const deleteNode = useCallback((nodeId?: string) => {
    if (!nodeId) return
    setNodes((nds) => nds.filter((n) => n.id !== nodeId))
    setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId))
    setContextMenu(null)
  }, [setNodes, setEdges])

  const deleteEdge = useCallback((edgeId?: string) => {
    if (!edgeId) return
    setEdges((eds) => eds.filter((e) => e.id !== edgeId))
    setContextMenu(null)
  }, [setEdges])

  const selectAll = useCallback(() => {
    setNodes((nds) => nds.map((n) => ({ ...n, selected: true })))
    setEdges((eds) => eds.map((e) => ({ ...e, selected: true })))
    setContextMenu(null)
  }, [setNodes, setEdges])

  const fitView = useCallback(() => {
    reactFlowInstance.current?.fitView({ padding: 0.2 })
    setContextMenu(null)
  }, [])

  const clearCanvas = useCallback(() => {
    setNodes([])
    setEdges([])
    setContextMenu(null)
  }, [setNodes, setEdges])

  /* -- drag and drop from palette -------------------------- */

  const onDragOver = useCallback((event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback(
    (event: DragEvent<HTMLDivElement>) => {
      event.preventDefault()
      const nodeType = event.dataTransfer.getData('application/reactflow')
      if (!nodeType || !reactFlowInstance.current) return

      const position = reactFlowInstance.current.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      })

      const newNode: Node = {
        id: getNextNodeId(),
        type: nodeType,
        position,
        data: { onChange: handleNodeDataChange, models },
      }

      setNodes((nds) => [...nds, newNode])
    },
    [handleNodeDataChange, models, setNodes]
  )

  /* -- save ------------------------------------------------ */

  const handleSave = useCallback(() => {
    if (!ruleName.trim()) return
    const viewport = reactFlowInstance.current?.getViewport() || { x: 0, y: 0, zoom: 1 }
    const flowGraph = serializeGraph(nodes, edges, viewport)
    const condition = generateConditionSummary(nodes, edges)
    onSave(ruleName, severity, flowGraph, condition, initialRule?.id)
  }, [ruleName, severity, nodes, edges, onSave, initialRule])

  /* -- test ------------------------------------------------ */

  const handleTest = useCallback(() => {
    const results = validateFlow(nodes, edges)
    setTestResults(results)
  }, [nodes, edges])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-[60] bg-background flex flex-col">
      {/* -- toolbar ------------------------------------------ */}
      <div className="flex items-center gap-3 px-4 py-3 border-b shrink-0">
        <Input
          className="w-64 h-8 text-sm"
          placeholder="rule name"
          value={ruleName}
          onChange={(e) => setRuleName(e.target.value)}
        />
        <Select value={severity} onValueChange={setSeverity}>
          <SelectTrigger className="w-32 h-8 text-xs">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="critical">critical</SelectItem>
            <SelectItem value="high">high</SelectItem>
            <SelectItem value="medium">medium</SelectItem>
            <SelectItem value="low">low</SelectItem>
          </SelectContent>
        </Select>
        <div className="flex-1" />
        <Button size="sm" variant="outline" className="gap-1.5 h-8" onClick={handleTest}>
          <FlaskConical className="h-3.5 w-3.5" />
          test flow
        </Button>
        <Button size="sm" variant="outline" className="gap-1.5 h-8" onClick={onClose}>
          <X className="h-3.5 w-3.5" />
          cancel
        </Button>
        <Button size="sm" className="gap-1.5 h-8" onClick={handleSave} disabled={!ruleName.trim()}>
          <Save className="h-3.5 w-3.5" />
          save rule
        </Button>
      </div>

      {/* -- test results banner ------------------------------ */}
      {testResults && (
        <div className="px-4 py-2 border-b bg-card/50 flex items-start gap-3 shrink-0">
          <div className="flex-1 flex flex-wrap gap-2">
            {testResults.map((r, i) => (
              <div key={i} className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded-md ${
                r.type === 'error' ? 'bg-red-500/10 text-red-400' :
                r.type === 'warning' ? 'bg-yellow-500/10 text-yellow-400' :
                'bg-green-500/10 text-green-400'
              }`}>
                {r.type === 'error' ? <XCircle className="h-3 w-3" /> :
                 r.type === 'warning' ? <AlertTriangle className="h-3 w-3" /> :
                 <CheckCircle className="h-3 w-3" />}
                {r.text}
              </div>
            ))}
          </div>
          <Button size="sm" variant="ghost" className="h-6 w-6 p-0 shrink-0" onClick={() => setTestResults(null)}>
            <X className="h-3 w-3" />
          </Button>
        </div>
      )}

      <div className="flex flex-1 overflow-hidden">
        {/* -- left palette ------------------------------------- */}
        <div className="w-[240px] border-r bg-card overflow-y-auto shrink-0">
          <div className="px-3 py-3 space-y-4">
            {paletteItems.map((group) => (
              <div key={group.category}>
                <div className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-2">
                  {group.category}
                </div>
                <div className="space-y-1">
                  {group.items.map((item) => {
                    const Icon = item.icon
                    return (
                      <div
                        key={item.type}
                        className="flex items-center gap-2 px-2 py-1.5 rounded-md cursor-grab hover:bg-secondary/60 transition-colors text-sm"
                        draggable
                        onDragStart={(e) => {
                          e.dataTransfer.setData('application/reactflow', item.type)
                          e.dataTransfer.effectAllowed = 'move'
                        }}
                      >
                        <Icon className="h-3.5 w-3.5 shrink-0" style={{ color: item.accent }} />
                        <span className="text-xs">{item.label}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* -- canvas ------------------------------------------- */}
        <div className="flex-1 relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onInit={onInit}
            onDragOver={onDragOver}
            onDrop={onDrop}
            nodeTypes={nodeTypes}
            defaultEdgeOptions={{ type: 'smoothstep', animated: true }}
            onPaneContextMenu={onPaneContextMenu}
            onNodeContextMenu={onNodeContextMenu}
            onEdgeContextMenu={onEdgeContextMenu}
            deleteKeyCode="Delete"
            fitView
            className="bg-background"
          >
            <Background variant={BackgroundVariant.Lines} gap={24} size={1} color="hsl(var(--muted-foreground))" style={{ opacity: 0.06 }} />
            <Controls className="!bg-card !border-border" />
            <MiniMap
              className="!bg-card !border-border"
              nodeColor="#6366f1"
              maskColor="rgba(0,0,0,0.3)"
            />
          </ReactFlow>

          {/* -- context menu ----------------------------------- */}
          {contextMenu && (
            <div
              className="fixed z-[100] min-w-[200px] rounded-lg border bg-popover text-popover-foreground shadow-xl py-1"
              style={{ left: contextMenu.x, top: contextMenu.y }}
              onClick={(e) => e.stopPropagation()}
            >
              {contextMenu.type === 'canvas' && (
                <>
                  {/* add node submenu */}
                  <div
                    className="relative"
                    onMouseEnter={() => setAddNodeSubmenuOpen(true)}
                    onMouseLeave={() => setAddNodeSubmenuOpen(false)}
                  >
                    <div className="flex items-center justify-between px-3 py-1.5 text-xs hover:bg-secondary/60 cursor-pointer rounded-sm mx-1">
                      <span>add node</span>
                      <ChevronRight className="h-3 w-3 text-muted-foreground" />
                    </div>
                    {addNodeSubmenuOpen && (
                      <div className="absolute left-full top-0 min-w-[200px] rounded-lg border bg-popover shadow-xl py-1 -mt-1 ml-0.5">
                        {addNodeItems.map((item) => {
                          const Icon = item.icon
                          return (
                            <div
                              key={item.type}
                              className="flex items-center gap-2 px-3 py-1.5 text-xs hover:bg-secondary/60 cursor-pointer rounded-sm mx-1"
                              onClick={() => addNodeAtPosition(item.type)}
                            >
                              <Icon className="h-3 w-3" style={{ color: item.accent }} />
                              {item.label}
                            </div>
                          )
                        })}
                      </div>
                    )}
                  </div>
                  <div className="h-px bg-border my-1" />
                  <div
                    className="flex items-center gap-2 px-3 py-1.5 text-xs hover:bg-secondary/60 cursor-pointer rounded-sm mx-1"
                    onClick={selectAll}
                  >
                    <MousePointer2 className="h-3 w-3 text-muted-foreground" />
                    select all
                  </div>
                  <div
                    className="flex items-center gap-2 px-3 py-1.5 text-xs hover:bg-secondary/60 cursor-pointer rounded-sm mx-1"
                    onClick={fitView}
                  >
                    <Maximize className="h-3 w-3 text-muted-foreground" />
                    fit view
                  </div>
                  <div className="h-px bg-border my-1" />
                  <div
                    className="flex items-center gap-2 px-3 py-1.5 text-xs hover:bg-red-500/10 text-red-400 cursor-pointer rounded-sm mx-1"
                    onClick={clearCanvas}
                  >
                    <Eraser className="h-3 w-3" />
                    clear canvas
                  </div>
                </>
              )}

              {contextMenu.type === 'node' && (
                <>
                  <div
                    className="flex items-center gap-2 px-3 py-1.5 text-xs hover:bg-secondary/60 cursor-pointer rounded-sm mx-1"
                    onClick={() => duplicateNode(contextMenu.targetId)}
                  >
                    <Copy className="h-3 w-3 text-muted-foreground" />
                    duplicate node
                  </div>
                  <div className="h-px bg-border my-1" />
                  <div
                    className="flex items-center gap-2 px-3 py-1.5 text-xs hover:bg-red-500/10 text-red-400 cursor-pointer rounded-sm mx-1"
                    onClick={() => deleteNode(contextMenu.targetId)}
                  >
                    <Trash2 className="h-3 w-3" />
                    delete node
                  </div>
                </>
              )}

              {contextMenu.type === 'edge' && (
                <div
                  className="flex items-center gap-2 px-3 py-1.5 text-xs hover:bg-red-500/10 text-red-400 cursor-pointer rounded-sm mx-1"
                  onClick={() => deleteEdge(contextMenu.targetId)}
                >
                  <Trash2 className="h-3 w-3" />
                  delete edge
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
