'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../../../features/auth/AuthContext';
import { organizationService } from '../../../services/organizations';

export default function SettingsPage() {
  const { organization, setOrganization } = useAuth();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [timezone, setTimezone] = useState('UTC');
  const [locale, setLocale] = useState('en_US');
  const [isSaving, setIsSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (organization) {
      setName(organization.name);
      setDescription(organization.description || '');
      if (organization.settings) {
        setTimezone(organization.settings.timezone || 'UTC');
        setLocale(organization.settings.locale || 'en_US');
      }
    }
  }, [organization]);

  if (!organization) {
    return <div className="text-zinc-400">Loading organization context...</div>;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setSuccess(false);
    setError('');
    try {
      const updated = await organizationService.update(organization.id, {
        name,
        description: description || undefined,
        settings: {
          ...organization.settings,
          timezone,
          locale,
        },
      });
      setOrganization(updated);
      setSuccess(true);
    } catch (err: any) {
      setError(err.message || 'Failed to update settings');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h2 className="text-xl font-bold text-white mb-1">Organization Settings</h2>
        <p className="text-sm text-zinc-400">Configure profile details, subscription settings, and team preferences.</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6 bg-zinc-900 border border-zinc-800/80 rounded-xl p-8 shadow-xl">
        {success && (
          <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-lg text-sm font-semibold">
            Settings updated successfully!
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg text-sm font-semibold">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Organization Name</label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors"
            />
          </div>

          <div className="md:col-span-2">
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors h-28 resize-none"
              placeholder="Workspace details..."
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Timezone</label>
            <select
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors"
            >
              <option value="UTC">UTC</option>
              <option value="America/New_York">EST (America/New_York)</option>
              <option value="America/Los_Angeles">PST (America/Los_Angeles)</option>
              <option value="Europe/London">GMT (Europe/London)</option>
              <option value="Asia/Tokyo">JST (Asia/Tokyo)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Locale</label>
            <select
              value={locale}
              onChange={(e) => setLocale(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition-colors"
            >
              <option value="en_US">en_US</option>
              <option value="en_GB">en_GB</option>
              <option value="ja_JP">ja_JP</option>
              <option value="fr_FR">fr_FR</option>
            </select>
          </div>
        </div>

        <div className="pt-4 border-t border-zinc-800 flex justify-between items-center">
          <div className="text-xs text-zinc-500">
            Tenant ID: <span className="font-mono">{organization.id}</span>
          </div>
          <button
            type="submit"
            disabled={isSaving}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold shadow-lg shadow-indigo-500/20 disabled:opacity-50 transition-colors"
          >
            {isSaving ? 'Saving Changes...' : 'Save Settings'}
          </button>
        </div>
      </form>

      {/* Subscription Tier Management */}
      <div className="bg-zinc-900 border border-zinc-800/80 rounded-xl p-8 shadow-xl space-y-6">
        <div>
          <h3 className="text-lg font-bold text-white mb-1">Billing & Subscription</h3>
          <p className="text-sm text-zinc-400">View and update your active subscription details.</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-zinc-950 border border-zinc-800 rounded-xl p-6">
          <div className="space-y-1">
            <span className="text-xs text-zinc-500 uppercase font-semibold">Active Plan</span>
            <p className="text-xl font-bold text-indigo-400 capitalize">{organization.subscription_tier}</p>
          </div>
          <div className="space-y-1">
            <span className="text-xs text-zinc-500 uppercase font-semibold">Status</span>
            <p className="text-xl font-bold text-emerald-400 capitalize">{organization.subscription_status}</p>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="button"
            onClick={() => alert("Enterprise plan switching functionality will be unlocked in Phase 6.")}
            className="px-5 py-2.5 border border-zinc-800 hover:bg-zinc-800 text-white rounded-lg text-sm font-semibold transition-colors"
          >
            Upgrade Tier
          </button>
        </div>
      </div>
    </div>
  );
}
