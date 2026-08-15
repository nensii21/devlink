import { useQuery } from '@tanstack/react-query';
import { api } from '@/api';
import { OrganizationMember, Permission } from '../types';
import { hasPermission } from '../permissions';

// Temporary hook until full organization context is implemented
export function useOrganization(orgId: string) {
  // In a real implementation, we'd fetch the current user's membership
  // Since we don't have the user context easily here without more setup, 
  // we'll simulate fetching members and finding the current user.
  const { data: members, isLoading } = useQuery({
    queryKey: ['organizations', orgId, 'members'],
    queryFn: async () => {
      const res = await api.get<OrganizationMember[]>(`/organizations/${orgId}/members`);
      return res;
    },
  });

  // We are assuming a way to get current user ID here, e.g., from auth context
  // For the sake of this feature, we will just return the first owner if it's mock
  // In a real app, replace `currentUserId` with the actual user ID.
  const currentUserId = "current-user-uuid"; // placeholder
  
  const membership = members?.find(m => m.user_id === currentUserId) || members?.[0]; // mock fallback

  return { membership, isLoading, members };
}

export function usePermissions(orgId: string) {
  const { membership, isLoading } = useOrganization(orgId);

  const can = (permission: Permission) =>
    membership ? hasPermission(membership.role, permission) : false;

  return {
    role: membership?.role,
    can,
    isLoading,
  };
}
