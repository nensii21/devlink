import React, { useState } from 'react';
import { OrganizationHeader } from './OrganizationHeader';

interface OrganizationProfileProps {
  organizationData: {
    name: string;
    logo_url?: string;
    banner_url?: string;
    location?: string;
    website?: string;
    description?: string;
    hiring: boolean;
  };
}

export const OrganizationProfile: React.FC<OrganizationProfileProps> = ({ organizationData }) => {
  const [activeTab, setActiveTab] = useState<'about' | 'team' | 'projects' | 'hiring'>('about');

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <OrganizationHeader
        name={organizationData.name}
        logoUrl={organizationData.logo_url}
        bannerUrl={organizationData.banner_url}
        location={organizationData.location}
        website={organizationData.website}
        isHiring={organizationData.hiring}
      />

      {/* Tabs */}
      <div className="flex border-b border-gray-800 mb-6 gap-6">
        {(['about', 'team', 'projects', 'hiring'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 text-sm font-medium capitalize border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-indigo-500 text-indigo-400'
                : 'border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-gray-900/30 border border-gray-800 rounded-xl p-6">
        {activeTab === 'about' && (
          <div>
            <h2 className="text-xl font-semibold text-white mb-3">About Us</h2>
            <p className="text-gray-300 leading-relaxed">
              {organizationData.description || 'No description provided.'}
            </p>
          </div>
        )}

        {activeTab === 'team' && (
          <div>
            <h2 className="text-xl font-semibold text-white mb-4">Team Members</h2>
            <p className="text-gray-400 text-sm">Showing team members connected to {organizationData.name}.</p>
          </div>
        )}

        {activeTab === 'projects' && (
          <div>
            <h2 className="text-xl font-semibold text-white mb-4">Projects</h2>
            <p className="text-gray-400 text-sm">Projects built or maintained by {organizationData.name}.</p>
          </div>
        )}

        {activeTab === 'hiring' && (
          <div>
            <h2 className="text-xl font-semibold text-white mb-4">Open Roles</h2>
            {organizationData.hiring ? (
              <p className="text-gray-300 text-sm">We are actively recruiting talent! Apply below.</p>
            ) : (
              <p className="text-gray-400 text-sm">We are not actively hiring right now.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};