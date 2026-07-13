'use client';

import React, { useEffect, useState } from 'react';
import { useAuth } from '../../../features/auth/AuthContext';
import { teamService } from '../../../services/teams';
import { organizationService } from '../../../services/organizations';
import { Team, TeamMember, OrganizationMember } from '../../../types';

export default function TeamsPage() {
  const { organization } = useAuth();
  
  // Teams lists
  const [teams, setTeams] = useState<Team[]>([]);
  const [totalTeams, setTotalTeams] = useState(0);
  const [loadingTeams, setLoadingTeams] = useState(true);
  const [triggerLoadTeams, setTriggerLoadTeams] = useState(0);

  // Selected Team Details
  const [selectedTeam, setSelectedTeam] = useState<Team | null>(null);
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [loadingMembers, setLoadingMembers] = useState(false);
  const [triggerLoadMembers, setTriggerLoadMembers] = useState(0);

  // Organization members (for team assignment dropdown)
  const [orgMembers, setOrgMembers] = useState<OrganizationMember[]>([]);

  // Create Team Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createDesc, setCreateDesc] = useState('');
  const [isCreating, setIsCreating] = useState(false);

  // Add Member State
  const [selectedUserId, setSelectedUserId] = useState('');
  const [memberRole, setMemberRole] = useState('developer');
  const [isAddingMember, setIsAddingMember] = useState(false);

  // Load Teams & Org Members
  useEffect(() => {
    if (!organization) return;

    const fetchTeams = async () => {
      setLoadingTeams(true);
      try {
        const res = await teamService.list();
        setTeams(res.teams);
        setTotalTeams(res.total);
      } catch (err) {
        console.error('Failed to load teams:', err);
      } finally {
        setLoadingTeams(false);
      }
    };

    const fetchOrgMembers = async () => {
      try {
        const res = await organizationService.listMembers(organization.id);
        setOrgMembers(res.members);
      } catch (err) {
        console.error('Failed to load organization members:', err);
      }
    };

    fetchTeams();
    fetchOrgMembers();
  }, [organization, triggerLoadTeams]);

  // Load Selected Team Members
  useEffect(() => {
    if (!selectedTeam) return;

    const fetchTeamMembers = async () => {
      setLoadingMembers(true);
      try {
        const res = await teamService.listMembers(selectedTeam.id);
        setTeamMembers(res.members);
      } catch (err) {
        console.error('Failed to load team members:', err);
      } finally {
        setLoadingMembers(false);
      }
    };

    fetchTeamMembers();
  }, [selectedTeam, triggerLoadMembers]);

  if (!organization) {
    return <div className="text-zinc-400">Loading organization context...</div>;
  }

  const handleCreateTeam = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createName) return;
    setIsCreating(true);
    try {
      const created = await teamService.create(createName, createDesc || null, organization.id);
      setShowCreateModal(false);
      setCreateName('');
      setCreateDesc('');
      setTriggerLoadTeams(prev => prev + 1);
      // Auto-select newly created team
      setSelectedTeam(created);
    } catch (err: any) {
      alert(err.message || 'Failed to create team');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteTeam = async (teamId: string, name: string) => {
    if (!confirm(`Are you sure you want to delete the team "${name}"?`)) return;
    try {
      await teamService.delete(teamId);
      if (selectedTeam?.id === teamId) {
        setSelectedTeam(null);
      }
      setTriggerLoadTeams(prev => prev + 1);
    } catch (err: any) {
      alert(err.message || 'Failed to delete team');
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTeam || !selectedUserId) return;
    setIsAddingMember(true);
    try {
      await teamService.addMember(selectedTeam.id, selectedUserId, memberRole);
      setSelectedUserId('');
      setTriggerLoadMembers(prev => prev + 1);
    } catch (err: any) {
      alert(err.message || 'Failed to add member to team');
    } finally {
      setIsAddingMember(false);
    }
  };

  const handleRemoveMember = async (userId: string, name: string) => {
    if (!selectedTeam) return;
    if (!confirm(`Are you sure you want to remove "${name}" from this team?`)) return;
    try {
      await teamService.removeMember(selectedTeam.id, userId);
      setTriggerLoadMembers(prev => prev + 1);
    } catch (err: any) {
      alert(err.message || 'Failed to remove member from team');
    }
  };

  // Filter org members that are NOT currently in the selected team
  const availableOrgMembers = orgMembers.filter(
    (om) => !teamMembers.some((tm) => tm.user_id === om.user_id)
  );

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-white mb-1">Teams Workspace</h2>
          <p className="text-sm text-zinc-400">Establish and organize specialized engineering pods and project committees.</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2.5 rounded-lg text-sm font-semibold shadow-lg shadow-indigo-500/20 transition-colors flex items-center gap-2"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          Create Team
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Teams List (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          {loadingTeams ? (
            <div className="space-y-4">
              {[1, 2, 3].map((n) => (
                <div key={n} className="h-28 bg-zinc-900 border border-zinc-800 animate-pulse rounded-xl" />
              ))}
            </div>
          ) : teams.length === 0 ? (
            <div className="text-center py-16 bg-zinc-900 border border-dashed border-zinc-800 rounded-xl">
              <svg className="h-12 w-12 text-zinc-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <p className="text-zinc-500 font-semibold mb-4">No Teams Found</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="bg-zinc-800 hover:bg-zinc-700 text-white px-4 py-2 rounded-lg text-xs font-semibold transition-colors"
              >
                Create First Team
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {teams.map((t) => {
                const isSelected = selectedTeam?.id === t.id;
                return (
                  <div
                    key={t.id}
                    onClick={() => setSelectedTeam(t)}
                    className={`bg-zinc-900 border p-5 rounded-xl shadow-lg cursor-pointer transition-all hover:-translate-y-0.5 flex flex-col justify-between h-40 ${
                      isSelected ? 'border-indigo-500 shadow-indigo-500/10' : 'border-zinc-800/80 hover:border-zinc-700/80'
                    }`}
                  >
                    <div>
                      <div className="flex justify-between items-start gap-2">
                        <h4 className="font-bold text-white text-base truncate">{t.name}</h4>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDeleteTeam(t.id, t.name); }}
                          className="text-zinc-500 hover:text-red-400 p-1 rounded hover:bg-zinc-850 transition-colors shrink-0"
                          title="Delete Team"
                        >
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                      <p className="text-xs text-zinc-400 line-clamp-2 mt-1">{t.description || 'No description provided.'}</p>
                    </div>

                    <div className="flex items-center justify-between text-xs text-zinc-500 border-t border-zinc-800/60 pt-3">
                      <span>Created: {new Date(t.created_at).toLocaleDateString()}</span>
                      <span className="font-semibold text-indigo-400">View details →</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Selected Team Sidebar (1 col) */}
        <div className="bg-zinc-900 border border-zinc-800/80 rounded-xl p-6 shadow-xl h-fit space-y-6">
          {selectedTeam ? (
            <>
              <div>
                <h3 className="text-lg font-bold text-white mb-1">{selectedTeam.name}</h3>
                <p className="text-xs text-zinc-400">{selectedTeam.description || 'No description.'}</p>
              </div>

              {/* Add member form */}
              <div className="bg-zinc-950 border border-zinc-800/80 rounded-xl p-4 space-y-4">
                <p className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Assign Team Member</p>
                <form onSubmit={handleAddMember} className="space-y-3">
                  <div>
                    <select
                      value={selectedUserId}
                      onChange={(e) => setSelectedUserId(e.target.value)}
                      required
                      className="w-full bg-zinc-900 border border-zinc-800 rounded px-2.5 py-2 text-xs text-zinc-300 focus:outline-none focus:border-indigo-500 transition-colors"
                    >
                      <option value="">Select Org Member...</option>
                      {availableOrgMembers.map((om) => (
                        <option key={om.user_id} value={om.user_id}>
                          {om.full_name || om.email}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="flex gap-2">
                    <select
                      value={memberRole}
                      onChange={(e) => setMemberRole(e.target.value)}
                      className="bg-zinc-900 border border-zinc-800 rounded px-2.5 py-1.5 text-xs text-zinc-300 focus:outline-none focus:border-indigo-500 transition-colors w-2/3"
                    >
                      <option value="developer">Developer</option>
                      <option value="lead">Team Lead</option>
                      <option value="tester">QA / Tester</option>
                      <option value="manager">Product Manager</option>
                    </select>
                    <button
                      type="submit"
                      disabled={isAddingMember || !selectedUserId}
                      className="flex-1 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold shadow disabled:opacity-50 transition-colors"
                    >
                      Add
                    </button>
                  </div>
                </form>
              </div>

              {/* Members listing */}
              <div className="space-y-3">
                <p className="text-xs font-bold text-zinc-400 uppercase tracking-wider">Team Members ({teamMembers.length})</p>

                {loadingMembers ? (
                  <div className="space-y-2 py-2">
                    <div className="h-10 bg-zinc-850 animate-pulse rounded" />
                    <div className="h-10 bg-zinc-850 animate-pulse rounded" />
                  </div>
                ) : teamMembers.length === 0 ? (
                  <p className="text-xs text-zinc-500 italic">No members assigned to this team.</p>
                ) : (
                  <div className="divide-y divide-zinc-800/80 max-h-60 overflow-y-auto pr-1">
                    {teamMembers.map((m) => (
                      <div key={m.id} className="py-2.5 flex items-center justify-between group first:pt-0 last:pb-0">
                        <div>
                          <p className="text-xs font-semibold text-zinc-200">{m.full_name || m.email}</p>
                          <p className="text-[10px] text-zinc-500 capitalize">{m.role}</p>
                        </div>
                        <button
                          onClick={() => handleRemoveMember(m.user_id, m.full_name || m.email)}
                          className="text-zinc-600 hover:text-red-400 p-1 rounded hover:bg-zinc-850 transition-colors"
                          title="Remove Member"
                        >
                          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2.5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="text-center py-16 text-zinc-500 text-sm italic">
              Select a team from the workspace grid to view settings and members.
            </div>
          )}
        </div>
      </div>

      {/* Create Team Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl w-full max-w-md p-6 shadow-2xl relative">
            <button
              onClick={() => setShowCreateModal(false)}
              className="absolute top-4 right-4 text-zinc-400 hover:text-white p-1 hover:bg-zinc-800 rounded-lg transition-colors"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            <h3 className="text-lg font-bold text-white mb-2">Create New Team</h3>
            <p className="text-sm text-zinc-400 mb-6">Teams allow you to partition tasks and projects into distinct cohorts.</p>

            <form onSubmit={handleCreateTeam} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Team Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Frontend Pod, QA Team"
                  value={createName}
                  onChange={(e) => setCreateName(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Description</label>
                <textarea
                  placeholder="Explain the team goals..."
                  value={createDesc}
                  onChange={(e) => setCreateDesc(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors h-24 resize-none"
                />
              </div>

              <div className="pt-2 flex justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 text-sm font-semibold text-zinc-400 hover:text-white rounded-lg hover:bg-zinc-800 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isCreating}
                  className="px-4 py-2 text-sm font-semibold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg shadow-lg shadow-indigo-500/20 disabled:opacity-50 transition-colors"
                >
                  {isCreating ? 'Creating...' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
