
import React from 'react';

interface LegalIconProps {
  type: 'justice' | 'parliament' | 'gavel' | 'scales' | 'book' | 'document';
  className?: string;
}

const LegalIcon: React.FC<LegalIconProps> = ({ type, className = "w-8 h-8" }) => {
  const icons = {
    justice: (
      <svg viewBox="0 0 100 100" className={className} fill="currentColor">
        <path d="M50 10c-3 0-5 2-5 5v5h-5c-2 0-4 1-4 3v7c0 2 2 3 4 3h20c2 0 4-1 4-3v-7c0-2-2-3-4-3h-5v-5c0-3-2-5-5-5z"/>
        <rect x="30" y="35" width="40" height="50" rx="3" ry="3"/>
        <circle cx="35" cy="45" r="2"/>
        <circle cx="65" cy="45" r="2"/>
        <path d="M40 55h20v3H40zM40 62h20v3H40zM40 69h15v3H40z"/>
        <path d="M25 25l10 5-5 10-10-5zM75 25l-10 5 5 10 10-5z" opacity="0.7"/>
      </svg>
    ),
    parliament: (
      <svg viewBox="0 0 100 100" className={className} fill="currentColor">
        <rect x="10" y="70" width="80" height="20"/>
        <rect x="20" y="30" width="8" height="40"/>
        <rect x="36" y="25" width="8" height="45"/>
        <rect x="52" y="20" width="8" height="50"/>
        <rect x="68" y="25" width="8" height="45"/>
        <rect x="84" y="30" width="8" height="40"/>
        <polygon points="50,5 25,25 75,25"/>
        <rect x="47" y="15" width="6" height="8"/>
      </svg>
    ),
    gavel: (
      <svg viewBox="0 0 100 100" className={className} fill="currentColor">
        <rect x="20" y="30" width="25" height="8" rx="4" transform="rotate(45 32.5 34)"/>
        <rect x="25" y="25" width="15" height="18" rx="2" transform="rotate(45 32.5 34)"/>
        <rect x="50" y="50" width="30" height="6" rx="3" transform="rotate(45 65 53)"/>
        <circle cx="75" cy="75" r="8"/>
        <rect x="70" y="80" width="20" height="4" rx="2"/>
      </svg>
    ),
    scales: (
      <svg viewBox="0 0 100 100" className={className} fill="currentColor">
        <rect x="48" y="20" width="4" height="60"/>
        <rect x="40" y="75" width="20" height="5"/>
        <circle cx="25" cy="40" r="15" fill="none" stroke="currentColor" strokeWidth="2"/>
        <circle cx="75" cy="40" r="15" fill="none" stroke="currentColor" strokeWidth="2"/>
        <path d="M25 25v30M75 25v30M15 40h20M65 40h20" stroke="currentColor" strokeWidth="2"/>
        <path d="M25 25L50 30L75 25" stroke="currentColor" strokeWidth="2" fill="none"/>
      </svg>
    ),
    book: (
      <svg viewBox="0 0 100 100" className={className} fill="currentColor">
        <rect x="20" y="15" width="60" height="70" rx="3"/>
        <rect x="25" y="20" width="50" height="5" rx="2" opacity="0.7"/>
        <rect x="25" y="30" width="40" height="3" rx="1" opacity="0.5"/>
        <rect x="25" y="37" width="45" height="3" rx="1" opacity="0.5"/>
        <rect x="25" y="44" width="35" height="3" rx="1" opacity="0.5"/>
        <rect x="25" y="51" width="42" height="3" rx="1" opacity="0.5"/>
        <rect x="25" y="58" width="38" height="3" rx="1" opacity="0.5"/>
        <rect x="15" y="20" width="5" height="60" rx="2"/>
      </svg>
    ),
    document: (
      <svg viewBox="0 0 100 100" className={className} fill="currentColor">
        <path d="M25 10v80h50V25L60 10H25z"/>
        <path d="M60 10v15h15" fill="background"/>
        <rect x="30" y="30" width="25" height="3" rx="1" opacity="0.7"/>
        <rect x="30" y="37" width="35" height="3" rx="1" opacity="0.7"/>
        <rect x="30" y="44" width="30" height="3" rx="1" opacity="0.7"/>
        <rect x="30" y="51" width="32" height="3" rx="1" opacity="0.7"/>
        <rect x="30" y="58" width="28" height="3" rx="1" opacity="0.7"/>
      </svg>
    )
  };

  return icons[type] || null;
};

export default LegalIcon;
