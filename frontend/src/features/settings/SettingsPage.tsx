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

import { PREMIUM_UI } from '../../shared/styles/ui-variants';
import { cn } from '../../shared/utils/cn';

export default function SettingsPage() {
  const { t } = useTranslation();
  
  const tabs = [
    { to: 'profile', label: t('settings.tabs.profile'), icon: User },
    { to: 'subscription', label: t('settings.tabs.subscription', 'Assinatura'), icon: CreditCard },
    { to: 'memories', label: t('settings.tabs.memories'), icon: Brain },
    { to: 'trainer', label: t('settings.tabs.trainer'), icon: Target },
    { to: 'integrations', label: t('settings.tabs.integrations'), icon: Database },
  ];

  return (
    <div className={cn(PREMIUM_UI.animation.fadeIn, "flex flex-col space-y-8 pb-20")}>
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
        <div>
          <h1 className={cn(PREMIUM_UI.text.heading, "flex items-center")}>
            <SettingsIcon className="mr-3 text-indigo-400 shrink-0" size={32} />
            <span className="leading-tight">{t('settings.title')}</span>
          </h1>
          <p className={PREMIUM_UI.text.label}>{t('settings.subtitle')}</p>
        </div>

        {/* PILL TABS */}
        <nav className="grid grid-cols-5 gap-0.5 bg-white/5 backdrop-blur-md rounded-2xl p-1 border border-white/5 w-full lg:w-fit md:flex md:rounded-full md:overflow-x-auto hide-scrollbar max-w-full">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <NavLink
                key={tab.to}
                to={tab.to}
                aria-label={tab.label}
                className={({ isActive }) => cn(
                  "flex items-center justify-center gap-1.5 md:gap-2 px-0.5 md:px-4 lg:px-6 py-2 rounded-xl md:rounded-full text-[10px] md:text-xs font-black transition-all uppercase tracking-wider lg:tracking-widest whitespace-nowrap",
                  isActive 
                    ? "bg-white text-black shadow-lg" 
                    : "text-zinc-500 hover:text-zinc-300"
                )}
              >
                <Icon size={16} className="shrink-0" />
                <span className="sr-only md:not-sr-only md:inline">{tab.label}</span>
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Content Area */}
      <div className="flex-1 min-h-[500px]">
        <Outlet />
      </div>
    </div>
  );
}
