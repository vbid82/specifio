import { useAuth } from '../contexts/AuthContext'

export function Account() {
  const { specifier } = useAuth()

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="font-satoshi text-[24px] font-bold text-charcoal">
        Account
      </h1>
      {specifier && (
        <div className="mt-4 text-body text-slate">
          <p>{specifier.first_name} {specifier.last_name}</p>
          <p>{specifier.email}</p>
          <p>{specifier.firm_name}</p>
        </div>
      )}
    </div>
  )
}
