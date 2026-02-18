import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '@/styles/globals.css'
import { ToastProvider } from '@/components/global/toast-provider'
import { ApolloWrapper } from '@/lib/apollo-provider'
import { ThemeProvider } from '@/lib/theme'
import { AuthProvider } from '@/lib/auth-provider'
import { AuthGate } from '@/components/layout/auth-gate'
import { AuthenticatedShell } from '@/components/layout/authenticated-shell'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
    title: 'OpenUBA',
    description: 'User and Entity Behavior Analytics',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="en" suppressHydrationWarning>
            <body className={inter.className}>
                <ThemeProvider defaultTheme="dark" storageKey="openuba-ui-theme">
                    <ApolloWrapper>
                        <AuthProvider>
                            <ToastProvider>
                                <AuthGate>
                                    <AuthenticatedShell>
                                        {children}
                                    </AuthenticatedShell>
                                </AuthGate>
                            </ToastProvider>
                        </AuthProvider>
                    </ApolloWrapper>
                </ThemeProvider>
            </body>
        </html>
    )
}
