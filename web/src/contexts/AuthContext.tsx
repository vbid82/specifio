import { createContext, useContext, useState, useEffect } from 'react'
import type { ReactNode } from 'react'
import { api, ApiError } from '../lib/api'
import type { Specifier } from '../types'

interface AuthContextType {
  specifier: Specifier | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (token: string) => void
  logout: () => void
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [specifier, setSpecifier] = useState<Specifier | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  const refresh = async () => {
    try {
      const data = await api.get<Specifier>('/auth/me')
      setSpecifier(data)
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        localStorage.removeItem('specifio_token')
        setSpecifier(null)
      }
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    const token = localStorage.getItem('specifio_token')
    if (token) {
      refresh()
    } else {
      setIsLoading(false)
    }
  }, [])

  const login = (token: string) => {
    localStorage.setItem('specifio_token', token)
    refresh()
  }

  const logout = () => {
    localStorage.removeItem('specifio_token')
    setSpecifier(null)
  }

  return (
    <AuthContext.Provider
      value={{
        specifier,
        isLoading,
        isAuthenticated: !!specifier,
        login,
        logout,
        refresh,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
