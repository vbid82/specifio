import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuth } from '../contexts/AuthContext'
import type { TokenResponse } from '../types'

export function AuthVerify() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { login } = useAuth()
  const [error, setError] = useState('')

  useEffect(() => {
    const token = searchParams.get('token')
    if (!token) {
      setError('Invalid verification link.')
      return
    }

    const verify = async () => {
      try {
        const data = await api.get<TokenResponse>(`/auth/verify?token=${token}`)
        login(data.access_token)
        navigate('/catalog', { replace: true })
      } catch {
        setError('This link has expired or already been used. Please request a new one.')
      }
    }

    verify()
  }, [searchParams, login, navigate])

  if (error) {
    return (
      <div className="mx-auto max-w-sm px-4 py-16">
        <h1 className="font-satoshi text-[24px] font-bold text-charcoal">
          Verification failed
        </h1>
        <p className="mt-3 text-body text-slate">{error}</p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-sm px-4 py-16">
      <p className="text-body text-slate">Verifying your link...</p>
    </div>
  )
}
