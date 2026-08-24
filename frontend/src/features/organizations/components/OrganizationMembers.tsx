import React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/api';
import { OrganizationMember, OrganizationMemberRole } from '../types';
import { usePermissions } from '../hooks/usePermissions';
import { RequirePermission } from './RequirePermission';

interface OrganizationMembersProps {
  orgId: string;
}

const ROLES: OrganizationMemberRole[] = ['owner', 'admin', 'recruiter', 'maintainer', 'member'];

export function OrganizationMembers({ orgId }: OrganizationMembersProps) {
  const queryClient = useQueryClient();
  const { can } = usePermissions(orgId);

  const { data: members, isLoading } = useQuery({
    queryKey: ['organizations', orgId, 'members'],
    queryFn: async () => {
      const res = await api.get<OrganizationMember[]>(`/organizations/${orgId}/members`);
      return res;
    },
  });

  const updateRoleMutation = useMutation({
    mutationFn: async ({ userId, role }: { userId: string; role: OrganizationMemberRole }) => {
      const res = await api.patch<OrganizationMember>(`/organizations/${orgId}/members/${userId}`, { role });
      return res;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['organizations', orgId, 'members'] });
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || "Failed to update role");
    }
  });

  const removeMemberMutation = useMutation({
    mutationFn: async (userId: string) => {
      await api.delete(`/organizations/${orgId}/members/${userId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['organizations', orgId, 'members'] });
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || "Failed to remove member");
    }
  });

  if (isLoading) return <div className="text-muted-foreground">Loading members...</div>;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="mb-2 text-xl font-semibold text-foreground">Organization Members</h2>
          <p className="text-sm text-muted-foreground">Manage who has access to this organization.</p>
        </div>
      </div>

      <div className="overflow-hidden rounded-lg border border-border bg-card">
        <table className="w-full text-left text-sm text-foreground">
          <thead className="bg-muted text-muted-foreground">
            <tr>
              <th className="px-6 py-4 font-medium">Member</th>
              <th className="px-6 py-4 font-medium">Joined</th>
              <th className="px-6 py-4 font-medium">Role</th>
              <th className="px-6 py-4 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {members?.map((member) => (
              <tr key={member.id} className="transition-colors hover:bg-muted/60">
                <td className="px-6 py-4">
                  <div className="font-medium text-foreground">
                    {member.user?.full_name || member.user?.username || member.user_id}
                  </div>
                </td>
                <td className="px-6 py-4 text-muted-foreground">
                  {new Date(member.joined_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4">
                  <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium capitalize text-muted-foreground">
                    {member.role}
                  </span>
                </td>
                <td className="px-6 py-4 text-right">
                  <RequirePermission orgId={orgId} permission="members:manage">
                    <div className="flex justify-end gap-3 items-center">
                      <select
                        className="rounded border border-input bg-background text-sm text-foreground focus:ring-2 focus:ring-ring"
                        value={member.role}
                        onChange={(e) => updateRoleMutation.mutate({ 
                          userId: member.user_id, 
                          role: e.target.value as OrganizationMemberRole 
                        })}
                        disabled={updateRoleMutation.isPending}
                      >
                        {ROLES.map(role => (
                          <option key={role} value={role}>{role}</option>
                        ))}
                      </select>
                      <button
                        onClick={() => {
                          if (window.confirm("Remove this member?")) {
                            removeMemberMutation.mutate(member.user_id);
                          }
                        }}
                        className="text-red-400 hover:text-red-300 text-sm font-medium"
                        disabled={removeMemberMutation.isPending}
                      >
                        Remove
                      </button>
                    </div>
                  </RequirePermission>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
