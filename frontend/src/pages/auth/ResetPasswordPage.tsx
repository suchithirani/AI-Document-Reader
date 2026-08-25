import React, { useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { AlertCircle, ArrowRight, CheckCircle2, Mail, ShieldCheck } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { PasswordInput } from '@/components/auth/PasswordInput'
import { useAuth } from '@/hooks/useAuth'

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const location = useLocation()
  const navigate = useNavigate()

  const queryToken = searchParams.get('token') || searchParams.get('otp') || ''
  const queryEmail = searchParams.get('email') || searchParams.get('identifier') || ''
  const stateEmail = (location.state as { email?: string })?.email || ''

  const [email, setEmail] = useState(queryEmail || stateEmail)
  const [otp, setOtp] = useState(queryToken)
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [isSuccess, setIsSuccess] = useState(false)

  const { resetPassword, isResettingPassword, resetError } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)

    if (!email.trim() || !email.includes('@')) {
      setFormError('Please enter a valid email address.')
      return
    }

    if (!otp.trim() || otp.trim().length < 6) {
      setFormError('Please provide the 6-digit reset code.')
      return
    }

    if (password.length < 8) {
      setFormError('New password must be at least 8 characters.')
      return
    }

    if (password !== confirmPassword) {
      setFormError('Passwords do not match.')
      return
    }

    try {
      await resetPassword({
        identifier: email.trim(),
        otp: otp.trim(),
        new_password: password,
      })
      setIsSuccess(true)
    } catch {
      // Handled by mutation toast & resetError
    }
  }

  const displayedError = formError || resetError

  if (isSuccess) {
    return (
      <div className="space-y-6 text-center">
        <div className="mx-auto w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shadow-xs">
          <CheckCircle2 className="w-6 h-6" />
        </div>
        <div className="space-y-1.5">
          <h2 className="text-2xl font-bold tracking-tight text-[#211C17] dark:text-white">
            Password reset complete
          </h2>
          <p className="text-xs sm:text-sm text-[#71695F] dark:text-zinc-400">
            Your password has been securely updated. You can now sign in with your new credentials.
          </p>
        </div>

        <Button
          type="button"
          variant="primary"
          size="lg"
          className="w-full justify-center font-semibold mt-2"
          rightIcon={<ArrowRight className="w-4 h-4" />}
          onClick={() => navigate('/login', { replace: true })}
        >
          Sign In Now
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 text-left">
      <div className="space-y-1.5 text-center">
        <div className="mx-auto w-10 h-10 rounded-2xl bg-[#EFE9E1] text-[#886F4E] dark:bg-white/[0.08] dark:text-[#A68A6A] flex items-center justify-center shadow-xs mb-2">
          <ShieldCheck className="w-5 h-5" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-[#211C17] dark:text-white">
          Reset your password
        </h2>
        <p className="text-xs sm:text-sm text-[#71695F] dark:text-zinc-400">
          Enter your verification code and choose a new password
        </p>
      </div>

      {displayedError && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{displayedError}</span>
        </div>
      )}

      <form noValidate onSubmit={handleSubmit} className="space-y-3.5">
        <Input
          label="Email address"
          type="email"
          name="email"
          placeholder="name@company.com"
          leftIcon={<Mail className="w-4 h-4 text-[#9A9187] dark:text-zinc-500" />}
          value={email}
          onChange={(e) => {
            setEmail(e.target.value)
            setFormError(null)
          }}
          disabled={isResettingPassword}
          required
        />

        <div className="space-y-1.5">
          <label className="text-xs font-medium text-[#71695F] dark:text-zinc-400">
            6-Digit Reset Code (OTP)
          </label>
          <input
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={6}
            placeholder="123456"
            value={otp}
            onChange={(e) => {
              const val = e.target.value.replace(/\D/g, '')
              setOtp(val)
              setFormError(null)
            }}
            disabled={isResettingPassword}
            className="w-full h-10 px-3.5 text-center tracking-[0.4em] font-mono text-base rounded-xl border bg-[#FFFCF8] hover:bg-[#FFFFFF] focus:bg-[#FFFFFF] dark:bg-white/[0.04] border-[rgba(90,70,50,0.18)] dark:border-white/[0.1] text-[#211C17] dark:text-white focus:outline-none focus:ring-2 focus:ring-[#886F4E]/20 dark:focus:ring-white/10 transition-all"
            required
          />
        </div>

        <PasswordInput
          label="New Password"
          name="password"
          autoComplete="new-password"
          placeholder="At least 8 characters"
          value={password}
          showStrengthMeter
          onChange={(e) => {
            setPassword(e.target.value)
            setFormError(null)
          }}
          disabled={isResettingPassword}
          required
        />

        <PasswordInput
          label="Confirm New Password"
          name="confirmPassword"
          autoComplete="new-password"
          placeholder="Repeat new password"
          value={confirmPassword}
          onChange={(e) => {
            setConfirmPassword(e.target.value)
            setFormError(null)
          }}
          disabled={isResettingPassword}
          required
        />

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full justify-center mt-2 font-semibold"
          isLoading={isResettingPassword}
          disabled={isResettingPassword}
          rightIcon={<ArrowRight className="w-4 h-4" />}
        >
          Update Password
        </Button>
      </form>

      <div className="text-center pt-2 text-xs text-[#71695F] dark:text-zinc-400">
        Remembered password?{' '}
        <Link
          to="/login"
          className="font-medium text-[#886F4E] hover:underline dark:text-[#A68A6A]"
        >
          Return to sign in
        </Link>
      </div>
    </div>
  )
}
