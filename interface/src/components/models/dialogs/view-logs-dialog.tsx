'use client'

import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'
import { AlertCircle, CheckCircle2 } from 'lucide-react'

interface ViewLogsDialogProps {
    log: any
    open: boolean
    onOpenChange: (open: boolean) => void
}

export function ViewLogsDialog({ log, open, onOpenChange }: ViewLogsDialogProps) {
    if (!log) return null

    // Helper to extract clean content from error message if it's the backend wrapper
    const getLogContent = () => {
        if (log.errorMessage) {
            // Check if it's the specific "Command ... returned non-zero ...: b'...'" format
            const match = log.errorMessage.match(/returned non-zero exit status \d+: b"(.*)"/)
            if (match && match[1]) {
                try {
                    // Unescape newlines
                    return match[1].replace(/\\n/g, '\n')
                } catch (e) {
                    return log.errorMessage
                }
            }
            return log.errorMessage
        }

        if (log.outputSummary) {
            return JSON.stringify(log.outputSummary, null, 2)
        }

        return 'No logs available.'
    }

    const content = getLogContent()
    const isError = !!log.errorMessage

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-3xl max-h-[80vh] flex flex-col">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        {isError ? <AlertCircle className="text-red-500 h-5 w-5" /> : <CheckCircle2 className="text-green-500 h-5 w-5" />}
                        Execution Logs - {log.modelByModelId?.name || log.modelId}
                    </DialogTitle>
                    <p className="text-sm text-muted-foreground font-mono">{log.id}</p>
                </DialogHeader>

                <div className="flex-1 overflow-auto bg-slate-950 text-slate-50 p-4 rounded-md font-mono text-xs whitespace-pre-wrap">
                    {content}
                </div>
            </DialogContent>
        </Dialog>
    )
}
