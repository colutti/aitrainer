import { LayoutDashboard, Users, FileText, AlignLeft, BarChart3 } from 'lucide-react';
import { NavLink, Outlet } from 'react-router-dom';

import { cn } from '../../../../../src/shared/utils/cn';

export function AdminLayout() {
  const tabs = [
    { to: '.', end: true, label: 'Dashboard', icon: LayoutDashboard },
    { to: 'users', label: 'Usuários', icon: Users },
    { to: 'logs', label: 'Logs', icon: FileText }, // or Terminal
    { to: 'prompts', label: 'Prompts', icon: AlignLeft },
    { to: 'tokens', label: 'Tokens', icon: BarChart3 },
  ];

  return (
    <div className="flex flex-col h-full space-y-4 md:space-y-6">
      <div className="border-b border-border overflow-x-auto hide-scrollbar">
        <nav className="flex gap-2 md:gap-4 pb-4 min-w-max md:min-w-0">
          {tabs.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              end={tab.end}
              className={({ isActive }) => cn(
                "flex items-center gap-1 md:gap-2 px-2 md:px-4 py-2 rounded-lg text-xs md:text-sm font-medium transition-colors whitespace-nowrap shrink-0 md:shrink",
                isActive
                  ? "bg-gradient-start/10 text-gradient-start border border-gradient-start/20"
                  : "text-text-secondary hover:text-text-primary hover:bg-white/5"
              )}
            >
              <tab.icon size={16} className="md:w-[18px] md:h-[18px]" />
              <span className="hidden sm:inline">{tab.label}</span>
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="flex-1 min-h-0 overflow-hidden">
        <Outlet />
      </div>
    </div>
  );
}
