'use client';

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { User, Organization } from '../../types';

interface AuthContextType {
  user: User | null;
  organization: Organization | null;
  loading: boolean;
  token: string | null;
  login: (token: string, refreshToken: string) => Promise<void>;
  register: (email: string, fullName: string, orgName: string) => Promise<void>;
  logout: () => void;
  setOrganization: (org: Organization) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('user');
      return saved ? JSON.parse(saved) : null;
    }
    return null;
  });
  const [organization, setOrg] = useState<Organization | null>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('organization');
      return saved ? JSON.parse(saved) : null;
    }
    return null;
  });
  const [token, setToken] = useState<string | null>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('token');
    }
    return null;
  });
  const [loading, setLoading] = useState(false);

  const login = async (accessToken: string, refreshToken: string) => {
    setLoading(true);
    try {
      localStorage.setItem('token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
      setToken(accessToken);

      // Fetch user profile info
      const apiURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
      const res = await fetch(`${apiURL}/auth/me`, {
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!res.ok) {
        throw new Error('Failed to fetch user profile');
      }

      const userData = await res.json();
      setUser(userData);
      localStorage.setItem('user', JSON.stringify(userData));

      if (userData.organizations && userData.organizations.length > 0) {
        const defaultOrg = userData.organizations[0].organization;
        setOrg(defaultOrg);
        localStorage.setItem('organization', JSON.stringify(defaultOrg));
      }
    } catch (err) {
      logout();
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (_email: string, _fullName: string, _orgName: string) => {
    // Endpoint wrapper for registering
    // Actual API request handled in auth page, calls login after completion
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    localStorage.removeItem('organization');
    setUser(null);
    setOrg(null);
    setToken(null);
  };

  const setOrganization = (org: Organization) => {
    setOrg(org);
    localStorage.setItem('organization', JSON.stringify(org));
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        organization,
        loading,
        token,
        login,
        register,
        logout,
        setOrganization,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
