import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AlertCircle, ArrowLeft, ArrowRight, CheckCircle2, HelpCircle, Mail } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/hooks/useAuth'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const { forgotPassword, isSendingForgot } = useAuth()
  const navigate = useNavigate()

  const maskEmail = (str: string) => {
    if (!str.includes('@')) return str
    const [local, domain] = str.split('@')
    if (local.length <= 2) return `${local[0]}*@${domain}`
    return `${local[0]}***${local.slice(-1)}@${domain}`
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)

    if (!email.trim() || !email.includes('@')) {
      setFormError('Please enter a valid email address.')
      return
    }

    try {
      await forgotPassword({ identifier: email.trim() })
    } catch {
      // Intentionally suppressed for anti-enumeration security: Always show success confirmation
    }
    setSubmitted(true)
  }

  if (submitted) {
    return (
      <div className="space-y-6 text-center">
        <div className="mx-auto w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shadow-xs">
          <CheckCircle2 className="w-6 h-6" />
        </div>
        <div className="space-y-1.5">
          <h2 className="text-2xl font-bold tracking-tight text-[#211C17] dark:text-white">
            Check your email
          </h2>
          <p className="text-xs sm:text-sm text-[#71695F] dark:text-zinc-400">
            If an account exists for <span className="font-semibold text-[#211C17] dark:text-white font-mono">{maskEmail(email)}</span>, you will receive password reset instructions.
          </p>
        </div>

        <div className="space-y-3 pt-2">
          <Button
            type="button"
            variant="primary"
            size="lg"
            className="w-full justify-center font-semibold"
            rightIcon={<ArrowRight className="w-4 h-4" />}
            onClick={() => navigate('/reset-password', { state: { email } })}
          >
            Enter Reset Code
          </Button>

          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-[#71695F] hover:text-[#211C17] dark:text-zinc-400 dark:hover:text-white transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to sign in</span>
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 text-left">
      <div className="space-y-1.5 text-center">
        <div className="mx-auto w-10 h-10 rounded-2xl bg-[#EFE9E1] text-[#886F4E] dark:bg-white/[0.08] dark:text-[#A68A6A] flex items-center justify-center shadow-xs mb-2">
          <HelpCircle className="w-5 h-5" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-[#211C17] dark:text-white">
          Forgot your password?
        </h2>
        <p className="text-xs sm:text-sm text-[#71695F] dark:text-zinc-400">
          Enter your account email to receive password reset instructions
        </p>
      </div>

      {formError && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{formError}</span>
        </div>
      )}

      <form noValidate onSubmit={handleSubmit} className="space-y-4">
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
          disabled={isSendingForgot}
          required
        />

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full justify-center mt-2 font-semibold"
          isLoading={isSendingForgot}
          disabled={isSendingForgot}
          rightIcon={<ArrowRight className="w-4 h-4" />}
        >
          Send Reset Instructions
        </Button>
      </form>

      <div className="text-center pt-2 text-xs text-[#71695F] dark:text-zinc-400">
        Remembered your password?{' '}
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
