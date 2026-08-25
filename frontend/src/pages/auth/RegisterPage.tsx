import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AlertCircle, ArrowRight, Mail, User } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { PasswordInput } from '@/components/auth/PasswordInput'
import { useAuth } from '@/hooks/useAuth'

export function RegisterPage() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const { register, isRegistering, registerError } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)

    if (name.trim().length < 2) {
      setFormError('Name must be at least 2 characters.')
      return
    }

    if (!email.trim() || !email.includes('@')) {
      setFormError('Please enter a valid email address.')
      return
    }

    if (password.length < 8) {
      setFormError('Password must be at least 8 characters.')
      return
    }

    if (password !== confirmPassword) {
      setFormError('Passwords do not match.')
      return
    }

    try {
      await register({
        name: name.trim(),
        email: email.trim(),
        password,
      })
      navigate('/verify-email', { state: { email: email.trim() } })
    } catch (err: unknown) {
      // If the email is already registered, present a security-conscious helpful message
      const errMsg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message || ''
      if (errMsg.toLowerCase().includes('already') || errMsg.toLowerCase().includes('registered') || errMsg.toLowerCase().includes('exist')) {
        setFormError('If you can’t create an account with this email, it may already be registered. Try signing in or resetting your password.')
      }
    }
  }

  const displayedError = formError || registerError

  return (
    <div className="space-y-6 text-left">
      <div className="space-y-1.5 text-center">
        <h2 className="text-2xl font-bold tracking-tight text-[#211C17] dark:text-white">
          Create an account
        </h2>
        <p className="text-xs sm:text-sm text-[#71695F] dark:text-zinc-400">
          Sign up to begin indexing and querying intelligence documents
        </p>
      </div>

      {displayedError && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="leading-relaxed">{displayedError}</p>
            {displayedError.includes('already be registered') && (
              <div className="flex gap-3 pt-1 text-[11px] font-semibold">
                <Link to="/login" className="underline hover:text-rose-900 dark:hover:text-rose-200">
                  Sign in instead
                </Link>
                <Link to="/forgot-password" className="underline hover:text-rose-900 dark:hover:text-rose-200">
                  Reset password
                </Link>
              </div>
            )}
          </div>
        </div>
      )}

      <form noValidate onSubmit={handleSubmit} className="space-y-3.5">
        <Input
          label="Full name"
          type="text"
          name="name"
          autoComplete="name"
          placeholder="Jane Doe"
          leftIcon={<User className="w-4 h-4 text-[#9A9187] dark:text-zinc-500" />}
          value={name}
          onChange={(e) => {
            setName(e.target.value)
            setFormError(null)
          }}
          disabled={isRegistering}
          required
        />

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
          disabled={isRegistering}
          required
        />

        <PasswordInput
          label="Password"
          name="password"
          autoComplete="new-password"
          placeholder="At least 8 characters"
          value={password}
          showStrengthMeter
          onChange={(e) => {
            setPassword(e.target.value)
            setFormError(null)
          }}
          disabled={isRegistering}
          required
        />

        <PasswordInput
          label="Confirm Password"
          name="confirmPassword"
          autoComplete="new-password"
          placeholder="Repeat password"
          value={confirmPassword}
          onChange={(e) => {
            setConfirmPassword(e.target.value)
            setFormError(null)
          }}
          disabled={isRegistering}
          required
        />

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full justify-center mt-2 font-semibold"
          isLoading={isRegistering}
          disabled={isRegistering}
          rightIcon={<ArrowRight className="w-4 h-4" />}
        >
          Create Account
        </Button>
      </form>

      <div className="text-center pt-2 text-xs text-[#71695F] dark:text-zinc-400">
        Already have an account?{' '}
        <Link
          to="/login"
          className="font-medium text-[#886F4E] hover:underline dark:text-[#A68A6A]"
        >
          Sign in
        </Link>
      </div>
    </div>
  )
}
