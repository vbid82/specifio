import { useAuth } from '../../contexts/AuthContext'

export function AdminDashboard() {
  const { specifier } = useAuth()

  if (specifier?.role !== 'admin') {
    return (
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <p className="text-body text-ember">Access denied.</p>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="font-satoshi text-[24px] font-bold text-charcoal">
        Admin Dashboard
      </h1>
      <p className="mt-2 text-body text-slate">
        Admin panel. Building next.
      </p>
    </div>
  )
}
