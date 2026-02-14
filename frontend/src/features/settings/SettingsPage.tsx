import {
  User,
  Settings as SettingsIcon,
  Database,
  Target,
  Brain
} from 'lucide-react';
import { NavLink, Outlet } from 'react-router-dom';

import { cn } from '../../shared/utils/cn';

export function SettingsPage() {
  const tabs = [
    { to: 'profile', label: 'Perfil Pessoal', icon: User },
    { to: 'memories', label: 'Memórias', icon: Brain },
    { to: 'trainer', label: 'Treinador AI', icon: Target },
    { to: 'integrations', label: 'Integrações', icon: Database },
  ];

  return (
    <div className="flex flex-col h-full space-y-4 md:space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-20">
      {/* Header */}
      <div className="flex-shrink-0">
        <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
          <SettingsIcon className="text-gradient-start" size={32} />
          Configurações
        </h1>
        <p className="text-text-secondary mt-1">Gerencie seu perfil e preferências do app.</p>
      </div>

      {/* Horizontal Tab Navigation */}
      <div className="border-b border-border overflow-x-auto hide-scrollbar flex-shrink-0">
        <nav className="flex gap-1 sm:gap-2 md:gap-4 pb-4 min-w-max md:min-w-0">
          {tabs.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              className={({ isActive }) => cn(
                "flex items-center gap-1 sm:gap-2 px-2 sm:px-3 md:px-4 py-2 rounded-lg text-xs sm:text-sm md:text-base font-medium transition-colors whitespace-nowrap shrink-0 md:shrink",
                isActive
                  ? "bg-gradient-start/10 text-gradient-start border border-gradient-start/20 shadow-orange-sm/5"
                  : "text-text-secondary hover:text-text-primary hover:bg-white/5"
              )}
            >
              <tab.icon size={16} className="sm:w-5 sm:h-5" />
              <span className="hidden sm:inline">{tab.label}</span>
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Content Area */}
      <div className="flex-1 min-h-0 overflow-y-auto pr-2">
        <Outlet />
      </div>
    </div>
  );
}

