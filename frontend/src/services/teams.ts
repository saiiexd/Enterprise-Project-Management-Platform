import { api } from './api';
import { Team, TeamMember } from '../types';

export const teamService = {
  create: async (name: string, description: string | null, organizationId: string): Promise<Team> => {
    return api.post('/teams/', { name, description, organization_id: organizationId });
  },

  list: async (params?: { search?: string; skip?: number; limit?: number }): Promise<{ teams: Team[]; total: number }> => {
    return api.get('/teams/', { params });
  },

  get: async (teamId: string): Promise<Team> => {
    return api.get(`/teams/${teamId}`);
  },

  update: async (teamId: string, data: { name?: string; description?: string }): Promise<Team> => {
    return api.put(`/teams/${teamId}`, data);
  },

  delete: async (teamId: string): Promise<void> => {
    return api.delete(`/teams/${teamId}`);
  },

  listMembers: async (teamId: string, params?: { skip?: number; limit?: number }): Promise<{ members: TeamMember[]; total: number }> => {
    return api.get(`/teams/${teamId}/members`, { params });
  },

  addMember: async (teamId: string, userId: string, role?: string): Promise<TeamMember> => {
    return api.post(`/teams/${teamId}/members`, { user_id: userId, role });
  },

  removeMember: async (teamId: string, userId: string): Promise<void> => {
    return api.delete(`/teams/${teamId}/members/${userId}`);
  },
};
