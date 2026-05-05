import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../lib/api'

export function Register() {
  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    firm_name: '',
    role: '',
  })
  const [sent, setSent] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await api.post('/auth/register', formData)
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
          We sent a verification link to{' '}
          <span className="font-medium text-charcoal">{formData.email}</span>.
          Click the link to complete your registration.
        </p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-sm px-4 py-16">
      <h1 className="font-satoshi text-[24px] font-bold text-charcoal">
        Create an account
      </h1>
      <p className="mt-2 text-body text-slate">
        Register to access trade pricing, project tools, and sample requests.
      </p>

      <div className="mt-6 space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label htmlFor="first_name" className="block text-label text-slate">
              First name
            </label>
            <input
              id="first_name"
              name="first_name"
              type="text"
              value={formData.first_name}
              onChange={handleChange}
              className="mt-1 w-full rounded border border-warm-grey px-3 py-2 text-body text-charcoal focus:border-specifio-blue focus:outline-none focus:ring-1 focus:ring-specifio-blue"
              required
            />
          </div>
          <div>
            <label htmlFor="last_name" className="block text-label text-slate">
              Last name
            </label>
            <input
              id="last_name"
              name="last_name"
              type="text"
              value={formData.last_name}
              onChange={handleChange}
              className="mt-1 w-full rounded border border-warm-grey px-3 py-2 text-body text-charcoal focus:border-specifio-blue focus:outline-none focus:ring-1 focus:ring-specifio-blue"
              required
            />
          </div>
        </div>

        <div>
          <label htmlFor="email" className="block text-label text-slate">
            Work email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            value={formData.email}
            onChange={handleChange}
            className="mt-1 w-full rounded border border-warm-grey px-3 py-2 text-body text-charcoal focus:border-specifio-blue focus:outline-none focus:ring-1 focus:ring-specifio-blue"
            placeholder="you@yourfirm.com"
            required
          />
        </div>

        <div>
          <label htmlFor="firm_name" className="block text-label text-slate">
            Firm name
          </label>
          <input
            id="firm_name"
            name="firm_name"
            type="text"
            value={formData.firm_name}
            onChange={handleChange}
            className="mt-1 w-full rounded border border-warm-grey px-3 py-2 text-body text-charcoal focus:border-specifio-blue focus:outline-none focus:ring-1 focus:ring-specifio-blue"
            required
          />
        </div>

        <div>
          <label htmlFor="role" className="block text-label text-slate">
            Your role
          </label>
          <input
            id="role"
            name="role"
            type="text"
            value={formData.role}
            onChange={handleChange}
            className="mt-1 w-full rounded border border-warm-grey px-3 py-2 text-body text-charcoal focus:border-specifio-blue focus:outline-none focus:ring-1 focus:ring-specifio-blue"
            placeholder="Interior designer, architect, FF&E manager..."
            required
          />
        </div>

        {error && <p className="text-[13px] text-ember">{error}</p>}

        <button
          type="button"
          onClick={handleSubmit}
          disabled={
            loading ||
            !formData.email ||
            !formData.first_name ||
            !formData.last_name ||
            !formData.firm_name ||
            !formData.role
          }
          className="w-full rounded bg-specifio-blue px-4 py-2.5 text-[14px] font-medium text-white hover:bg-specifio-blue/90 disabled:opacity-50"
        >
          {loading ? 'Creating account...' : 'Create account'}
        </button>
      </div>

      <p className="mt-6 text-center text-[13px] text-slate">
        Already have an account?{' '}
        <Link to="/login" className="text-specifio-blue hover:underline">
          Sign in
        </Link>
      </p>
    </div>
  )
}
