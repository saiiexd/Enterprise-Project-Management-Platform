'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '../../features/auth/AuthContext';
import { teamService } from '../../services/teams';
import { organizationService } from '../../services/organizations';
import { Team, OrganizationMember } from '../../types';

export default function DashboardPage() {
  const { organization } = useAuth();
  const [teams, setTeams] = useState<Team[]>([]);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [totalTeams, setTotalTeams] = useState(0);
  const [totalMembers, setTotalMembers] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!organization) return;

    const fetchData = async () => {
      setLoading(true);
      try {
        const teamsData = await teamService.list({ limit: 5 });
        setTeams(teamsData.teams);
        setTotalTeams(teamsData.total);

        const membersData = await organizationService.listMembers(organization.id, { limit: 5 });
        setMembers(membersData.members);
        setTotalMembers(membersData.total);
      } catch (err) {
        console.error('Error fetching dashboard stats:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [organization]);

  if (!organization) {
    return (
      <div className="text-center py-12 bg-zinc-900 border border-zinc-800 rounded-2xl max-w-xl mx-auto">
        <h2 className="text-xl font-bold text-white mb-2">No Active Organization</h2>
        <p className="text-sm text-zinc-400">Please select or create an organization in the header switcher to begin.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden bg-gradient-to-r from-indigo-900 to-indigo-950 border border-indigo-500/20 rounded-2xl p-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-6 shadow-2xl">
        <div className="space-y-2 z-10">
          <h2 className="text-2xl md:text-3xl font-extrabold text-white">Welcome back to {organization.name}!</h2>
          <p className="text-indigo-200 text-sm max-w-md">Manage teams, assign members, invite collaborators, and scale your project workflows.</p>
        </div>
        <div className="flex gap-3 z-10">
          <Link href="/dashboard/teams" className="bg-white hover:bg-zinc-100 text-zinc-900 px-4 py-2 rounded-lg text-sm font-semibold transition-colors">
            Manage Teams
          </Link>
          <Link href="/dashboard/members" className="bg-indigo-600 hover:bg-indigo-500 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors">
            Invite Members
          </Link>
        </div>
        {/* Subtle grid decoration */}
        <div className="absolute right-0 bottom-0 opacity-10 pointer-events-none w-96 h-full select-none bg-[radial-gradient(#fff_1px,transparent_1px)] [background-size:16px_16px]" />
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-zinc-900 border border-zinc-800/80 rounded-xl p-6 shadow-lg flex flex-col justify-between h-36">
          <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Active Teams</span>
          {loading ? (
            <div className="h-8 w-16 bg-zinc-850 animate-pulse rounded" />
          ) : (
            <span className="text-3xl font-extrabold text-white">{totalTeams}</span>
          )}
          <span className="text-xs text-zinc-400">Primary engineering and product units</span>
        </div>

        <div className="bg-zinc-900 border border-zinc-800/80 rounded-xl p-6 shadow-lg flex flex-col justify-between h-36">
          <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Organization Members</span>
          {loading ? (
            <div className="h-8 w-16 bg-zinc-850 animate-pulse rounded" />
          ) : (
            <span className="text-3xl font-extrabold text-white">{totalMembers}</span>
          )}
          <span className="text-xs text-zinc-400">Total collaborators in this workspace</span>
        </div>

        <div className="bg-zinc-900 border border-zinc-800/80 rounded-xl p-6 shadow-lg flex flex-col justify-between h-36">
          <span className="text-xs font-semibold text-zinc-500 uppercase tracking-wider">Subscription Tier</span>
          <span className="text-2xl font-extrabold text-white capitalize bg-gradient-to-r from-yellow-400 via-orange-500 to-red-500 bg-clip-text text-transparent">
            {organization.subscription_tier}
          </span>
          <span className="text-xs text-zinc-400">Status: {organization.subscription_status}</span>
        </div>
      </div>

      {/* Lists Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Teams List */}
        <div className="bg-zinc-900 border border-zinc-800/80 rounded-xl p-6 shadow-lg space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-bold text-white">Teams</h3>
            <Link href="/dashboard/teams" className="text-xs font-semibold text-indigo-400 hover:text-indigo-300">
              View All
            </Link>
          </div>

          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((n) => (
                <div key={n} className="h-12 bg-zinc-850 animate-pulse rounded-lg" />
              ))}
            </div>
          ) : teams.length === 0 ? (
            <div className="text-center py-8 border border-dashed border-zinc-800 rounded-lg">
              <p className="text-sm text-zinc-500 mb-3">No teams created yet.</p>
              <Link href="/dashboard/teams" className="text-xs bg-zinc-800 text-white px-3 py-1.5 rounded-lg hover:bg-zinc-700 transition-colors">
                Create First Team
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-zinc-800/80">
              {teams.map((t) => (
                <div key={t.id} className="py-3 flex items-center justify-between first:pt-0 last:pb-0">
                  <div>
                    <h4 className="text-sm font-semibold text-zinc-200">{t.name}</h4>
                    <p className="text-xs text-zinc-500 truncate max-w-[280px]">{t.description || 'No description'}</p>
                  </div>
                  <Link href={`/dashboard/teams?teamId=${t.id}`} className="text-xs bg-zinc-800 hover:bg-zinc-700 text-zinc-300 px-2.5 py-1 rounded transition-colors">
                    Manage
                  </Link>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Members List */}
        <div className="bg-zinc-900 border border-zinc-800/80 rounded-xl p-6 shadow-lg space-y-6">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-bold text-white">Members</h3>
            <Link href="/dashboard/members" className="text-xs font-semibold text-indigo-400 hover:text-indigo-300">
              View All
            </Link>
          </div>

          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((n) => (
                <div key={n} className="h-12 bg-zinc-850 animate-pulse rounded-lg" />
              ))}
            </div>
          ) : (
            <div className="divide-y divide-zinc-800/80">
              {members.map((m) => (
                <div key={m.user_id} className="py-3 flex items-center justify-between first:pt-0 last:pb-0">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-zinc-800 flex items-center justify-center font-semibold text-indigo-400 text-xs uppercase">
                      {m.full_name?.charAt(0) || m.email.charAt(0)}
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-zinc-200">{m.full_name || 'EPMP User'}</h4>
                      <p className="text-xs text-zinc-500">{m.email}</p>
                    </div>
                  </div>
                  <span className="text-[10px] font-mono uppercase bg-zinc-850 px-2.5 py-0.5 rounded-full text-zinc-400 border border-zinc-700/30">
                    {m.role_name}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
