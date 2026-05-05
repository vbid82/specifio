import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

export function Navbar() {
  const { isAuthenticated, specifier, logout } = useAuth()
  const location = useLocation()

  const isActive = (path: string) => location.pathname.startsWith(path)

  return (
    <nav className="border-b border-warm-grey bg-white">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-14 items-center justify-between">
          {/* Wordmark */}
          <Link
            to="/"
            className="font-satoshi text-xl font-bold tracking-wide text-charcoal"
            style={{ letterSpacing: '0.05em' }}
          >
            Specifio
          </Link>

          {/* Navigation */}
          <div className="flex items-center gap-6">
            <NavLink to="/catalog" active={isActive('/catalog')}>
              Catalog
            </NavLink>
            {isAuthenticated && (
              <NavLink to="/projects" active={isActive('/projects')}>
                Projects
              </NavLink>
            )}
            {isAuthenticated && specifier?.role === 'admin' && (
              <NavLink to="/admin" active={isActive('/admin')}>
                Admin
              </NavLink>
            )}

            {/* Auth */}
            {isAuthenticated ? (
              <div className="flex items-center gap-4">
                <Link
                  to="/account"
                  className="text-label text-slate hover:text-charcoal"
                >
                  {specifier?.first_name}
                </Link>
                <button
                  onClick={logout}
                  className="text-label text-slate hover:text-charcoal"
                >
                  Sign out
                </button>
              </div>
            ) : (
              <Link
                to="/login"
                className="rounded bg-specifio-blue px-4 py-1.5 text-[13px] font-medium text-white hover:bg-specifio-blue/90"
              >
                Sign in
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

function NavLink({
  to,
  active,
  children,
}: {
  to: string
  active: boolean
  children: React.ReactNode
}) {
  return (
    <Link
      to={to}
      className={`text-[14px] font-medium transition-colors ${
        active
          ? 'text-charcoal border-b-2 border-specifio-blue pb-[15px] -mb-[17px]'
          : 'text-slate hover:text-charcoal'
      }`}
    >
      {children}
    </Link>
  )
}
