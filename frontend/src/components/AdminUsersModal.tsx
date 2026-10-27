import React, { FormEvent, useEffect, useState } from 'react';
import { Copy, Link2, LoaderCircle, UserPlus, X } from 'lucide-react';
import { createManagedUser, createUserResetLink, getManagedUsers, ManagedUser } from '../lib/api';

interface AdminUsersModalProps {
  onClose: () => void;
}

export const AdminUsersModal: React.FC<AdminUsersModalProps> = ({ onClose }) => {
  const [users, setUsers] = useState<ManagedUser[]>([]);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [resetLink, setResetLink] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const refreshUsers = async () => setUsers(await getManagedUsers());

  useEffect(() => {
    void refreshUsers().catch((loadError) => setError(loadError instanceof Error ? loadError.message : 'Could not load users.'));
  }, []);

  const handleCreate = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError('');
    setMessage('');
    setResetLink('');
    try {
      const result = await createManagedUser(name.trim(), email.trim());
      setResetLink(result.resetLink);
      setMessage(`Account created for ${result.user.email}. Share the one-time link below; it expires in 30 minutes.`);
      setName('');
      setEmail('');
      await refreshUsers();
    } catch (createError) {
      setError(createError instanceof Error ? createError.message : 'Could not create the account.');
    } finally {
      setBusy(false);
    }
  };

  const handleResetLink = async (user: ManagedUser) => {
    setBusy(true);
    setError('');
    setMessage(`A new password reset link was created for ${user.email}. It expires in 30 minutes.`);
    try {
      const result = await createUserResetLink(user.id);
      setResetLink(result.resetLink);
    } catch (resetError) {
      setError(resetError instanceof Error ? resetError.message : 'Could not create a reset link.');
      setMessage('');
    } finally {
      setBusy(false);
    }
  };

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(resetLink);
      setMessage('Reset link copied to clipboard.');
    } catch {
      setError('Clipboard access failed. Select and copy the link manually.');
    }
  };

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-slate-950/70 p-4 backdrop-blur-sm" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
      <section role="dialog" aria-modal="true" aria-labelledby="users-title" className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-slate-700 bg-slate-900 text-slate-100 shadow-2xl">
        <header className="flex items-start justify-between border-b border-slate-800 px-6 py-5">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-emerald-400">Workspace administration</p>
            <h2 id="users-title" className="mt-1 text-xl font-semibold">Manage users</h2>
            <p className="mt-1 text-sm text-slate-400">Create named accounts and issue password setup links.</p>
          </div>
          <button onClick={onClose} className="rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white" aria-label="Close user management"><X className="h-5 w-5" /></button>
        </header>

        <div className="space-y-6 p-6">
          <form onSubmit={handleCreate} className="grid gap-3 rounded-xl border border-slate-800 bg-slate-950/50 p-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
            <label className="space-y-1.5 text-xs font-medium text-slate-300">
              <span>Full name</span>
              <input required value={name} onChange={(event) => setName(event.target.value)} className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2.5 text-sm text-white outline-none focus:border-emerald-500" placeholder="Ajinkya Patil" />
            </label>
            <label className="space-y-1.5 text-xs font-medium text-slate-300">
              <span>Work email</span>
              <input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2.5 text-sm text-white outline-none focus:border-emerald-500" placeholder="name@company.com" />
            </label>
            <button disabled={busy} className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-slate-950 hover:bg-emerald-400 disabled:opacity-60">
              {busy ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <UserPlus className="h-4 w-4" />} Create user
            </button>
          </form>

          {(message || error) && <div className={`rounded-lg border px-3 py-2.5 text-sm ${error ? 'border-red-900 bg-red-950/40 text-red-300' : 'border-emerald-900 bg-emerald-950/40 text-emerald-300'}`} role={error ? 'alert' : 'status'}>{error || message}</div>}

          {resetLink && (
            <div className="rounded-xl border border-emerald-900/80 bg-emerald-950/20 p-4">
              <div className="mb-2 flex items-center justify-between gap-3 text-sm font-medium text-emerald-300"><span className="inline-flex items-center gap-2"><Link2 className="h-4 w-4" /> One-time password link</span><button onClick={() => void copyLink()} className="inline-flex items-center gap-1.5 rounded-md px-2 py-1 text-xs hover:bg-emerald-900/50"><Copy className="h-3.5 w-3.5" /> Copy</button></div>
              <a href={resetLink} className="break-all text-xs text-slate-200 underline decoration-slate-600 underline-offset-2">{resetLink}</a>
            </div>
          )}

          <div>
            <h3 className="mb-3 text-sm font-semibold">Accounts</h3>
            <div className="divide-y divide-slate-800 rounded-xl border border-slate-800">
              {users.map((user) => (
                <div key={user.id} className="flex flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{user.name} <span className="ml-1 text-xs font-normal text-slate-500">{user.role === 'admin' ? 'Admin' : 'Member'}</span></p>
                    <p className="truncate text-xs text-slate-400">{user.email}</p>
                  </div>
                  <button disabled={busy || !user.active} onClick={() => void handleResetLink(user)} className="shrink-0 rounded-lg border border-slate-700 px-3 py-2 text-xs font-medium text-slate-200 hover:border-emerald-600 hover:text-emerald-300 disabled:opacity-50">
                    Generate reset link
                  </button>
                </div>
              ))}
              {!users.length && !error && <p className="px-4 py-5 text-sm text-slate-500">No accounts found.</p>}
            </div>
          </div>
          <p className="text-xs leading-relaxed text-slate-500">Links are shown only once and expire after 30 minutes. Share them with the intended user through a secure channel.</p>
        </div>
      </section>
    </div>
  );
};
