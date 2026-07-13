import { api } from './api';
import { Organization, OrganizationMember } from '../types';

export const organizationService = {
  create: async (name: string, description?: string): Promise<Organization> => {
    return api.post('/organizations/', { name, description });
  },
  
  getActive: async (): Promise<Organization> => {
    return api.get('/organizations/active');
  },
  
  update: async (orgId: string, data: { name?: string; description?: string; settings?: any }): Promise<Organization> => {
    return api.put(`/organizations/${orgId}`, data);
  },
  
  listMembers: async (
    orgId: string,
    params?: { search?: string; skip?: number; limit?: number }
  ): Promise<{ members: OrganizationMember[]; total: number }> => {
    return api.get(`/organizations/${orgId}/members`, { params });
  },
  
  removeMember: async (orgId: string, userId: string): Promise<void> => {
    return api.delete(`/organizations/${orgId}/members/${userId}`);
  },
  
  updateMemberRole: async (orgId: string, userId: string, roleName: string): Promise<OrganizationMember> => {
    return api.put(`/organizations/${orgId}/members/${userId}/role`, { role_name: roleName });
  },
};
