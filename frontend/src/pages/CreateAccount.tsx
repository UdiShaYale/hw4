import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuth } from '../lib/auth'

export function CreateAccount() {
  const { signIn } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirm_password: '',
  })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const update = (field: keyof typeof form) => (event: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [field]: event.target.value }))

  // Shown under the field as the shopper types; the backend checks this too.
  const mismatch =
    form.confirm_password.length > 0 && form.password !== form.confirm_password

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (form.password !== form.confirm_password) {
      setError('Passwords do not match.')
      return
    }
    setBusy(true)
    setError('')
    try {
      // The backend hashes the password and returns the new row; sign in with it.
      signIn(await api.signup(form))
      navigate('/')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create the account.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="page">
      <div className="auth">
        <h1>Create Account</h1>
        <p className="muted">One account for orders, sizes and saved favourites.</p>

        {error && <div className="alert error">{error}</div>}

        <form onSubmit={submit}>
          <div className="row">
            <div className="field">
              <label htmlFor="first">First name</label>
              <input id="first" required value={form.first_name} onChange={update('first_name')} />
            </div>
            <div className="field">
              <label htmlFor="last">Last name</label>
              <input id="last" required value={form.last_name} onChange={update('last_name')} />
            </div>
          </div>

          <div className="field">
            <label htmlFor="newemail">Email</label>
            <input
              id="newemail"
              type="email"
              required
              value={form.email}
              onChange={update('email')}
              placeholder="you@yale.edu"
              autoComplete="email"
            />
          </div>

          <div className="field">
            <label htmlFor="newpassword">Password</label>
            <input
              id="newpassword"
              type="password"
              required
              minLength={8}
              value={form.password}
              onChange={update('password')}
              autoComplete="new-password"
            />
            <small className="muted">At least 8 characters.</small>
          </div>

          <div className="field">
            <label htmlFor="confirmpassword">Confirm password</label>
            <input
              id="confirmpassword"
              type="password"
              required
              minLength={8}
              value={form.confirm_password}
              onChange={update('confirm_password')}
              autoComplete="new-password"
              aria-invalid={mismatch}
            />
            {mismatch && <small className="field-error">Passwords do not match.</small>}
          </div>

          <button type="submit" className="btn btn-wide" disabled={busy || mismatch}>
            {busy ? 'Creating…' : 'Create Account'}
          </button>
        </form>

        <p className="muted" style={{ marginTop: '1.25rem', fontSize: '0.9rem' }}>
          Already have one? <Link to="/login">Log in</Link>.
        </p>
      </div>
    </div>
  )
}
