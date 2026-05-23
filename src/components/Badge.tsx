import React from 'react';

export type BadgeVariant = 'primary' | 'secondary' | 'high' | 'medium' | 'low' | 'outline' | 'info';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode;
  variant?: BadgeVariant;
}

export const Badge: React.FC<BadgeProps> = ({ 
  children, 
  className = '', 
  variant = 'primary',
  ...props 
}) => {
  const baseClasses = 'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium border transition-colors duration-200 focus:outline-none';
  
  const variantClasses: Record<BadgeVariant, string> = {
    primary: 'bg-navy-800 border-navy-800/80 text-white hover:bg-navy-900',
    secondary: 'bg-slate-100/90 border-slate-200 text-slate-700 hover:bg-slate-200/60 hover:text-slate-900',
    high: 'bg-rose-50/80 border-rose-200/60 text-rose-800 hover:bg-rose-100/60 shadow-sm shadow-rose-100/30',
    medium: 'bg-amber-50/80 border-amber-200/60 text-amber-900 hover:bg-amber-100/60 shadow-sm shadow-amber-100/30',
    low: 'bg-emerald-50/80 border-emerald-200/60 text-emerald-800 hover:bg-emerald-100/60 shadow-sm shadow-emerald-100/30',
    outline: 'border-slate-200/80 text-slate-600 bg-transparent hover:bg-slate-100/50 hover:text-slate-900',
    info: 'bg-blue-50/80 border-blue-200/60 text-blue-800 hover:bg-blue-100/60 shadow-sm shadow-blue-100/30'
  };

  // Add dot indicator for high/medium/low severity badges
  const renderDot = () => {
    if (variant === 'high') {
      return <span className="w-1.5 h-1.5 rounded-full bg-rose-500 shrink-0"></span>;
    }
    if (variant === 'medium') {
      return <span className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0"></span>;
    }
    if (variant === 'low') {
      return <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0"></span>;
    }
    return null;
  };

  return (
    <span 
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {renderDot()}
      {children}
    </span>
  );
};
