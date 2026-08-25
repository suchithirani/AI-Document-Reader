import React, { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { AlertCircle, ArrowRight, CheckCircle2, Edit2, KeyRound, Mail, RefreshCw } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { OtpInput } from '@/components/auth/OtpInput'
import { useAuth } from '@/hooks/useAuth'

export function VerifyEmailPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const initialEmail = (location.state as { email?: string })?.email || ''

  const [email, setEmail] = useState(initialEmail)
  const [isEditingEmail, setIsEditingEmail] = useState(!initialEmail)
  const [otp, setOtp] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [cooldown, setCooldown] = useState(0)
  const [isSuccess, setIsSuccess] = useState(false)

  const { verifyEmail, isVerifying, verifyError, resendOtp, isResendingOtp } = useAuth()

  // Cooldown countdown timer
  useEffect(() => {
    if (cooldown <= 0) return
    const timer = setInterval(() => {
      setCooldown((prev) => prev - 1)
    }, 1000)
    return () => clearInterval(timer)
  }, [cooldown])

  const maskEmail = (str: string) => {
    if (!str.includes('@')) return str
    const [local, domain] = str.split('@')
    if (local.length <= 2) return `${local[0]}*@${domain}`
    return `${local[0]}***${local.slice(-1)}@${domain}`
  }

  const handleVerify = async (e?: React.FormEvent, codeToVerify = otp) => {
    if (e) e.preventDefault()
    setFormError(null)

    if (!email.trim() || !email.includes('@')) {
      setFormError('Please provide a valid email address.')
      return
    }

    if (codeToVerify.length !== 6) {
      setFormError('Please enter the complete 6-digit verification code.')
      return
    }

    try {
      await verifyEmail({ identifier: email.trim(), otp: codeToVerify.trim() })
      setIsSuccess(true)
    } catch {
      // Handled by mutation toast & verifyError
    }
  }

  const handleResend = async () => {
    if (cooldown > 0 || isResendingOtp) return
    if (!email.trim() || !email.includes('@')) {
      setFormError('Please enter your email to resend the code.')
      return
    }

    try {
      await resendOtp({ identifier: email.trim() })
      setCooldown(60)
    } catch {
      // Handled by mutation toast
    }
  }

  const displayedError = formError || verifyError

  if (isSuccess) {
    return (
      <div className="space-y-6 text-center">
        <div className="mx-auto w-12 h-12 rounded-2xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shadow-xs">
          <CheckCircle2 className="w-6 h-6" />
        </div>
        <div className="space-y-1.5">
          <h2 className="text-2xl font-bold tracking-tight text-[#211C17] dark:text-white">
            Email Verified Successfully
          </h2>
          <p className="text-xs sm:text-sm text-[#71695F] dark:text-zinc-400">
            Your account is fully activated. You can now sign in to access your workspace.
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
          Proceed to Sign In
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6 text-left">
      <div className="space-y-1.5 text-center">
        <div className="mx-auto w-10 h-10 rounded-2xl bg-[#EFE9E1] text-[#886F4E] dark:bg-white/[0.08] dark:text-[#A68A6A] flex items-center justify-center shadow-xs mb-2">
          <KeyRound className="w-5 h-5" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-[#211C17] dark:text-white">
          Verify your email
        </h2>
        <p className="text-xs sm:text-sm text-[#71695F] dark:text-zinc-400">
          Enter the 6-digit verification code sent to your email
        </p>
      </div>

      {displayedError && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-700 dark:text-rose-400 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{displayedError}</span>
        </div>
      )}

      {/* Masked Email Indicator with Edit option */}
      {email && !isEditingEmail ? (
        <div className="p-3 rounded-xl bg-[rgba(255,255,255,0.60)] border border-[rgba(90,70,50,0.14)] dark:bg-white/[0.04] dark:border-white/[0.08] flex items-center justify-between text-xs">
          <div className="flex items-center gap-2 text-[#211C17] dark:text-zinc-200">
            <Mail className="w-3.5 h-3.5 text-[#886F4E] dark:text-[#A68A6A]" />
            <span className="font-medium font-mono">{maskEmail(email)}</span>
          </div>
          <button
            type="button"
            onClick={() => setIsEditingEmail(true)}
            className="inline-flex items-center gap-1 text-[#886F4E] hover:underline dark:text-[#A68A6A] font-medium cursor-pointer"
          >
            <Edit2 className="w-3 h-3" />
            <span>Change</span>
          </button>
        </div>
      ) : (
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
          disabled={isVerifying}
          required
        />
      )}

      <form noValidate onSubmit={(e) => handleVerify(e)} className="space-y-5">
        <div className="space-y-2">
          <label className="block text-center text-xs font-medium text-[#71695F] dark:text-zinc-400">
            Enter 6-Digit Code
          </label>
          <OtpInput
            value={otp}
            onChange={(val) => {
              setOtp(val)
              setFormError(null)
            }}
            onComplete={(val) => handleVerify(undefined, val)}
            disabled={isVerifying}
          />
        </div>

        <Button
          type="submit"
          variant="primary"
          size="lg"
          className="w-full justify-center font-semibold"
          isLoading={isVerifying}
          disabled={isVerifying || otp.length !== 6}
          rightIcon={<ArrowRight className="w-4 h-4" />}
        >
          Verify Email
        </Button>
      </form>

      {/* Resend OTP Section */}
      <div className="flex items-center justify-between pt-2 border-t border-[rgba(90,70,50,0.10)] dark:border-white/[0.08] text-xs">
        <span className="text-[#71695F] dark:text-zinc-400">
          Didn&apos;t receive code?
        </span>
        <button
          type="button"
          onClick={handleResend}
          disabled={cooldown > 0 || isResendingOtp}
          className="inline-flex items-center gap-1.5 font-medium text-[#886F4E] hover:text-[#705634] dark:text-[#A68A6A] dark:hover:text-[#C5A785] disabled:opacity-40 disabled:pointer-events-none cursor-pointer"
        >
          <RefreshCw className={`w-3 h-3 ${isResendingOtp ? 'animate-spin' : ''}`} />
          <span>{cooldown > 0 ? `Resend in ${cooldown}s` : 'Resend Code'}</span>
        </button>
      </div>

      <div className="text-center text-xs text-[#71695F] dark:text-zinc-400">
        Already verified?{' '}
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
