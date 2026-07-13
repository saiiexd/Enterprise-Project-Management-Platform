import { api } from './api';
import { Invitation } from '../types';

export const invitationService = {
  invite: async (email: string, roleName: string): Promise<Invitation> => {
    return api.post('/invitations/', { email, role_name: roleName });
  },

  list: async (params?: { skip?: number; limit?: number }): Promise<{ invitations: Invitation[]; total: number }> => {
    return api.get('/invitations/', { params });
  },

  resend: async (invitationId: string): Promise<Invitation> => {
    return api.post(`/invitations/${invitationId}/resend`);
  },

  cancel: async (invitationId: string): Promise<void> => {
    return api.post(`/invitations/${invitationId}/cancel`);
  },

  accept: async (token: string): Promise<any> => {
    return api.post('/invitations/accept', { token });
  },

  reject: async (token: string): Promise<any> => {
    return api.post('/invitations/reject', { token });
  },
};
