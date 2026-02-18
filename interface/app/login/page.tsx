'use client'

import * as React from 'react'
import { useAuth } from '@/lib/auth-provider'
import { useRouter } from 'next/navigation'
import { Eye, EyeOff, Loader2 } from 'lucide-react'

export default function LoginPage() {
  const { login, user } = useAuth()
  const router = useRouter()
  const [username, setUsername] = React.useState('')
  const [password, setPassword] = React.useState('')
  const [showPassword, setShowPassword] = React.useState(false)
  const [error, setError] = React.useState('')
  const [isLoading, setIsLoading] = React.useState(false)
  const [shake, setShake] = React.useState(false)

  React.useEffect(() => {
    if (user) router.replace('/')
  }, [user, router])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)
    try {
      await login(username, password)
      router.replace('/')
    } catch (err: any) {
      setError(err.message || 'login failed')
      setShake(true)
      setTimeout(() => setShake(false), 500)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-[#0a0a1a]">
      {/* animated background */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="login-bg-gradient" />
        <div className="login-shape login-shape-1" />
        <div className="login-shape login-shape-2" />
        <div className="login-shape login-shape-3" />
        <div className="login-shape login-shape-4" />
        <div className="login-shape login-shape-5" />
        <div className="login-grid" />
      </div>

      {/* login card */}
      <div
        className={`relative z-10 w-full max-w-md mx-4 ${shake ? 'animate-shake' : ''}`}
      >
        <div className="backdrop-blur-xl bg-white/[0.07] border border-white/[0.12] rounded-2xl shadow-2xl p-8">
          {/* logo */}
          <div className="flex flex-col items-center mb-8">
            <img
              src="/images/openuba-logo-light.png"
              alt="OpenUBA"
              className="h-12 w-auto object-contain mb-4"
            />
            <p className="text-sm text-white/50 mt-1">User & Entity Behavior Analytics</p>
          </div>

          <h2 className="text-lg font-semibold text-white/90 text-center mb-6">Sign in to your account</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-medium text-white/60 uppercase tracking-wider mb-1.5 block">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full h-11 px-4 rounded-lg bg-white/[0.06] border border-white/[0.1] text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/25 transition-colors"
                placeholder="Enter username"
                autoFocus
                autoComplete="username"
                required
              />
            </div>

            <div>
              <label className="text-xs font-medium text-white/60 uppercase tracking-wider mb-1.5 block">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full h-11 px-4 pr-11 rounded-lg bg-white/[0.06] border border-white/[0.1] text-white placeholder-white/30 focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/25 transition-colors"
                  placeholder="Enter password"
                  autoComplete="current-password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/70 transition-colors"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {error && (
              <div className="text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-lg px-4 py-2.5 text-center">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading || !username || !password}
              className="w-full h-11 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-medium hover:from-cyan-400 hover:to-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 shadow-lg shadow-cyan-500/20"
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-white/30 mt-6">OpenUBA v0.0.2</p>
      </div>

      <style jsx>{`
        .login-bg-gradient {
          position: absolute;
          inset: 0;
          background: radial-gradient(ellipse 80% 60% at 50% 0%, rgba(14, 165, 233, 0.12), transparent),
                      radial-gradient(ellipse 60% 40% at 80% 80%, rgba(59, 130, 246, 0.08), transparent),
                      radial-gradient(ellipse 50% 30% at 20% 60%, rgba(6, 182, 212, 0.06), transparent);
        }
        .login-grid {
          position: absolute;
          inset: 0;
          background-image: linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
                            linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
          background-size: 60px 60px;
        }
        .login-shape {
          position: absolute;
          border-radius: 50%;
          opacity: 0.08;
          filter: blur(40px);
        }
        .login-shape-1 {
          width: 300px; height: 300px;
          background: #06b6d4;
          top: -100px; left: -50px;
          animation: float1 20s ease-in-out infinite;
        }
        .login-shape-2 {
          width: 200px; height: 200px;
          background: #3b82f6;
          top: 30%; right: -40px;
          animation: float2 25s ease-in-out infinite;
        }
        .login-shape-3 {
          width: 250px; height: 250px;
          background: #8b5cf6;
          bottom: -80px; left: 30%;
          animation: float3 22s ease-in-out infinite;
        }
        .login-shape-4 {
          width: 150px; height: 150px;
          background: #06b6d4;
          top: 60%; left: -30px;
          animation: float2 18s ease-in-out infinite reverse;
        }
        .login-shape-5 {
          width: 180px; height: 180px;
          background: #3b82f6;
          top: 10%; right: 15%;
          animation: float1 23s ease-in-out infinite reverse;
        }
        @keyframes float1 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          33% { transform: translate(30px, -30px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
        }
        @keyframes float2 {
          0%, 100% { transform: translate(0, 0) rotate(0deg); }
          50% { transform: translate(-40px, 30px) rotate(180deg); }
        }
        @keyframes float3 {
          0%, 100% { transform: translate(0, 0) scale(1); }
          50% { transform: translate(30px, -40px) scale(1.15); }
        }
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
          20%, 40%, 60%, 80% { transform: translateX(4px); }
        }
        .animate-shake {
          animation: shake 0.5s ease-in-out;
        }
      `}</style>
    </div>
  )
}
