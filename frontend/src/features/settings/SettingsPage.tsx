import {
  User,
  Settings as SettingsIcon,
  Database,
  Target,
  Brain
} from 'lucide-react';
import { NavLink, Outlet } from 'react-router-dom';

import { useAuthStore } from '../../shared/hooks/useAuth';
import { cn } from '../../shared/utils/cn';

export function SettingsPage() {
  const { userInfo } = useAuthStore();

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
      <div className="border-b border-border overflow-x-auto hide-scrollbar">
        <nav className="flex gap-2 md:gap-4 pb-4 min-w-max md:min-w-0">
          {tabs.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              className={({ isActive }) => cn(
                "flex items-center gap-2 px-3 md:px-4 py-2 rounded-lg text-sm md:text-base font-medium transition-colors whitespace-nowrap shrink-0 md:shrink",
                isActive
                  ? "bg-gradient-start/10 text-gradient-start border border-gradient-start/20 shadow-orange-sm/5"
                  : "text-text-secondary hover:text-text-primary hover:bg-white/5"
              )}
            >
              <tab.icon size={20} />
              <span>{tab.label}</span>
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Content with Responsive Sidebar */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
          {/* Main Content Area */}
          <div className="lg:col-span-2 min-h-0 overflow-y-auto pr-2">
            <Outlet />
          </div>

          {/* User Info Sidebar - Hidden on mobile, visible on lg+ */}
          <div className="hidden lg:block min-h-0 overflow-y-auto">
            <UserInfoPanel userInfo={userInfo} />
          </div>
        </div>
      </div>

      {/* User Info Panel for Mobile - Shown below content */}
      <div className="lg:hidden" data-testid="user-info-container">
        <UserInfoPanel userInfo={userInfo} />
      </div>
    </div>
  );
}

function UserInfoPanel({ userInfo }: { userInfo: any }) {
  return (
    <div className="bg-dark-card border border-border rounded-2xl p-4 text-center sticky top-0">
      <div className="w-16 h-16 rounded-full bg-gradient-start mx-auto mb-3 flex items-center justify-center text-2xl font-bold text-white shadow-orange">
        {userInfo?.name.charAt(0).toUpperCase() ?? 'U'}
      </div>
      <p className="font-bold text-text-primary truncate">{userInfo?.name ?? 'Usuário'}</p>
      <p className="text-xs text-text-muted mt-0.5 truncate">{userInfo?.email}</p>
    </div>
  );
}

