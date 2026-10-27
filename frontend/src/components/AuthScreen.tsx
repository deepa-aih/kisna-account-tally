import React, { FormEvent, useState } from 'react';
import { Eye, EyeOff, LockKeyhole, ShieldCheck } from 'lucide-react';
import { resetPassword, signIn } from '../lib/api';
import type { AuthUser } from '../lib/api';

interface AuthScreenProps {
  resetToken?: string;
  onSignedIn: (user: AuthUser) => void;
}

const passwordRules = [
  'At least 12 characters',
  'At least one uppercase and one lowercase letter',
  'At least one number',
];

export const AuthScreen: React.FC<AuthScreenProps> = ({ resetToken, onSignedIn }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError('');
    setNotice('');
    setBusy(true);
    try {
      if (resetToken) {
        await resetPassword(resetToken, password);
        window.history.replaceState({}, '', window.location.pathname);
        setPassword('');
        setNotice('Password updated. Sign in with your new password.');
        window.setTimeout(() => window.location.reload(), 900);
      } else {
        const result = await signIn(email.trim(), password);
        onSignedIn(result.user);
      }
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : 'Unable to complete the request.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 px-4 py-10 text-slate-100 flex items-center justify-center">
      <section className="w-full max-w-md overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl">
        <div className="border-b border-slate-800 px-8 py-7">
          <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400">
            {resetToken ? <LockKeyhole className="h-6 w-6" /> : <ShieldCheck className="h-6 w-6" />}
          </div>
          <p className="text-sm text-slate-400">Account Tally</p>
          <h1 className="mt-1 text-2xl font-semibold tracking-tight">
            {resetToken ? 'Set your password' : 'Sign in to your workspace'}
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            {resetToken
              ? 'Choose a password to activate or recover your account.'
              : 'Use the work email and password provided for your account.'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 px-8 py-7">
          {!resetToken && (
            <label className="block space-y-2 text-sm font-medium">
              <span>Work email</span>
              <input
                type="email"
                autoComplete="username"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-3 text-slate-100 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
                placeholder="you@company.com"
              />
            </label>
          )}

          <label className="block space-y-2 text-sm font-medium">
            <span>{resetToken ? 'New password' : 'Password'}</span>
            <span className="relative block">
              <input
                type={showPassword ? 'text' : 'password'}
                autoComplete={resetToken ? 'new-password' : 'current-password'}
                required
                minLength={resetToken ? 12 : undefined}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3.5 py-3 pr-12 text-slate-100 outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
                placeholder={resetToken ? 'Create a strong password' : 'Enter your password'}
              />
              <button
                type="button"
                onClick={() => setShowPassword((visible) => !visible)}
                className="absolute inset-y-0 right-0 flex items-center px-3 text-slate-400 hover:text-white"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </span>
          </label>

          {resetToken && (
            <ul className="space-y-1 text-xs text-slate-400">
              {passwordRules.map((rule) => <li key={rule}>- {rule}</li>)}
            </ul>
          )}

          {error && <p role="alert" className="rounded-lg border border-red-900/70 bg-red-950/40 px-3 py-2.5 text-sm text-red-300">{error}</p>}
          {notice && <p role="status" className="rounded-lg border border-emerald-900/70 bg-emerald-950/40 px-3 py-2.5 text-sm text-emerald-300">{notice}</p>}

          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-emerald-500 px-4 py-3 font-semibold text-slate-950 transition hover:bg-emerald-400 disabled:cursor-wait disabled:opacity-60"
          >
            {busy ? 'Please wait...' : resetToken ? 'Save password' : 'Sign in'}
          </button>

          {!resetToken && (
            <p className="text-center text-xs leading-relaxed text-slate-500">
              Need an account or a password reset? Contact your workspace administrator for an invite or reset link.
            </p>
          )}
        </form>
      </section>
    </main>
  );
};
