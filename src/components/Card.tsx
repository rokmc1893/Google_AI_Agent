import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  variant?: 'dashboard' | 'document' | 'glass' | 'glowing' | 'default';
}

export const Card: React.FC<CardProps> = ({ 
  children, 
  className = '', 
  variant = 'default',
  ...props 
}) => {
  // Constraints: p-6 minimum for dashboards, p-8 for document views
  const paddingClass = 
    variant === 'document' ? 'p-8' : 
    variant === 'dashboard' ? 'p-6' : 
    'p-6';

  let variantClass = '';
  switch (variant) {
    case 'dashboard':
      variantClass = 'bg-white border border-slate-200/95 rounded-2xl shadow-sm hover:shadow-md hover:-translate-y-0.5 hover:border-slate-300/80 transition-all duration-300 radial-glow-navy';
      break;
    case 'document':
      variantClass = 'paper-document rounded-2xl';
      break;
    case 'glass':
      variantClass = 'glass-card rounded-2xl shadow-sm hover:shadow-md transition-all duration-300 border-white/60';
      break;
    case 'glowing':
      variantClass = 'bg-white border border-slate-200/95 rounded-2xl shadow-sm animate-border-glow transition-all duration-300 radial-glow-navy';
      break;
    default:
      variantClass = 'bg-white border border-slate-200 rounded-2xl';
  }

  return (
    <div 
      className={`${variantClass} ${paddingClass} ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, className = '', ...props }) => (
  <div className={`flex flex-col space-y-1.5 mb-4 ${className}`} {...props}>
    {children}
  </div>
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ children, className = '', ...props }) => (
  <h3 className={`text-lg font-bold leading-none tracking-tight text-slate-900 ${className}`} {...props}>
    {children}
  </h3>
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({ children, className = '', ...props }) => (
  <p className={`text-xs text-slate-500 font-medium ${className}`} {...props}>
    {children}
  </p>
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, className = '', ...props }) => (
  <div className={`text-slate-900 ${className}`} {...props}>
    {children}
  </div>
);

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ children, className = '', ...props }) => (
  <div className={`flex items-center pt-4 border-t border-slate-200 mt-4 ${className}`} {...props}>
    {children}
  </div>
);
