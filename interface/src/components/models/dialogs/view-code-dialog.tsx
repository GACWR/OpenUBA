'use client'

import { useState, useEffect, useCallback } from 'react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useAuth } from '@/lib/auth-provider'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ViewCodeDialogProps {
    model: any
    open: boolean
    onOpenChange: (open: boolean) => void
}

export function ViewCodeDialog({ model, open, onOpenChange }: ViewCodeDialogProps) {
    const [code, setCode] = useState<string>('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const { authFetch } = useAuth()

    const fetchCode = useCallback(async () => {
        setLoading(true)
        setError(null)
        try {
            const res = await authFetch(`${API_URL}/api/v1/models/${model.id}/code`)
            if (!res.ok) {
                throw new Error('failed to fetch code')
            }
            const data = await res.json()
            setCode(data.content)
        } catch (err) {
            console.error('error fetching code:', err)
            setError('failed to load source code. file may be missing.')
        } finally {
            setLoading(false)
        }
    }, [authFetch, model?.id])

    useEffect(() => {
        if (open && model) {
            fetchCode()
        }
    }, [open, model, fetchCode])

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[900px] h-[80vh] flex flex-col">
                <DialogHeader>
                    <DialogTitle>source code: {model.name}</DialogTitle>
                </DialogHeader>

                <div className="flex-1 min-h-0 border rounded-md bg-slate-950 overflow-hidden">
                    {loading && <div className="p-4 text-slate-400">loading code...</div>}
                    {error && <div className="p-4 text-red-400">{error}</div>}
                    {!loading && !error && (
                        <SyntaxHighlighter
                            language="python"
                            style={vscDarkPlus}
                            customStyle={{ margin: 0, height: '100%', fontSize: '13px', paddingTop: '1rem', paddingBottom: '1rem' }}
                            codeTagProps={{ style: { fontFamily: 'var(--font-mono, monospace)' } }}
                            showLineNumbers={true}
                            wrapLines={true}
                        >
                            {code}
                        </SyntaxHighlighter>
                    )}
                </div>
            </DialogContent>
        </Dialog>
    )
}
