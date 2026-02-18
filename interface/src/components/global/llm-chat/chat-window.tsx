'use client'

import * as React from 'react'
import ReactMarkdown from 'react-markdown'
import { usePathname, useParams } from 'next/navigation'
import { useUIStore, ChatMessage } from '@/lib/state/ui-store'
import { X, Minus, Send, Trash2, Loader2, ChevronDown, ChevronRight, Brain, Bot } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const LLM_PROVIDERS = [
    { value: 'ollama', label: 'Ollama' },
    { value: 'openai', label: 'OpenAI' },
    { value: 'claude', label: 'Claude' },
    { value: 'gemini', label: 'Gemini' },
]

type EnabledProvider = {
    integration_type: string
    enabled: boolean
    config: Record<string, any>
}

/** Parse content into thinking blocks and response text */
function parseThinkingContent(content: string): { thinking: string[]; response: string; isStillThinking: boolean } {
    if (!content) return { thinking: [], response: '', isStillThinking: false }

    const thinking: string[] = []
    let response = content

    // extract completed <think>...</think> blocks
    const thinkRegex = /<think>([\s\S]*?)<\/think>/g
    let match
    while ((match = thinkRegex.exec(content)) !== null) {
        // split thinking content into paragraphs
        const paragraphs = match[1]
            .split(/\n\n+/)
            .map(p => p.trim())
            .filter(p => p.length > 0)
        thinking.push(...paragraphs)
    }

    // remove completed think blocks from response
    response = response.replace(/<think>[\s\S]*?<\/think>/g, '').trim()

    // check for unclosed <think> tag (still thinking)
    const unclosedMatch = response.match(/<think>([\s\S]*)$/)
    let isStillThinking = false
    if (unclosedMatch) {
        isStillThinking = true
        const partial = unclosedMatch[1]
            .split(/\n\n+/)
            .map(p => p.trim())
            .filter(p => p.length > 0)
        thinking.push(...partial)
        response = response.replace(/<think>[\s\S]*$/, '').trim()
    }

    return { thinking, response, isStillThinking }
}

