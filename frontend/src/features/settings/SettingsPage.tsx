import {
  User,
  Settings as SettingsIcon,
  Database,
  Target,
  Brain,
  CreditCard
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { NavLink, Outlet } from 'react-router-dom';

import { cn } from '../../shared/utils/cn';

export function SettingsPage() {
  const { t } = useTranslation();
  
  const tabs = [
    { to: 'profile', label: t('settings.tabs.profile'), icon: User },
    { to: 'subscription', label: t('settings.tabs.subscription', 'Assinatura'), icon: CreditCard },
    { to: 'memories', label: t('settings.tabs.memories'), icon: Brain },
    { to: 'trainer', label: t('settings.tabs.trainer'), icon: Target },
    { to: 'integrations', label: t('settings.tabs.integrations'), icon: Database },
  ];

  return (
    <div className="flex flex-col h-full space-y-4 md:space-y-6 pb-20">
      {/* Header */}
      <div className="shrink-0">
        <h1 className="text-3xl font-black text-text-primary flex items-center gap-3 tracking-tight">
          <SettingsIcon className="text-primary" size={32} />
          {t('settings.title')}
        </h1>
        <p className="text-text-secondary mt-1 text-sm font-medium">{t('settings.subtitle')}</p>
      </div>

      {/* Horizontal Tab Navigation */}
      <div className="border-b border-border overflow-x-auto hide-scrollbar shrink-0">
        <nav className="flex flex-wrap gap-1 sm:gap-2 md:gap-4 pb-4 w-full">
          {tabs.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              className={({ isActive }) => cn(
                "flex items-center gap-1 sm:gap-2 px-2 sm:px-3 md:px-4 py-2 rounded text-xs sm:text-sm md:text-base font-black uppercase tracking-widest transition-colors duration-150 whitespace-nowrap shrink-0 md:shrink",
                isActive
                  ? "bg-primary/10 text-primary border border-primary/20"
                  : "text-text-muted hover:text-text-primary hover:bg-white/5"
              )}
            >
              <tab.icon size={18} className="sm:w-5 sm:h-5" />
              <span>{tab.label}</span>
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

