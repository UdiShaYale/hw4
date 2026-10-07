import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import type { User } from './types'

/**
 * Minimal client-side session: the backend verifies the password and hands back
 * the user row, and we remember it so the nav can greet them. No tokens yet —
 * nothing behind the login is protected.
 */
const STORAGE_KEY = 'campus-customs-user'

interface AuthValue {
  user: User | null
  signIn: (user: User) => void
  signOut: () => void
}

const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (!saved) return null
    try {
      return JSON.parse(saved) as User
    } catch {
      return null
    }
  })

  useEffect(() => {
    if (user) localStorage.setItem(STORAGE_KEY, JSON.stringify(user))
    else localStorage.removeItem(STORAGE_KEY)
  }, [user])

  const value = useMemo<AuthValue>(
    () => ({ user, signIn: setUser, signOut: () => setUser(null) }),
    [user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>')
  return context
}
