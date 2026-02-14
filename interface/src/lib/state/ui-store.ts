import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type ChatMessageRole = 'user' | 'assistant' | 'system';
export type ChatMessage = { id: string; role: ChatMessageRole; content: string; createdAt: string };

export type CurrentUser = {
  id: string
  username: string
  role: string
  email?: string | null
  display_name?: string | null
  permissions: Record<string, { read: boolean; write: boolean }>
}

interface UIState {
  isSidebarOpen: boolean
  toggleSidebar: () => void

  // Auth state
  token: string | null
  currentUser: CurrentUser | null
  setAuth: (token: string, user: CurrentUser) => void
  logout: () => void
  hasPermission: (page: string, access?: 'read' | 'write') => boolean

  // Chat state
  isChatOpen: boolean
  toggleChat: () => void
  chatPosition: { x: number; y: number }
  chatSize: { width: number; height: number }
  setChatPosition: (pos: { x: number; y: number }) => void
  setChatSize: (size: { width: number; height: number }) => void
  messages: ChatMessage[]
  addMessage: (msg: ChatMessage) => void
  updateLastMessage: (content: string) => void
  clearMessages: () => void
  isStreaming: boolean
  setStreaming: (v: boolean) => void
  activeThreadId: string | null
  setActiveThreadId: (id: string | null) => void

  // LLM provider selection
  selectedProvider: string
  selectedModel: string
  setSelectedProvider: (p: string) => void
  setSelectedModel: (m: string) => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set, get) => ({
      isSidebarOpen: true,
      toggleSidebar: () => set((state: UIState) => ({ isSidebarOpen: !state.isSidebarOpen })),

      // Auth
      token: null as string | null,
      currentUser: null as CurrentUser | null,
      setAuth: (token: string, user: CurrentUser) => set({ token, currentUser: user }),
      logout: () => set({ token: null, currentUser: null }),
      hasPermission: (page: string, access: 'read' | 'write' = 'read'): boolean => {
        const user = get().currentUser
        if (!user) return false
        if (user.role === 'admin') return true
        const perm = user.permissions?.[page]
        if (!perm) return false
        return access === 'write' ? perm.write : perm.read
      },

      isChatOpen: false,
      toggleChat: () => set((state: UIState) => ({ isChatOpen: !state.isChatOpen })),
      chatPosition: { x: -1, y: -1 },
      chatSize: { width: 420, height: 520 },
      setChatPosition: (pos: { x: number; y: number }) => set({ chatPosition: pos }),
      setChatSize: (size: { width: number; height: number }) => set({ chatSize: size }),
      messages: [] as ChatMessage[],
      addMessage: (msg: ChatMessage) => set((state: UIState) => ({ messages: [...state.messages, msg] })),
      updateLastMessage: (content: string) => set((state: UIState) => {
        if (state.messages.length === 0) return state
        const updated = [...state.messages]
        updated[updated.length - 1] = { ...updated[updated.length - 1], content }
        return { messages: updated }
      }),
      clearMessages: () => set({ messages: [] }),
      isStreaming: false,
      setStreaming: (v: boolean) => set({ isStreaming: v }),
      activeThreadId: null as string | null,
      setActiveThreadId: (id: string | null) => set({ activeThreadId: id }),

      selectedProvider: 'ollama',
      selectedModel: 'lfm2.5-thinking',
      setSelectedProvider: (p: string) => set({ selectedProvider: p }),
      setSelectedModel: (m: string) => set({ selectedModel: m }),
    }),
    {
      name: 'openuba-ui-storage',
    }
  )
)
