import { LayoutDashboard, Users, FileText, AlignLeft, BarChart3 } from 'lucide-react';
import { NavLink, Outlet } from 'react-router-dom';

import { cn } from '../../../shared/utils/cn';

export function AdminLayout() {
  const tabs = [
    { to: '.', end: true, label: 'Dashboard', icon: LayoutDashboard },
    { to: 'users', label: 'Usuários', icon: Users },
    { to: 'logs', label: 'Logs', icon: FileText }, // or Terminal
    { to: 'prompts', label: 'Prompts', icon: AlignLeft },
    { to: 'tokens', label: 'Tokens', icon: BarChart3 },
  ];

  return (
    <div className="flex flex-col h-full space-y-6">
      <div className="border-b border-border">
        <nav className="flex gap-4 overflow-x-auto pb-4 hide-scrollbar">
          {tabs.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              end={tab.end}
              className={({ isActive }) => cn(
                "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap",
                isActive 
                  ? "bg-gradient-start/10 text-gradient-start border border-gradient-start/20" 
                  : "text-text-secondary hover:text-text-primary hover:bg-white/5"
              )}
            >
              <tab.icon size={18} />
              {tab.label}
            </NavLink>
          ))}
        </nav>
      </div>

      <div className="flex-1 min-h-0">
        <Outlet />
      </div>
    </div>
  );
}