/** Collapsible thinking block component */
function ThinkingBlock({ paragraphs, isStillThinking, isStreaming }: {
    paragraphs: string[]
    isStillThinking: boolean
    isStreaming: boolean
}) {
    const [isExpanded, setIsExpanded] = React.useState(false)

    if (paragraphs.length === 0 && !isStillThinking) return null

    return (
        <div className="mb-2">
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="flex items-center gap-1.5 text-xs text-purple-400/80 hover:text-purple-300 transition-colors group"
            >
                <Brain className="h-3 w-3" />
                <span className="font-medium">
                    {isStillThinking ? 'Thinking' : 'Thought process'}
                </span>
                {isStillThinking && isStreaming && (
                    <span className="flex gap-0.5">
                        <span className="w-1 h-1 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                        <span className="w-1 h-1 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                        <span className="w-1 h-1 rounded-full bg-purple-400 animate-bounce" style={{ animationDelay: '300ms' }} />
                    </span>
                )}
                {!isStillThinking && (
                    <ChevronRight className={`h-3 w-3 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                )}
            </button>

            {(isExpanded || isStillThinking) && paragraphs.length > 0 && (
                <div className="mt-1.5 pl-4 border-l border-purple-500/20 space-y-1.5 max-h-[200px] overflow-y-auto scrollbar-hide">
                    {paragraphs.map((p, i) => (
                        <p key={i} className="text-[11px] leading-relaxed text-purple-300/50 italic">
                            {p}
                        </p>
                    ))}
                </div>
            )}
        </div>
    )
}

/** Markdown-rendered assistant message */
function AssistantContent({ content, isStreaming, isLast }: {
    content: string
    isStreaming: boolean
    isLast: boolean
}) {
    const { thinking, response, isStillThinking } = React.useMemo(
        () => parseThinkingContent(content),
        [content]
    )

    const hasThinking = thinking.length > 0 || isStillThinking
    const showCursor = isStreaming && isLast && !isStillThinking && response.length > 0

    return (
        <div>
            {hasThinking && (
                <ThinkingBlock
                    paragraphs={thinking}
                    isStillThinking={isStillThinking}
                    isStreaming={isStreaming && isLast}
                />
            )}
            {/* while still thinking and no response yet, show nothing for response */}
            {isStillThinking && !response && isStreaming && isLast ? null : (
                response ? (
                    <div className="chat-markdown">
                        <ReactMarkdown>{response}</ReactMarkdown>
                        {showCursor && (
                            <span className="inline-block w-1.5 h-4 bg-blue-400 ml-0.5 animate-pulse align-text-bottom" />
                        )}
                    </div>
                ) : (
                    isStreaming && isLast && !isStillThinking ? (
                        <span className="inline-block w-1.5 h-4 bg-blue-400 animate-pulse" />
                    ) : null
                )
            )}
        </div>
    )
}

export function LLMChatWindow() {
    const pathname = usePathname()
    const params = useParams()
    const {
        isChatOpen,
        toggleChat,
        messages,
        addMessage,
        updateLastMessage,
        clearMessages,
        isStreaming,
        setStreaming,
        chatPosition,
        setChatPosition,
        selectedProvider,
        selectedModel,
        setSelectedProvider,
        setSelectedModel,
    } = useUIStore()

    const [input, setInput] = React.useState('')
    const [isVisible, setIsVisible] = React.useState(false)
    const [isClosing, setIsClosing] = React.useState(false)
    const [showProviderMenu, setShowProviderMenu] = React.useState(false)
    const [enabledProviders, setEnabledProviders] = React.useState<EnabledProvider[]>([])
    const messagesEndRef = React.useRef<HTMLDivElement>(null)
    const headerRef = React.useRef<HTMLDivElement>(null)
    const providerMenuRef = React.useRef<HTMLDivElement>(null)
    const isDragging = React.useRef(false)
    const dragOffset = React.useRef({ x: 0, y: 0 })

    // fetch enabled providers on mount
    React.useEffect(() => {
        const fetchProviders = async () => {
            try {
                const authToken = useUIStore.getState().token
                const resp = await fetch(`${API_URL}/api/v1/settings/integrations`, {
                    headers: authToken ? { Authorization: `Bearer ${authToken}` } : {},
                })
                if (resp.ok) {
                    const data: EnabledProvider[] = await resp.json()
                    setEnabledProviders(data.filter(p =>
                        p.enabled && ['ollama', 'openai', 'claude', 'gemini'].includes(p.integration_type)
                    ))
                }
            } catch { /* silently ignore */ }
        }
        fetchProviders()
    }, [isChatOpen])

    // auto-scroll to bottom on new messages
    React.useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    // handle open/close animation
    React.useEffect(() => {
        if (isChatOpen) {
            setIsClosing(false)
            requestAnimationFrame(() => setIsVisible(true))
        }
    }, [isChatOpen])

    // close provider menu on outside click
    React.useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (providerMenuRef.current && !providerMenuRef.current.contains(e.target as Node)) {
                setShowProviderMenu(false)
            }
        }
        if (showProviderMenu) {
            document.addEventListener('mousedown', handler)
            return () => document.removeEventListener('mousedown', handler)
        }
    }, [showProviderMenu])

    // dragging handlers
    React.useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (!isDragging.current) return
            e.preventDefault()
            const newX = e.clientX - dragOffset.current.x
            const newY = e.clientY - dragOffset.current.y
            const clampedX = Math.max(0, Math.min(newX, window.innerWidth - 200))
            const clampedY = Math.max(0, Math.min(newY, window.innerHeight - 100))
            setChatPosition({ x: clampedX, y: clampedY })
        }

        const handleMouseUp = () => {
            if (isDragging.current) {
                isDragging.current = false
                document.body.style.userSelect = ''
            }
        }

        window.addEventListener('mousemove', handleMouseMove)
        window.addEventListener('mouseup', handleMouseUp)
        return () => {
            window.removeEventListener('mousemove', handleMouseMove)
            window.removeEventListener('mouseup', handleMouseUp)
        }
    }, [setChatPosition])

    const handleDragStart = (e: React.MouseEvent) => {
        if ((e.target as HTMLElement).closest('button')) return
        isDragging.current = true
        document.body.style.userSelect = 'none'

        if (chatPosition.x < 0 || chatPosition.y < 0) {
            const rect = headerRef.current?.parentElement?.getBoundingClientRect()
            if (rect) {
                dragOffset.current = {
                    x: e.clientX - rect.left,
                    y: e.clientY - rect.top,
                }
            }
        } else {
            dragOffset.current = {
                x: e.clientX - chatPosition.x,
                y: e.clientY - chatPosition.y,
            }
        }
    }

    const handleClose = () => {
        setIsClosing(true)
        setIsVisible(false)
        setTimeout(() => {
            toggleChat()
            setIsClosing(false)
        }, 200)
    }

    const handleSend = async () => {
        if (!input.trim() || isStreaming) return

        const userMsg = input.trim()
        setInput('')

        addMessage({
            id: Date.now().toString(),
            role: 'user',
            content: userMsg,
            createdAt: new Date().toISOString(),
        })

        const assistantId = (Date.now() + 1).toString()
        addMessage({
            id: assistantId,
            role: 'assistant',
            content: '',
            createdAt: new Date().toISOString(),
        })

        setStreaming(true)
        let accumulated = ''

        try {
            const context: { route: string; params?: Record<string, string> } = {
                route: pathname || '/',
            }
            if (params && typeof params === 'object') {
                const p: Record<string, string> = {}
                for (const [k, v] of Object.entries(params)) {
                    if (typeof v === 'string') p[k] = v
                }
                if (Object.keys(p).length > 0) context.params = p
            }

            const allMessages = [
                ...messages.filter((m: { role: string; content: string }) => m.role !== 'assistant' || m.content),
                { role: 'user' as const, content: userMsg },
            ].map((m: { role: string; content: string }) => ({
                role: m.role,
                // strip <think> blocks from assistant history so the LLM doesn't see its own reasoning
                content: m.role === 'assistant'
                    ? m.content.replace(/<think>[\s\S]*?<\/think>/g, '').trim()
                    : m.content,
            })).filter((m: { role: string; content: string }) => m.content)

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    messages: allMessages,
                    context,
                    provider: selectedProvider,
                    model: selectedModel,
                }),
            })

            if (!response.ok) {
                throw new Error(`Server error: ${response.status}`)
            }

            const reader = response.body?.getReader()
            if (!reader) throw new Error('No response body')

            const decoder = new TextDecoder()
            let buffer = ''

            while (true) {
                const { done, value } = await reader.read()
                if (done) break

                buffer += decoder.decode(value, { stream: true })
                const lines = buffer.split('\n')
                buffer = lines.pop() || ''

                for (const line of lines) {
                    const trimmed = line.trim()
                    if (!trimmed || !trimmed.startsWith('data: ')) continue

                    const data = trimmed.slice(6)
                    if (data === '[DONE]') continue

                    try {
                        const parsed = JSON.parse(data)
                        if (parsed.token) {
                            accumulated += parsed.token
                            updateLastMessage(accumulated)
                        }
                    } catch {
                        // skip malformed SSE lines
                    }
                }
            }

            if (buffer.trim()) {
                const trimmed = buffer.trim()
                if (trimmed.startsWith('data: ') && trimmed.slice(6) !== '[DONE]') {
                    try {
                        const parsed = JSON.parse(trimmed.slice(6))
                        if (parsed.token) {
                            accumulated += parsed.token
                            updateLastMessage(accumulated)
                        }
                    } catch { /* skip */ }
                }
            }

            if (!accumulated) {
                updateLastMessage('No response received from the LLM service.')
            }

        } catch (error) {
            console.error('Chat error:', error)
            const errMsg = error instanceof Error ? error.message : 'Unknown error'
            updateLastMessage(accumulated || `Connection error: ${errMsg}`)
        } finally {
            setStreaming(false)
        }
    }

    const getProviderLabel = () => {
        const p = LLM_PROVIDERS.find(x => x.value === selectedProvider)
        return p?.label || selectedProvider
    }

    const availableProviders = React.useMemo(() => {
        const enabled = new Set(enabledProviders.map(p => p.integration_type))
        enabled.add('ollama')
        return LLM_PROVIDERS.filter(p => enabled.has(p.value))
    }, [enabledProviders])

    // Gradient AI button when chat is closed
    if (!isChatOpen && !isClosing) {
        return (
            <button
                onClick={toggleChat}
                className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg z-50 flex items-center justify-center bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-600 hover:from-blue-400 hover:via-blue-500 hover:to-indigo-500 hover:scale-110 hover:shadow-blue-500/25 hover:shadow-xl transition-all duration-300 text-white"
            >
                <Bot className="h-6 w-6" />
            </button>
        )
    }

    const hasCustomPosition = chatPosition.x >= 0 && chatPosition.y >= 0
    const positionStyle: React.CSSProperties = hasCustomPosition
        ? { left: chatPosition.x, top: chatPosition.y, bottom: 'auto', right: 'auto' }
        : { bottom: 96, right: 24 }

    return (
        <div
            className={`fixed w-[400px] h-[600px] bg-black/60 backdrop-blur-2xl border border-white/10 rounded-2xl flex flex-col z-50 overflow-hidden shadow-2xl shadow-black/50 origin-bottom-right ${isVisible && !isClosing ? 'animate-chat-open' : isClosing ? 'animate-chat-close' : 'opacity-0 scale-50'}`}
            style={positionStyle}
        >
            <div
                ref={headerRef}
                onMouseDown={handleDragStart}
                className="flex items-center justify-between p-4 border-b border-white/5 bg-white/5 cursor-move select-none"
            >
                <div className="flex items-center gap-2">
                    <div className="h-2 w-2 rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 animate-pulse" />
                    <span className="font-medium text-sm text-white">Assistant</span>

                    {/* Provider dropdown */}
                    <div className="relative" ref={providerMenuRef}>
                        <button
                            onClick={() => setShowProviderMenu(!showProviderMenu)}
                            className="flex items-center gap-1 px-2 py-0.5 rounded-md text-xs bg-white/5 hover:bg-white/10 transition-colors text-muted-foreground hover:text-white"
                        >
                            {getProviderLabel()}
                            <ChevronDown className="h-3 w-3" />
                        </button>

                        {showProviderMenu && (
                            <div className="absolute top-full left-0 mt-1 w-40 bg-black/90 backdrop-blur-xl border border-white/10 rounded-lg shadow-xl z-[60] overflow-hidden">
                                {availableProviders.map(p => (
                                    <button
                                        key={p.value}
                                        onClick={() => {
                                            setSelectedProvider(p.value)
                                            const providerConfig = enabledProviders.find(
                                                ep => ep.integration_type === p.value
                                            )
                                            if (providerConfig?.config?.model) {
                                                setSelectedModel(providerConfig.config.model)
                                            }
                                            setShowProviderMenu(false)
                                        }}
                                        className={`w-full text-left px-3 py-2 text-sm hover:bg-white/10 transition-colors flex items-center justify-between ${selectedProvider === p.value ? 'text-blue-400' : 'text-gray-300'}`}
                                    >
                                        {p.label}
                                        {selectedProvider === p.value && (
                                            <div className="h-1.5 w-1.5 rounded-full bg-blue-400" />
                                        )}
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {isStreaming && (
                        <Loader2 className="h-3 w-3 animate-spin text-blue-400" />
                    )}
                </div>
                <div className="flex items-center gap-1">
                    <button
                        onClick={clearMessages}
                        title="Clear conversation"
                        className="hover:bg-white/10 p-1.5 rounded-full transition-colors text-muted-foreground hover:text-white"
                    >
                        <Trash2 className="h-3.5 w-3.5" />
                    </button>
                    <button onClick={handleClose} className="hover:bg-white/10 p-1.5 rounded-full transition-colors text-muted-foreground hover:text-white">
                        <Minus className="h-4 w-4" />
                    </button>
                    <button onClick={handleClose} className="hover:bg-white/10 p-1.5 rounded-full transition-colors text-muted-foreground hover:text-white">
                        <X className="h-4 w-4" />
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-hide">
                {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground space-y-2">
                        <div className="h-12 w-12 rounded-2xl bg-gradient-to-br from-blue-500/20 to-indigo-500/20 flex items-center justify-center mb-2">
                            <Send className="h-6 w-6 opacity-50" />
                        </div>
                        <p className="text-sm font-medium">How can I help you today?</p>
                        <p className="text-xs opacity-50">Ask about models, anomalies, alerts, cases, or anything in OpenUBA.</p>
                    </div>
                )}
                {messages.map((msg: ChatMessage, idx: number) => (
                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${msg.role === 'user'
                            ? 'bg-gradient-to-br from-blue-600 to-indigo-600 text-white rounded-br-none'
                            : 'bg-white/10 text-gray-100 rounded-bl-none'
                            }`}>
                            {msg.role === 'user' ? (
                                msg.content
                            ) : (
                                <AssistantContent
                                    content={msg.content}
                                    isStreaming={isStreaming}
                                    isLast={idx === messages.length - 1}
                                />
                            )}
                        </div>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            <div className="p-4 border-t border-white/5 bg-white/5">
                <div className="flex gap-2 relative">
                    <input
                        className="flex-1 bg-black/20 border border-white/10 rounded-full px-4 py-2.5 text-sm focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/50 transition-all placeholder:text-muted-foreground/50"
                        placeholder={isStreaming ? 'Waiting for response...' : 'Type a message...'}
                        value={input}
                        disabled={isStreaming}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                    />
                    <button
                        onClick={handleSend}
                        disabled={!input.trim() || isStreaming}
                        className="bg-gradient-to-br from-blue-600 to-indigo-600 text-white p-2.5 rounded-full hover:from-blue-500 hover:to-indigo-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isStreaming ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <Send className="h-4 w-4" />
                        )}
                    </button>
                </div>
            </div>
        </div>
    )
}
