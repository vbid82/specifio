import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

export function Login() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await api.post('/auth/login', { email })
      setSent(true)
    } catch (err) {
      setError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (sent) {
    return (
      <div className="mx-auto max-w-sm px-4 py-16">
        <h1 className="font-satoshi text-[24px] font-bold text-charcoal">
          Check your email
        </h1>
        <p className="mt-3 text-body text-slate">
          We sent a sign-in link to <span className="font-medium text-charcoal">{email}</span>.
          Click the link to continue.
        </p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-sm px-4 py-16">
      <h1 className="font-satoshi text-[24px] font-bold text-charcoal">
        Sign in
      </h1>
      <p className="mt-2 text-body text-slate">
        Enter your email to receive a sign-in link.
      </p>

      <div className="mt-6">
        <div className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-label text-slate">
              Email address
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded border border-warm-grey px-3 py-2 text-body text-charcoal focus:border-specifio-blue focus:outline-none focus:ring-1 focus:ring-specifio-blue"
              placeholder="you@yourfirm.com"
              required
            />
          </div>

          {error && (
            <p className="text-[13px] text-ember">{error}</p>
          )}

          <button
            type="button"
            onClick={handleSubmit}
            disabled={loading || !email}
            className="w-full rounded bg-specifio-blue px-4 py-2.5 text-[14px] font-medium text-white hover:bg-specifio-blue/90 disabled:opacity-50"
          >
            {loading ? 'Sending...' : 'Send sign-in link'}
          </button>
        </div>

        <p className="mt-6 text-center text-[13px] text-slate">
          New to Specifio?{' '}
          <Link to="/register" className="text-specifio-blue hover:underline">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  )
}
