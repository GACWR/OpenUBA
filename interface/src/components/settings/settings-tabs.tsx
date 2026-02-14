'use client'

import React from 'react'

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Plus, Trash2, Edit2, X, Loader2, CheckCircle2, XCircle, Zap, Brain, Bot, Sparkles, Database, Cpu, Save, Shield } from "lucide-react"
import { useAuth } from '@/lib/auth-provider'
import { useUIStore } from '@/lib/state/ui-store'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

function getAuthHeaders(): Record<string, string> {
    const token = useUIStore.getState().token
    return token ? { Authorization: `Bearer ${token}` } : {}
}

type IntegrationType = 'ollama' | 'openai' | 'claude' | 'gemini' | 'elasticsearch' | 'spark'

interface IntegrationDef {
    type: IntegrationType
    name: string
    description: string
    category: 'llm' | 'data'
    icon: React.ReactNode
    color: string
    fields: FieldDef[]
}

interface FieldDef {
    key: string
    label: string
    type: 'text' | 'password' | 'select' | 'toggle'
    placeholder?: string
    options?: { value: string; label: string }[]
    required?: boolean
}

const INTEGRATION_DEFS: IntegrationDef[] = [
    {
        type: 'ollama',
        name: 'Ollama',
        description: 'Local or remote Ollama LLM server',
        category: 'llm',
        icon: <Bot className="h-5 w-5" />,
        color: 'text-green-500 bg-green-500/10',
        fields: [
            { key: 'host', label: 'Host URL', type: 'text', placeholder: 'http://localhost:11434', required: true },
            { key: 'model', label: 'Model', type: 'text', placeholder: 'llama3.1' },
        ],
    },
    {
        type: 'openai',
        name: 'OpenAI',
        description: 'GPT-4o, GPT-4o-mini, and other OpenAI models',
        category: 'llm',
        icon: <Sparkles className="h-5 w-5" />,
        color: 'text-emerald-500 bg-emerald-500/10',
        fields: [
            { key: 'api_key', label: 'API Key', type: 'password', placeholder: 'sk-...', required: true },
            {
                key: 'model', label: 'Model', type: 'select', options: [
                    { value: 'gpt-4o', label: 'GPT-4o' },
                    { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
                    { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
                    { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
                ],
            },
            { key: 'base_url', label: 'Base URL (optional)', type: 'text', placeholder: 'https://api.openai.com/v1' },
        ],
    },
    {
        type: 'claude',
        name: 'Claude',
        description: 'Anthropic Claude models',
        category: 'llm',
        icon: <Brain className="h-5 w-5" />,
        color: 'text-orange-500 bg-orange-500/10',
        fields: [
            { key: 'api_key', label: 'API Key', type: 'password', placeholder: 'sk-ant-...', required: true },
            {
                key: 'model', label: 'Model', type: 'select', options: [
                    { value: 'claude-sonnet-4-5-20250929', label: 'Claude Sonnet 4.5' },
                    { value: 'claude-haiku-4-5-20251001', label: 'Claude Haiku 4.5' },
                    { value: 'claude-opus-4-6', label: 'Claude Opus 4.6' },
                ],
            },
        ],
    },
    {
        type: 'gemini',
        name: 'Gemini',
        description: 'Google Gemini AI models',
        category: 'llm',
        icon: <Zap className="h-5 w-5" />,
        color: 'text-blue-500 bg-blue-500/10',
        fields: [
            { key: 'api_key', label: 'API Key', type: 'password', placeholder: 'AI...', required: true },
            {
                key: 'model', label: 'Model', type: 'select', options: [
                    { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash' },
                    { value: 'gemini-1.5-pro', label: 'Gemini 1.5 Pro' },
                    { value: 'gemini-1.5-flash', label: 'Gemini 1.5 Flash' },
                ],
            },
        ],
    },
    {
        type: 'elasticsearch',
        name: 'Elasticsearch',
        description: 'External Elasticsearch cluster for log storage',
        category: 'data',
        icon: <Database className="h-5 w-5" />,
        color: 'text-cyan-500 bg-cyan-500/10',
        fields: [
            { key: 'host', label: 'Host URL', type: 'text', placeholder: 'http://elasticsearch:9200', required: true },
            { key: 'api_key', label: 'API Key (optional)', type: 'password', placeholder: '' },
            { key: 'verify_ssl', label: 'Verify SSL', type: 'toggle' },
        ],
    },
    {
        type: 'spark',
        name: 'Apache Spark',
        description: 'External Spark cluster for data processing',
        category: 'data',
        icon: <Cpu className="h-5 w-5" />,
        color: 'text-amber-500 bg-amber-500/10',
        fields: [
            { key: 'master_url', label: 'Master URL', type: 'text', placeholder: 'spark://spark-master:7077', required: true },
            {
                key: 'deploy_mode', label: 'Deploy Mode', type: 'select', options: [
                    { value: 'client', label: 'Client' },
                    { value: 'cluster', label: 'Cluster' },
                ],
            },
        ],
    },
]

interface IntegrationState {
    integration_type: string
    enabled: boolean
    config: Record<string, any>
    created_at: string | null
    updated_at: string | null
}

export function SettingsTabs() {
    const { user } = useAuth()
    const isAdmin = user?.role === 'admin'
    const isManager = user?.role === 'manager' || isAdmin

    return (
        <Tabs defaultValue="general" className="space-y-4">
            <TabsList>
                <TabsTrigger value="general">General</TabsTrigger>
                <TabsTrigger value="integrations">Integrations</TabsTrigger>
                <TabsTrigger value="registries">Model Registries</TabsTrigger>
                {isManager && <TabsTrigger value="users">Users</TabsTrigger>}
                {isAdmin && <TabsTrigger value="access">Access</TabsTrigger>}
            </TabsList>

            <TabsContent value="general">
                <Card>
                    <CardHeader>
                        <CardTitle>General Settings</CardTitle>
                        <CardDescription>Manage your instance configuration.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="grid gap-2">
                            <Label htmlFor="instance-name">Instance Name</Label>
                            <Input id="instance-name" defaultValue="OpenUBA Production" />
                        </div>

                        <div className="grid gap-2">
                            <Label htmlFor="language">Language</Label>
                            <Select defaultValue="en">
                                <SelectTrigger id="language">
                                    <SelectValue placeholder="Select language" />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="en">English</SelectItem>
                                    <SelectItem value="es">Spanish</SelectItem>
                                    <SelectItem value="fr">French</SelectItem>
                                    <SelectItem value="de">German</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>

                        <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                                <Label className="text-base">Dark Mode</Label>
                                <p className="text-sm text-muted-foreground">Enable dark mode for the dashboard.</p>
                            </div>
                            <Switch defaultChecked />
                        </div>

                        <div className="flex items-center justify-between">
                            <div className="space-y-0.5">
                                <Label className="text-base">Auto-refresh Dashboard</Label>
                                <p className="text-sm text-muted-foreground">Automatically refresh dashboard data every 30 seconds.</p>
                            </div>
                            <Switch defaultChecked />
                        </div>

                        <Button>Save Changes</Button>
                    </CardContent>
                </Card>
            </TabsContent>

            <TabsContent value="integrations">
                <IntegrationsPanel />
            </TabsContent>

            <TabsContent value="registries">
                <Card>
                    <CardHeader>
                        <div className="flex items-center justify-between">
                            <div>
                                <CardTitle>Model Registries</CardTitle>
                                <CardDescription>Manage model sources.</CardDescription>
                            </div>
                            <Button size="sm" className="gap-2">
                                <Plus className="h-4 w-4" /> Add Registry
                            </Button>
                        </div>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-4">
                            <div className="flex items-center justify-between p-4 border rounded-lg">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <p className="font-medium">OpenUBA Hub</p>
                                        <Badge variant="secondary" className="text-xs">Default</Badge>
                                    </div>
                                    <p className="text-sm text-muted-foreground">https://hub.openuba.org</p>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button variant="ghost" size="icon"><Edit2 className="h-4 w-4" /></Button>
                                </div>
                            </div>

                            <div className="flex items-center justify-between p-4 border rounded-lg">
                                <div>
                                    <div className="flex items-center gap-2">
                                        <p className="font-medium">Local Filesystem</p>
                                        <Badge variant="secondary" className="text-xs">Dev</Badge>
                                    </div>
                                    <p className="text-sm text-muted-foreground">core/model_library</p>
                                </div>
                                <div className="flex items-center gap-2">
                                    <Button variant="ghost" size="icon"><Edit2 className="h-4 w-4" /></Button>
                                </div>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </TabsContent>

            {isManager && (
                <TabsContent value="users">
                    <UsersSettingsCard />
                </TabsContent>
            )}
            {isAdmin && (
                <TabsContent value="access">
                    <PermissionsMatrix />
                </TabsContent>
            )}
        </Tabs>
    )
}

function IntegrationsPanel() {
    const [integrations, setIntegrations] = React.useState<IntegrationState[]>([])
    const [loading, setLoading] = React.useState(true)
    const [configPanel, setConfigPanel] = React.useState<IntegrationType | null>(null)
    const [panelClosing, setPanelClosing] = React.useState(false)
    const [formData, setFormData] = React.useState<Record<string, any>>({})
    const [saving, setSaving] = React.useState(false)
    const [testing, setTesting] = React.useState(false)
    const [testResult, setTestResult] = React.useState<{ status: string; message?: string } | null>(null)

    const fetchIntegrations = React.useCallback(async () => {
        try {
            const resp = await fetch(`${API_URL}/api/v1/settings/integrations`, {
                headers: getAuthHeaders(),
            })
            if (resp.ok) {
                const data = await resp.json()
                setIntegrations(data)
            }
        } catch (e) {
            console.error('failed to fetch integrations', e)
        } finally {
            setLoading(false)
        }
    }, [])

    React.useEffect(() => {
        fetchIntegrations()
    }, [fetchIntegrations])

    const openConfigPanel = (type: IntegrationType) => {
        const existing = integrations.find(i => i.integration_type === type)
        setFormData({
            enabled: existing?.enabled ?? false,
            ...existing?.config ?? {},
        })
        setTestResult(null)
        setPanelClosing(false)
        setConfigPanel(type)
    }

    const closeConfigPanel = () => {
        setPanelClosing(true)
        setTimeout(() => {
            setConfigPanel(null)
            setPanelClosing(false)
        }, 200)
    }

    const handleSave = async () => {
        if (!configPanel) return
        setSaving(true)
        try {
            const { enabled, ...config } = formData
            const resp = await fetch(`${API_URL}/api/v1/settings/integrations/${configPanel}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
                body: JSON.stringify({ enabled: enabled ?? false, config }),
            })
            if (resp.ok) {
                await fetchIntegrations()
                closeConfigPanel()
            }
        } catch (e) {
            console.error('save failed', e)
        } finally {
            setSaving(false)
        }
    }

    const handleTest = async () => {
        if (!configPanel) return
        setTesting(true)
        setTestResult(null)

        // save first so test uses latest config
        try {
            const { enabled, ...config } = formData
            await fetch(`${API_URL}/api/v1/settings/integrations/${configPanel}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
                body: JSON.stringify({ enabled: enabled ?? false, config }),
            })
        } catch { /* ignore save error during test */ }

        try {
            const resp = await fetch(`${API_URL}/api/v1/settings/integrations/${configPanel}/test`, {
                headers: getAuthHeaders(),
            })
            if (resp.ok) {
                const data = await resp.json()
                setTestResult(data)
            } else {
                setTestResult({ status: 'error', message: `HTTP ${resp.status}` })
            }
        } catch (e: any) {
            setTestResult({ status: 'error', message: e.message })
        } finally {
            setTesting(false)
            await fetchIntegrations()
        }
    }

    const getStatus = (type: string): 'connected' | 'configured' | 'not_configured' => {
        const i = integrations.find(x => x.integration_type === type)
        if (!i || !i.enabled) return 'not_configured'
        if (i.config && Object.keys(i.config).length > 0) return 'connected'
        return 'configured'
    }

    const statusBadge = (type: string) => {
        const s = getStatus(type)
        if (s === 'connected') return <Badge variant="outline" className="bg-green-500/10 text-green-500 border-green-500/20">Enabled</Badge>
        if (s === 'configured') return <Badge variant="outline" className="bg-blue-500/10 text-blue-500 border-blue-500/20">Configured</Badge>
        return <Badge variant="outline" className="bg-white/5 text-muted-foreground border-white/10">Not Configured</Badge>
    }

    const llmDefs = INTEGRATION_DEFS.filter(d => d.category === 'llm')
    const dataDefs = INTEGRATION_DEFS.filter(d => d.category === 'data')
    const activeDef = configPanel ? INTEGRATION_DEFS.find(d => d.type === configPanel) : null

    return (
        <div className="relative">
            <Card>
                <CardHeader>
                    <CardTitle>Integrations</CardTitle>
                    <CardDescription>Configure LLM providers and external data services.</CardDescription>
                </CardHeader>
                <CardContent className="space-y-8">
                    <div>
                        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">LLM Providers</h3>
                        <div className="space-y-3">
                            {llmDefs.map(def => (
                                <div key={def.type} className="flex items-center justify-between p-4 border border-white/5 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors">
                                    <div className="flex items-center gap-4">
                                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${def.color}`}>
                                            {def.icon}
                                        </div>
                                        <div>
                                            <p className="font-medium">{def.name}</p>
                                            <p className="text-sm text-muted-foreground">{def.description}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        {statusBadge(def.type)}
                                        <Button variant="outline" size="sm" onClick={() => openConfigPanel(def.type)}>Configure</Button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div>
                        <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-4">Data Engines</h3>
                        <div className="space-y-3">
                            {dataDefs.map(def => (
                                <div key={def.type} className="flex items-center justify-between p-4 border border-white/5 rounded-xl bg-white/[0.02] hover:bg-white/[0.04] transition-colors">
                                    <div className="flex items-center gap-4">
                                        <div className={`h-10 w-10 rounded-xl flex items-center justify-center ${def.color}`}>
                                            {def.icon}
                                        </div>
                                        <div>
                                            <p className="font-medium">{def.name}</p>
                                            <p className="text-sm text-muted-foreground">{def.description}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3">
                                        {statusBadge(def.type)}
                                        <Button variant="outline" size="sm" onClick={() => openConfigPanel(def.type)}>Configure</Button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Animated right-side config panel */}
            {configPanel && activeDef && (
                <>
                    {/* Backdrop */}
                    <div
                        className={`fixed inset-0 bg-black/40 backdrop-blur-sm z-50 transition-opacity duration-300 ${panelClosing ? 'opacity-0' : 'opacity-100'}`}
                        onClick={closeConfigPanel}
                    />

                    {/* Panel */}
                    <div
                        className={`fixed top-0 right-0 h-full w-[480px] max-w-[90vw] bg-background border-l border-white/10 z-50 flex flex-col ${panelClosing ? 'animate-slide-out-right' : 'animate-slide-in-right'}`}
                    >
                        <div className="flex items-center justify-between p-6 border-b border-white/5">
                            <div className="flex items-center gap-3">
                                <div className={`h-9 w-9 rounded-lg flex items-center justify-center ${activeDef.color}`}>
                                    {activeDef.icon}
                                </div>
                                <div>
                                    <h2 className="font-semibold">{activeDef.name}</h2>
                                    <p className="text-xs text-muted-foreground">{activeDef.description}</p>
                                </div>
                            </div>
                            <Button variant="ghost" size="icon" onClick={closeConfigPanel}>
                                <X className="h-4 w-4" />
                            </Button>
                        </div>

                        <div className="flex-1 overflow-y-auto p-6 space-y-6">
                            {/* Enable toggle */}
                            <div className="flex items-center justify-between">
                                <div>
                                    <Label className="text-base">Enabled</Label>
                                    <p className="text-sm text-muted-foreground">Make this integration available</p>
                                </div>
                                <Switch
                                    checked={formData.enabled ?? false}
                                    onCheckedChange={(v) => setFormData(prev => ({ ...prev, enabled: v }))}
                                />
                            </div>

                            <div className="border-t border-white/5 pt-6 space-y-4">
                                {activeDef.fields.map(field => (
                                    <div key={field.key} className="space-y-2">
                                        <Label htmlFor={field.key}>{field.label}</Label>
                                        {field.type === 'text' && (
                                            <Input
                                                id={field.key}
                                                value={formData[field.key] ?? ''}
                                                placeholder={field.placeholder}
                                                onChange={(e) => setFormData(prev => ({ ...prev, [field.key]: e.target.value }))}
                                            />
                                        )}
                                        {field.type === 'password' && (
                                            <Input
                                                id={field.key}
                                                type="password"
                                                value={formData[field.key] ?? ''}
                                                placeholder={field.placeholder}
                                                onChange={(e) => setFormData(prev => ({ ...prev, [field.key]: e.target.value }))}
                                            />
                                        )}
                                        {field.type === 'select' && field.options && (
                                            <Select
                                                value={formData[field.key] ?? field.options[0]?.value ?? ''}
                                                onValueChange={(v) => setFormData(prev => ({ ...prev, [field.key]: v }))}
                                            >
                                                <SelectTrigger>
                                                    <SelectValue />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {field.options.map(opt => (
                                                        <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                        )}
                                        {field.type === 'toggle' && (
                                            <Switch
                                                checked={formData[field.key] ?? true}
                                                onCheckedChange={(v) => setFormData(prev => ({ ...prev, [field.key]: v }))}
                                            />
                                        )}
                                    </div>
                                ))}
                            </div>

                            {/* Test result */}
                            {testResult && (
                                <div className={`p-3 rounded-lg text-sm flex items-center gap-2 ${testResult.status === 'connected' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                                    {testResult.status === 'connected' ? (
                                        <CheckCircle2 className="h-4 w-4 shrink-0" />
                                    ) : (
                                        <XCircle className="h-4 w-4 shrink-0" />
                                    )}
                                    <span>{testResult.status === 'connected' ? 'Connection successful' : testResult.message || 'Connection failed'}</span>
                                </div>
                            )}
                        </div>

                        <div className="p-6 border-t border-white/5 flex items-center gap-3">
                            <Button
                                variant="outline"
                                onClick={handleTest}
                                disabled={testing}
                                className="gap-2"
                            >
                                {testing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Zap className="h-4 w-4" />}
                                Test Connection
                            </Button>
                            <div className="flex-1" />
                            <Button variant="ghost" onClick={closeConfigPanel}>Cancel</Button>
                            <Button onClick={handleSave} disabled={saving}>
                                {saving ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                                Save
                            </Button>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

function UsersSettingsCard() {
    const { user: currentUser } = useAuth()
    const isAdmin = currentUser?.role === 'admin'
    const [users, setUsers] = React.useState<any[]>([])
    const [loading, setLoading] = React.useState(true)
    const [showAddPanel, setShowAddPanel] = React.useState(false)
    const [panelClosing, setPanelClosing] = React.useState(false)
    const [editUser, setEditUser] = React.useState<any>(null)
    const [form, setForm] = React.useState({ username: '', email: '', password: '', role: 'analyst', display_name: '' })
    const [saving, setSaving] = React.useState(false)

    const fetchUsers = React.useCallback(async () => {
        try {
            const response = await fetch(`${API_URL}/api/v1/auth/users`, { headers: getAuthHeaders() })
            if (response.ok) setUsers(await response.json())
        } catch (e) { console.error('failed to fetch users', e) }
        finally { setLoading(false) }
    }, [])

    React.useEffect(() => { fetchUsers() }, [fetchUsers])

    const openAdd = () => {
        setEditUser(null)
        setForm({ username: '', email: '', password: '', role: 'analyst', display_name: '' })
        setPanelClosing(false)
        setShowAddPanel(true)
    }

    const openEdit = (u: any) => {
        setEditUser(u)
        setForm({ username: u.username, email: u.email || '', password: '', role: u.role, display_name: u.display_name || '' })
        setPanelClosing(false)
        setShowAddPanel(true)
    }

    const closePanel = () => {
        setPanelClosing(true)
        setTimeout(() => { setShowAddPanel(false); setPanelClosing(false); setEditUser(null) }, 200)
    }

    const handleSave = async () => {
        setSaving(true)
        try {
            if (editUser) {
                const body: any = {}
                if (form.role !== editUser.role) body.role = form.role
                if (form.display_name !== (editUser.display_name || '')) body.display_name = form.display_name
                if (form.email !== (editUser.email || '')) body.email = form.email
                if (form.password) body.password = form.password
                await fetch(`${API_URL}/api/v1/auth/users/${editUser.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
                    body: JSON.stringify(body),
                })
            } else {
                await fetch(`${API_URL}/api/v1/auth/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
                    body: JSON.stringify(form),
                })
            }
            await fetchUsers()
            closePanel()
        } catch (e) { console.error('save user failed', e) }
        finally { setSaving(false) }
    }

    const handleDelete = async (userId: string) => {
        await fetch(`${API_URL}/api/v1/auth/users/${userId}`, {
            method: 'DELETE',
            headers: getAuthHeaders(),
        })
        await fetchUsers()
    }

    const roleBadge = (role: string) => {
        const colors: Record<string, string> = {
            admin: 'bg-red-500/10 text-red-400 border-red-500/20',
            manager: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
            triage: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
            analyst: 'bg-green-500/10 text-green-400 border-green-500/20',
        }
        return <Badge variant="outline" className={colors[role] || ''}>{role}</Badge>
    }

    return (
        <div className="relative">
            <Card>
                <CardHeader>
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle>Users</CardTitle>
                            <CardDescription>Manage user access and roles.</CardDescription>
                        </div>
                        {isAdmin && (
                            <Button size="sm" className="gap-2" onClick={openAdd}>
                                <Plus className="h-4 w-4" /> Add User
                            </Button>
                        )}
                    </div>
                </CardHeader>
                <CardContent>
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Username</TableHead>
                                <TableHead>Display Name</TableHead>
                                <TableHead>Role</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Last Login</TableHead>
                                <TableHead>Created</TableHead>
                                {isAdmin && <TableHead className="text-right">Actions</TableHead>}
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {users.map((u) => (
                                <TableRow key={u.id}>
                                    <TableCell className="font-medium">{u.username}</TableCell>
                                    <TableCell>{u.display_name || '-'}</TableCell>
                                    <TableCell>{roleBadge(u.role)}</TableCell>
                                    <TableCell>
                                        {u.is_active !== false
                                            ? <Badge className="bg-green-500/10 text-green-500 border-green-500/20">Active</Badge>
                                            : <Badge className="bg-red-500/10 text-red-500 border-red-500/20">Disabled</Badge>}
                                    </TableCell>
                                    <TableCell className="text-sm text-muted-foreground">
                                        {u.last_login_at ? new Date(u.last_login_at).toLocaleDateString() : 'Never'}
                                    </TableCell>
                                    <TableCell className="text-sm text-muted-foreground">{new Date(u.created_at).toLocaleDateString()}</TableCell>
                                    {isAdmin && (
                                        <TableCell className="text-right">
                                            <Button variant="ghost" size="icon" onClick={() => openEdit(u)}><Edit2 className="h-4 w-4" /></Button>
                                            {u.username !== currentUser?.username && (
                                                <Button variant="ghost" size="icon" className="text-red-500" onClick={() => handleDelete(u.id)}><Trash2 className="h-4 w-4" /></Button>
                                            )}
                                        </TableCell>
                                    )}
                                </TableRow>
                            ))}
                            {users.length === 0 && !loading && (
                                <TableRow>
                                    <TableCell colSpan={isAdmin ? 7 : 6} className="text-center text-muted-foreground">No users found</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Add/Edit user panel */}
            {showAddPanel && (
                <>
                    <div className={`fixed inset-0 bg-black/40 backdrop-blur-sm z-50 transition-opacity duration-300 ${panelClosing ? 'opacity-0' : 'opacity-100'}`} onClick={closePanel} />
                    <div className={`fixed top-0 right-0 h-full w-[420px] max-w-[90vw] bg-background border-l border-white/10 z-50 flex flex-col ${panelClosing ? 'animate-slide-out-right' : 'animate-slide-in-right'}`}>
                        <div className="flex items-center justify-between p-6 border-b border-white/5">
                            <h2 className="font-semibold">{editUser ? 'Edit User' : 'Add User'}</h2>
                            <Button variant="ghost" size="icon" onClick={closePanel}><X className="h-4 w-4" /></Button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-6 space-y-4">
                            {!editUser && (
                                <div className="space-y-2">
                                    <Label>Username</Label>
                                    <Input value={form.username} onChange={(e) => setForm(f => ({ ...f, username: e.target.value }))} placeholder="username" />
                                </div>
                            )}
                            <div className="space-y-2">
                                <Label>Display Name</Label>
                                <Input value={form.display_name} onChange={(e) => setForm(f => ({ ...f, display_name: e.target.value }))} placeholder="Display Name" />
                            </div>
                            <div className="space-y-2">
                                <Label>Email</Label>
                                <Input type="email" value={form.email} onChange={(e) => setForm(f => ({ ...f, email: e.target.value }))} placeholder="user@example.com" />
                            </div>
                            <div className="space-y-2">
                                <Label>{editUser ? 'New Password (leave blank to keep)' : 'Password'}</Label>
                                <Input type="password" value={form.password} onChange={(e) => setForm(f => ({ ...f, password: e.target.value }))} placeholder={editUser ? '(unchanged)' : 'password'} />
                            </div>
                            <div className="space-y-2">
                                <Label>Role</Label>
                                <Select value={form.role} onValueChange={(v) => setForm(f => ({ ...f, role: v }))}>
                                    <SelectTrigger><SelectValue /></SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="admin">Admin</SelectItem>
                                        <SelectItem value="manager">Manager</SelectItem>
                                        <SelectItem value="triage">Triage</SelectItem>
                                        <SelectItem value="analyst">Analyst</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                        <div className="p-6 border-t border-white/5 flex gap-3 justify-end">
                            <Button variant="ghost" onClick={closePanel}>Cancel</Button>
                            <Button onClick={handleSave} disabled={saving}>
                                {saving && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
                                {editUser ? 'Update' : 'Create'}
                            </Button>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

const ALL_PAGES = ['home', 'data', 'models', 'rules', 'alerts', 'entities', 'anomalies', 'cases', 'schedules', 'settings', 'users']
const EDITABLE_ROLES = ['manager', 'triage', 'analyst']

function PermissionsMatrix() {
    const [matrix, setMatrix] = React.useState<Record<string, Record<string, { read: boolean; write: boolean }>>>({})
    const [loading, setLoading] = React.useState(true)
    const [saving, setSaving] = React.useState(false)

    const fetchMatrix = React.useCallback(async () => {
        try {
            const resp = await fetch(`${API_URL}/api/v1/auth/permissions`, { headers: getAuthHeaders() })
            if (resp.ok) setMatrix(await resp.json())
        } catch (e) { console.error('failed to fetch permissions', e) }
        finally { setLoading(false) }
    }, [])

    React.useEffect(() => { fetchMatrix() }, [fetchMatrix])

    const toggle = (role: string, page: string, access: 'read' | 'write') => {
        setMatrix(prev => {
            const updated = { ...prev }
            if (!updated[role]) updated[role] = {}
            if (!updated[role][page]) updated[role][page] = { read: false, write: false }
            updated[role] = { ...updated[role] }
            updated[role][page] = { ...updated[role][page], [access]: !updated[role][page][access] }
            return updated
        })
    }

    const saveRole = async (role: string) => {
        setSaving(true)
        try {
            await fetch(`${API_URL}/api/v1/auth/permissions`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
                body: JSON.stringify({ role, permissions: matrix[role] || {} }),
            })
        } catch (e) { console.error('save permissions failed', e) }
        finally { setSaving(false) }
    }

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center gap-3">
                    <Shield className="h-5 w-5 text-cyan-500" />
                    <div>
                        <CardTitle>Role Permissions</CardTitle>
                        <CardDescription>Configure page-level read/write access for each role. Admin always has full access.</CardDescription>
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                {loading ? (
                    <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin text-muted-foreground" /></div>
                ) : (
                    <div className="space-y-6">
                        {EDITABLE_ROLES.map(role => (
                            <div key={role} className="border border-white/5 rounded-xl p-4">
                                <div className="flex items-center justify-between mb-4">
                                    <h3 className="font-semibold capitalize">{role}</h3>
                                    <Button size="sm" variant="outline" onClick={() => saveRole(role)} disabled={saving} className="gap-2">
                                        {saving ? <Loader2 className="h-3 w-3 animate-spin" /> : <Save className="h-3 w-3" />}
                                        Save
                                    </Button>
                                </div>
                                <Table>
                                    <TableHeader>
                                        <TableRow>
                                            <TableHead className="w-32">Page</TableHead>
                                            <TableHead className="w-24 text-center">Read</TableHead>
                                            <TableHead className="w-24 text-center">Write</TableHead>
                                        </TableRow>
                                    </TableHeader>
                                    <TableBody>
                                        {ALL_PAGES.map(page => {
                                            const perm = matrix[role]?.[page] || { read: false, write: false }
                                            return (
                                                <TableRow key={page}>
                                                    <TableCell className="capitalize font-medium">{page}</TableCell>
                                                    <TableCell className="text-center">
                                                        <Switch checked={perm.read} onCheckedChange={() => toggle(role, page, 'read')} />
                                                    </TableCell>
                                                    <TableCell className="text-center">
                                                        <Switch checked={perm.write} onCheckedChange={() => toggle(role, page, 'write')} />
                                                    </TableCell>
                                                </TableRow>
                                            )
                                        })}
                                    </TableBody>
                                </Table>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    )
}
