import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AlertCircle, ArrowRight, CheckCircle2, Mail, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useAuth } from '@/hooks/useAuth'

export function ResendVerificationPage() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  const { resendOtp, isResendingOtp } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setFormError(null)

    if (!email.trim() || !email.includes('@')) {
      setFormError('Please enter a valid email address.')
      return
    }

    try {
      await resendOtp({ identifier: email.trim() })
      setSubmitted(true)
    } catch {
      // Handled by toast
    }
  }

  if (submitted) {
    return (
      <div className="space-y-6 text-center">
        <div className="mx-auto w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shadow-xs">
          <CheckCircle2 className="w-6 h-6" />
        </div>
        <div className="space-y-1.5">
          <h2 className="text-2xl font-bold tracking-tight text-[#211C17] dark:text-white">
            Verification code sent
          </h2>
          <p className="text-xs sm:text-sm text-[#71695F] dark:text-zinc-400">
            A new 6-digit verification code has been dispatched to <span className="font-semibold text-[#211C17] dark:text-white">{email}</span>.
          </p>
        </div>

        <Button
          type="button"
          variant="primary"
          size="lg"
          className="w-full justify-center font-semibold mt-2"
          rightIcon={<ArrowRight className="w-4 h-4" />}
          onClick={() => navigate('/verify-email', { state: { email } })}
        >
          Proceed to Verification
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 text-left">
      <div className="space-y-1.5 text-center">
        <div className="mx-auto w-10 h-10 rounded-2xl bg-[#EFE9E1] text-[#886F4E] dark:bg-white/[0.08] dark:text-[#A68A6A] flex items-center justify-center shadow-xs mb-2">
          <RefreshCw className="w-5 h-5" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-[#211C17] dark:text-white">
          Resend verification code
        </h2>
        <p className="text-xs sm:text-sm text-[#71695F] dark:text-zinc-400">
          Enter your email to receive a new 6-digit activation code
        </p>
      </div>

      {formError && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{formError}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
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
          required
        />

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full justify-center mt-2 font-semibold"
          isLoading={isResendingOtp}
          rightIcon={<ArrowRight className="w-4 h-4" />}
        >
          Send Verification Code
        </Button>
      </form>

      <div className="text-center pt-2 text-xs text-[#71695F] dark:text-zinc-400">
        Already have a code?{' '}
        <Link
          to="/verify-email"
          className="font-medium text-[#886F4E] hover:underline dark:text-[#A68A6A]"
        >
          Enter code
        </Link>
      </div>
    </div>
  )
}
