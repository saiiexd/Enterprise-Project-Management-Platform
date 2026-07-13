export interface User {
  id: string;
  email: string;
  full_name?: string;
  provider: string;
  profile_image_url?: string;
  is_active: boolean;
  is_verified: boolean;
  is_superuser: boolean;
  account_status: string;
  organizations?: OrganizationMember[];
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  description?: string;
  logo_url?: string;
  status: string;
  subscription_tier: string;
  subscription_status: string;
  owner_id?: string;
  settings?: OrganizationSettings;
  created_at: string;
  updated_at: string;
}

export interface OrganizationSettings {
  timezone: string;
  locale: string;
  working_days: number[];
  business_hours: {
    start: string;
    end: string;
  };
  branding?: {
    primary_color?: string;
    logo_url?: string | null;
  };
}

export interface OrganizationMember {
  user_id: string;
  email: string;
  full_name?: string | null;
  role_name: string;
  invitation_status: string;
  joined_at: string;
  organization?: Organization;
}

export interface Team {
  id: string;
  name: string;
  description?: string;
  organization_id: string;
  owner_id?: string;
  created_at: string;
  updated_at: string;
}

export interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  role: string;
  email: string;
  full_name?: string | null;
}

export interface Invitation {
  id: string;
  organization_id: string;
  email: string;
  role_name: string;
  token: string;
  status: string;
  expires_at: string;
  created_at: string;
}
