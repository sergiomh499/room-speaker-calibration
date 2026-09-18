import React, { ReactNode } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface CardProps {
  children: ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  badge?: ReactNode;
  icon?: ReactNode;
  action?: ReactNode;
  glow?: 'indigo' | 'emerald' | 'none';
}

export const Card: React.FC<CardProps> = ({
  children,
  className,
  title,
  subtitle,
  badge,
  icon,
  action,
  glow = 'none',
}) => {
  return (
    <div
      className={twMerge(
        clsx(
          'bg-surface-1 border border-border-subtle rounded-xl p-5 transition-all duration-200',
          glow === 'indigo' && 'shadow-[0_0_20px_rgba(99,102,241,0.15)] border-indigo-500/30',
          glow === 'emerald' && 'shadow-[0_0_20px_rgba(16,185,129,0.15)] border-emerald-500/30',
          className
        )
      )}
    >
      {(title || icon || action || badge) && (
        <div className="flex items-center justify-between pb-3 mb-4 border-b border-border-subtle">
          <div className="flex items-center gap-3">
            {icon && <div className="text-indigo-400">{icon}</div>}
            <div>
              {title && <h3 className="text-base font-semibold text-slate-100 tracking-tight">{title}</h3>}
              {subtitle && <p className="text-xs text-slate-400 font-mono mt-0.5">{subtitle}</p>}
            </div>
          </div>
          <div className="flex items-center gap-2">
            {badge}
            {action}
          </div>
        </div>
      )}
      {children}
    </div>
  );
};
