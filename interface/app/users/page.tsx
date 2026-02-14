'use client'

import * as React from 'react'
import { useAuth } from '@/lib/auth-provider'
import { useRouter } from 'next/navigation'
import { useUIStore } from '@/lib/state/ui-store'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Plus, Edit2, Trash2, X, Loader2, Shield } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function UsersPage() {
    const { user: currentUser } = useAuth()
    const router = useRouter()
    const isAdmin = currentUser?.role === 'admin'
    const isManager = currentUser?.role === 'manager' || isAdmin

    const [users, setUsers] = React.useState<any[]>([])
    const [loading, setLoading] = React.useState(true)
    const [showPanel, setShowPanel] = React.useState(false)
    const [panelClosing, setPanelClosing] = React.useState(false)
    const [editUser, setEditUser] = React.useState<any>(null)
    const [form, setForm] = React.useState({ username: '', email: '', password: '', role: 'analyst', display_name: '' })
    const [saving, setSaving] = React.useState(false)

    const getHeaders = (): Record<string, string> => {
        const token = useUIStore.getState().token
        return token ? { Authorization: `Bearer ${token}` } : {}
    }

    const fetchUsers = React.useCallback(async () => {
        try {
            const res = await fetch(`${API_URL}/api/v1/auth/users`, { headers: getHeaders() })
            if (res.ok) setUsers(await res.json())
        } catch (e) { console.error(e) }
        finally { setLoading(false) }
    }, [])

    React.useEffect(() => {
        if (!isManager) { router.replace('/'); return }
        fetchUsers()
    }, [isManager, router, fetchUsers])

    const openAdd = () => {
        setEditUser(null)
        setForm({ username: '', email: '', password: '', role: 'analyst', display_name: '' })
        setPanelClosing(false)
        setShowPanel(true)
    }

    const openEdit = (u: any) => {
        setEditUser(u)
        setForm({ username: u.username, email: u.email || '', password: '', role: u.role, display_name: u.display_name || '' })
        setPanelClosing(false)
        setShowPanel(true)
    }

    const closePanel = () => {
        setPanelClosing(true)
        setTimeout(() => { setShowPanel(false); setPanelClosing(false); setEditUser(null) }, 200)
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
                    headers: { 'Content-Type': 'application/json', ...getHeaders() },
                    body: JSON.stringify(body),
                })
            } else {
                await fetch(`${API_URL}/api/v1/auth/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...getHeaders() },
                    body: JSON.stringify(form),
                })
            }
            await fetchUsers()
            closePanel()
        } catch (e) { console.error(e) }
        finally { setSaving(false) }
    }

    const handleDelete = async (userId: string) => {
        await fetch(`${API_URL}/api/v1/auth/users/${userId}`, {
            method: 'DELETE',
            headers: getHeaders(),
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

    if (!isManager) return null

    return (
        <div className="space-y-6 relative">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Shield className="h-6 w-6 text-cyan-500" />
                    <div>
                        <h1 className="text-2xl font-bold tracking-tight">User Management</h1>
                        <p className="text-muted-foreground">Manage user accounts and roles</p>
                    </div>
                </div>
                {isAdmin && (
                    <Button onClick={openAdd} className="gap-2">
                        <Plus className="h-4 w-4" /> Add User
                    </Button>
                )}
            </div>

            <Card>
                <CardContent className="pt-6">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Username</TableHead>
                                <TableHead>Display Name</TableHead>
                                <TableHead>Email</TableHead>
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
                                    <TableCell className="text-muted-foreground">{u.email || '-'}</TableCell>
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
                                    <TableCell colSpan={isAdmin ? 8 : 7} className="text-center text-muted-foreground py-8">No users found</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </CardContent>
            </Card>

            {/* Add/Edit panel */}
            {showPanel && (
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
