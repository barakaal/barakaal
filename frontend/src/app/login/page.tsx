'use client'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { authApi } from '@/lib/api'
import { setToken } from '@/lib/auth'
import { Zap, Mail, Lock, AlertCircle } from 'lucide-react'

const loginSchema = z.object({
  email: z.string().email('Email invalide'),
  password: z.string().min(1, 'Mot de passe requis'),
})

type LoginForm = z.infer<typeof loginSchema>

export default function LoginPage() {
  const router = useRouter()
  const [error, setError] = useState<string>('')
  const [loading, setLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  })

  const onSubmit = async (data: LoginForm) => {
    setLoading(true)
    setError('')
    try {
      const res = await authApi.login(data.email, data.password)
      const token = res.data.access_token
      setToken(token)
      router.push('/dashboard')
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } }
      setError(axiosErr?.response?.data?.detail || 'Email ou mot de passe incorrect')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-indigo-600/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-indigo-800/10 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-600 rounded-2xl mb-4 shadow-lg shadow-indigo-900/50">
            <Zap className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-100">AI Dropship OS</h1>
          <p className="text-gray-400 mt-2">Connectez-vous à votre espace admin</p>
        </div>

        {/* Card */}
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 shadow-2xl">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            {/* Email */}
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-300">
                Adresse email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input
                  {...register('email')}
                  type="email"
                  placeholder="admin@company.com"
                  autoComplete="email"
                  className="input-dark w-full pl-10"
                />
              </div>
              {errors.email && (
                <p className="text-xs text-red-400 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  {errors.email.message}
                </p>
              )}
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-gray-300">
                Mot de passe
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input
                  {...register('password')}
                  type="password"
                  placeholder="••••••••"
                  autoComplete="current-password"
                  className="input-dark w-full pl-10"
                />
              </div>
              {errors.password && (
                <p className="text-xs text-red-400 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" />
                  {errors.password.message}
                </p>
              )}
            </div>

            {/* Error message */}
            {error && (
              <div className="bg-red-900/30 border border-red-800 rounded-lg px-4 py-3 flex items-start gap-2">
                <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold py-3 px-4 rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-gray-900"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Connexion...
                </>
              ) : (
                'Se connecter'
              )}
            </button>
          </form>

          {/* Demo hint */}
          <div className="mt-6 pt-6 border-t border-gray-800">
            <p className="text-xs text-gray-500 text-center">
              Demo: <span className="text-gray-400">admin@company.com</span> / <span className="text-gray-400">admin</span>
            </p>
          </div>
        </div>

        <p className="text-center text-xs text-gray-600 mt-6">
          AI Dropship Company OS &copy; 2025 — Tous droits réservés
        </p>
      </div>
    </div>
  )
}
