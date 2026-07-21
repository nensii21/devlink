import React from 'react';

interface OrganizationHeaderProps {
  name: string;
  logoUrl?: string;
  bannerUrl?: string;
  location?: string;
  website?: string;
  isHiring: boolean;
}

export const OrganizationHeader: React.FC<OrganizationHeaderProps> = ({
  name,
  logoUrl,
  bannerUrl,
  location,
  website,
  isHiring,
}) => {
  return (
    <div className="relative rounded-xl border border-gray-800 bg-gray-900/50 overflow-hidden mb-6">
      {/* Banner */}
      <div className="h-32 sm:h-48 w-full bg-gradient-to-r from-blue-900 to-indigo-900 relative">
        {bannerUrl && (
          <img src={bannerUrl} alt={`${name} banner`} className="w-full h-full object-cover" />
        )}
      </div>

      {/* Profile Details Bar */}
      <div className="p-6 pt-0 relative flex flex-col sm:flex-row items-start sm:items-end justify-between gap-4">
        <div className="flex items-end gap-4 -mt-12 sm:-mt-16">
          {/* Logo */}
          <div className="w-24 h-24 sm:w-32 sm:h-32 rounded-xl border-4 border-gray-900 bg-gray-800 overflow-hidden flex items-center justify-center font-bold text-2xl text-white shadow-lg">
            {logoUrl ? (
              <img src={logoUrl} alt={`${name} logo`} className="w-full h-full object-cover" />
            ) : (
              name.slice(0, 2).toUpperCase()
            )}
          </div>

          <div className="mb-2">
            <h1 className="text-2xl sm:text-3xl font-bold text-white flex items-center gap-2">
              {name}
              {isHiring && (
                <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium">
                  Hiring
                </span>
              )}
            </h1>
            {location && <p className="text-sm text-gray-400">{location}</p>}
          </div>
        </div>

        {website && (
          <a
            href={website}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors"
          >
            Visit Website
          </a>
        )}
      </div>
    </div>
  );
};
