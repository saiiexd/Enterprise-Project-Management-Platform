'use client';

import React, { useEffect, useState } from 'react';
import { useAuth } from '../../../features/auth/AuthContext';
import { organizationService } from '../../../services/organizations';
import { invitationService } from '../../../services/invitations';
import { OrganizationMember, Invitation } from '../../../types';

export default function MembersPage() {
  const { organization, user: currentUser } = useAuth();
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [loadingMembers, setLoadingMembers] = useState(true);
  const [loadingInvites, setLoadingInvites] = useState(true);
  
  // Invite Form state
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('Member');
  const [isInviting, setIsInviting] = useState(false);
  const [inviteSuccess, setInviteSuccess] = useState('');
  const [inviteError, setInviteError] = useState('');

  // Reload triggers
  const [triggerLoadMembers, setTriggerLoadMembers] = useState(0);
  const [triggerLoadInvites, setTriggerLoadInvites] = useState(0);

  useEffect(() => {
    if (!organization) return;

    const fetchMembers = async () => {
      setLoadingMembers(true);
      try {
        const res = await organizationService.listMembers(organization.id);
        setMembers(res.members);
      } catch (err) {
        console.error('Failed to load organization members:', err);
      } finally {
        setLoadingMembers(false);
      }
    };

    fetchMembers();
  }, [organization, triggerLoadMembers]);

  useEffect(() => {
    if (!organization) return;

    const fetchInvites = async () => {
      setLoadingInvites(true);
      try {
        const res = await invitationService.list();
        setInvitations(res.invitations);
      } catch (err) {
        console.error('Failed to load organization invitations:', err);
      } finally {
        setLoadingInvites(false);
      }
    };

    fetchInvites();
  }, [organization, triggerLoadInvites]);

  if (!organization) {
    return <div className="text-zinc-400">Loading organization context...</div>;
  }

  const handleSendInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail) return;
    setIsInviting(true);
    setInviteSuccess('');
    setInviteError('');
    try {
      await invitationService.invite(inviteEmail, inviteRole);
      setInviteSuccess(`Successfully sent invitation to ${inviteEmail}!`);
      setInviteEmail('');
      setTriggerLoadInvites(prev => prev + 1);
    } catch (err: any) {
      setInviteError(err.message || 'Failed to dispatch invitation');
    } finally {
      setIsInviting(false);
    }
  };

  const handleResendInvite = async (id: string, email: string) => {
    try {
      await invitationService.resend(id);
      alert(`Resent invitation email to ${email}!`);
      setTriggerLoadInvites(prev => prev + 1);
    } catch (err: any) {
      alert(err.message || 'Failed to resend invitation');
    }
  };

  const handleCancelInvite = async (id: string) => {
    if (!confirm('Are you sure you want to cancel this invitation?')) return;
    try {
      await invitationService.cancel(id);
      setTriggerLoadInvites(prev => prev + 1);
    } catch (err: any) {
      alert(err.message || 'Failed to cancel invitation');
    }
  };

  const handleRemoveMember = async (userId: string, name: string) => {
    if (userId === currentUser?.id) {
      alert("You cannot remove yourself from the organization. Transfer ownership or contact another administrator.");
      return;
    }
    if (!confirm(`Are you sure you want to remove ${name} from this organization?`)) return;
    try {
      await organizationService.removeMember(organization.id, userId);
      setTriggerLoadMembers(prev => prev + 1);
    } catch (err: any) {
      alert(err.message || 'Failed to remove member');
    }
  };

  const handleRoleChange = async (userId: string, newRole: string) => {
    try {
      await organizationService.updateMemberRole(organization.id, userId, newRole);
      alert("Role updated successfully.");
      setTriggerLoadMembers(prev => prev + 1);
    } catch (err: any) {
      alert(err.message || 'Failed to update member role');
    }
  };

  const rolesList = ['Organization Owner', 'Organization Administrator', 'Project Manager', 'Member', 'Guest'];

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div>
        <h2 className="text-xl font-bold text-white mb-1">Members & Invitations</h2>
        <p className="text-sm text-zinc-400">Add collaborators, manage workspace permissions, and audit active users.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Members Management Table */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-zinc-900 border border-zinc-800/80 rounded-xl p-6 shadow-xl space-y-4">
            <h3 className="text-lg font-bold text-white">Active Members ({members.length})</h3>

            {loadingMembers ? (
              <div className="space-y-3 py-4">
                {[1, 2, 3].map((n) => (
                  <div key={n} className="h-14 bg-zinc-850 animate-pulse rounded-lg" />
                ))}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="text-zinc-500 border-b border-zinc-800 pb-2">
                      <th className="pb-3 font-semibold">User</th>
                      <th className="pb-3 font-semibold">Role</th>
                      <th className="pb-3 font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-850">
                    {members.map((m) => {
                      const isSelf = m.user_id === currentUser?.id;
                      return (
                        <tr key={m.user_id} className="group">
                          <td className="py-4 pr-3 flex items-center gap-3">
                            <div className="h-9 w-9 rounded-full bg-zinc-850 border border-zinc-800 flex items-center justify-center font-semibold text-indigo-400 uppercase text-sm">
                              {m.full_name?.charAt(0) || m.email.charAt(0)}
                            </div>
                            <div>
                              <p className="font-semibold text-zinc-200">{m.full_name || 'EPMP User'} {isSelf && <span className="text-xs text-indigo-400">(You)</span>}</p>
                              <p className="text-xs text-zinc-500">{m.email}</p>
                            </div>
                          </td>
                          <td className="py-4">
                            {isSelf ? (
                              <span className="text-xs text-zinc-400 font-mono">{m.role_name}</span>
                            ) : (
                              <select
                                value={m.role_name}
                                onChange={(e) => handleRoleChange(m.user_id, e.target.value)}
                                className="bg-zinc-950 border border-zinc-800 rounded px-2.5 py-1 text-xs text-zinc-300 focus:outline-none focus:border-indigo-500 transition-colors"
                              >
                                {rolesList.map((role) => (
                                  <option key={role} value={role}>{role}</option>
                                ))}
                              </select>
                            )}
                          </td>
                          <td className="py-4 text-right">
                            {!isSelf && (
                              <button
                                onClick={() => handleRemoveMember(m.user_id, m.full_name || m.email)}
                                className="text-zinc-500 hover:text-red-400 p-1.5 rounded-lg hover:bg-zinc-800 transition-colors"
                                title="Remove Member"
                              >
                                <svg className="h-4.5 w-4.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Pending Invitations list */}
          <div className="bg-zinc-900 border border-zinc-800/80 rounded-xl p-6 shadow-xl space-y-4">
            <h3 className="text-lg font-bold text-white">Pending Invitations ({invitations.filter(i => i.status === 'pending').length})</h3>

            {loadingInvites ? (
              <div className="space-y-3 py-4">
                {[1, 2].map((n) => (
                  <div key={n} className="h-14 bg-zinc-850 animate-pulse rounded-lg" />
                ))}
              </div>
            ) : invitations.length === 0 ? (
              <div className="text-center py-8 border border-dashed border-zinc-800 rounded-lg text-zinc-500 text-sm">
                No pending invitations.
              </div>
            ) : (
              <div className="divide-y divide-zinc-850">
                {invitations.map((inv) => (
                  <div key={inv.id} className="py-3.5 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-semibold text-zinc-200">{inv.email}</p>
                      <p className="text-xs text-zinc-500">
                        Invited as <span className="font-mono">{inv.role_name}</span> • Exp: {new Date(inv.expires_at).toLocaleDateString()}
                      </p>
                    </div>
                    
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleResendInvite(inv.id, inv.email)}
                        className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20 px-2.5 py-1.5 rounded transition-colors"
                      >
                        Resend
                      </button>
                      <button
                        onClick={() => handleCancelInvite(inv.id)}
                        className="text-xs font-semibold text-red-400 hover:text-red-300 bg-red-500/10 hover:bg-red-500/20 px-2.5 py-1.5 rounded transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Invite Form Side Panel */}
        <div className="bg-zinc-900 border border-zinc-800/80 rounded-xl p-6 shadow-xl h-fit space-y-6">
          <div>
            <h3 className="text-lg font-bold text-white mb-1">Invite New Collaborator</h3>
            <p className="text-xs text-zinc-400">Dispatches an email containing a secure link to join this organization.</p>
          </div>

          <form onSubmit={handleSendInvite} className="space-y-4">
            {inviteSuccess && (
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg text-xs font-semibold">
                {inviteSuccess}
              </div>
            )}

            {inviteError && (
              <div className="p-3 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-xs font-semibold">
                {inviteError}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Email Address</label>
              <input
                type="email"
                required
                value={inviteEmail}
                onChange={(e) => setInviteEmail(e.target.value)}
                placeholder="e.g. name@company.com"
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Organization Role</label>
              <select
                value={inviteRole}
                onChange={(e) => setInviteRole(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors"
              >
                {rolesList.map((role) => (
                  <option key={role} value={role}>{role}</option>
                ))}
              </select>
            </div>

            <button
              type="submit"
              disabled={isInviting}
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold shadow-lg shadow-indigo-500/20 disabled:opacity-50 transition-colors"
            >
              {isInviting ? 'Sending Invite...' : 'Send Invitation'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
