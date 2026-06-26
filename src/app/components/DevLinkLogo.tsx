import React from 'react';

interface DevLinkLogoProps {
  className?: string;
  size?: number;
  hideText?: boolean;
}

export const DevLinkLogo: React.FC<DevLinkLogoProps> = ({ className, size = 32, hideText = false }) => {
  return (
    <div className={`flex items-center gap-2.5 ${className || ''}`}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="shrink-0"
      >
        <defs>
          <linearGradient
            id="logo-gradient"
            x1="10"
            y1="10"
            x2="34"
            y2="34"
            gradientUnits="userSpaceOnUse"
          >
            <stop stopColor="#3B82F6" />
            <stop offset="1" stopColor="#2563EB" />
          </linearGradient>
        </defs>
        {/* The 'd' shape body */}
        <circle cx="18" cy="24" r="10" stroke="url(#logo-gradient)" strokeWidth="6" />
        {/* The 'd' shape stem */}
        <path
          d="M28 8V34"
          stroke="url(#logo-gradient)"
          strokeWidth="6"
          strokeLinecap="round"
        />
      </svg>
      {!hideText && (
        <span className="text-xl font-bold tracking-tight text-text-primary">devlink</span>
      )}
    </div>
  );
};
