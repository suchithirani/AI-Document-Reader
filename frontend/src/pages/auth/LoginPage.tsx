import React, { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { AlertCircle, ArrowRight, Mail } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { PasswordInput } from '@/components/auth/PasswordInput'
import { useAuth } from '@/hooks/useAuth'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const { login, isLoggingIn, loginError } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)

    if (!email.trim() || !email.includes('@')) {
      setFormError('Please enter a valid email address.')
      return
    }

    if (!password || password.length < 8) {
      setFormError('Password must be at least 8 characters.')
      return
    }

    try {
      const data = await login({ email: email.trim(), password })
      if (data.user && !data.user.is_verified) {
        navigate('/verify-email', { state: { email: email.trim() } })
      } else {
        navigate(from, { replace: true })
      }
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message || ''

      // If backend reports email is unverified (status 403)
      if (status === 403 || msg.toLowerCase().includes('verify')) {
        navigate('/verify-email', { state: { email: email.trim() } })
        return
      }

      // Security requirement: concise generic error
      setFormError('Invalid email or password. Please check your credentials and try again.')
    }
  }

  const displayedError = formError || loginError

  return (
    <div className="space-y-6 text-left">
      <div className="space-y-1.5 text-center">
        <h2 className="text-2xl font-bold tracking-tight text-[#211C17] dark:text-white">
          Sign in to your account
        </h2>
        <p className="text-xs sm:text-sm text-[#71695F] dark:text-zinc-400">
          Enter your email and password to access the workspace
        </p>
      </div>

      {displayedError && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{displayedError}</span>
        </div>
      )}

      <form noValidate onSubmit={handleSubmit} className="space-y-4">
        <Input
          label="Email address"
          type="email"
          name="email"
          autoComplete="email"
          placeholder="name@company.com"
          leftIcon={<Mail className="w-4 h-4 text-[#9A9187] dark:text-zinc-500" />}
          value={email}
          onChange={(e) => {
            setEmail(e.target.value)
            setFormError(null)
          }}
          disabled={isLoggingIn}
          required
        />

        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-[#71695F] dark:text-zinc-400">
              Password
            </label>
            <Link
              to="/forgot-password"
              className="text-xs font-medium text-[#886F4E] hover:text-[#705634] dark:text-[#A68A6A] dark:hover:text-[#C5A785] transition-colors"
            >
              Forgot password?
            </Link>
          </div>
          <PasswordInput
            name="password"
            autoComplete="current-password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value)
              setFormError(null)
            }}
            disabled={isLoggingIn}
            required
          />
        </div>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full justify-center mt-2 font-semibold"
          isLoading={isLoggingIn}
          disabled={isLoggingIn}
          rightIcon={<ArrowRight className="w-4 h-4" />}
        >
          Sign In
        </Button>
      </form>

      <div className="text-center pt-2 text-xs text-[#71695F] dark:text-zinc-400">
        Don&apos;t have an account?{' '}
        <Link
          to="/register"
          className="font-medium text-[#886F4E] hover:underline dark:text-[#A68A6A]"
        >
          Create account
        </Link>
      </div>
    </div>
  )
}
