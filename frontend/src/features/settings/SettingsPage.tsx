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
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <p className={PREMIUM_UI.text.label}>{t('settings.subtitle')}</p>
          <h1 className={PREMIUM_UI.text.heading}>
            <SettingsIcon className="inline-block mr-3 text-indigo-400 mb-1" size={32} />
            {t('settings.title')}
          </h1>
        </div>

        {/* PILL TABS */}
        <nav className="grid grid-cols-2 gap-1 bg-white/5 backdrop-blur-md rounded-2xl p-1 border border-white/5 w-full md:w-fit md:flex md:rounded-full md:overflow-x-auto md:hide-scrollbar shrink-0 max-w-full">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <NavLink
                key={tab.to}
                to={tab.to}
                className={({ isActive }) => cn(
                  "flex items-center justify-center gap-2 px-3 md:px-6 py-2 rounded-xl md:rounded-full text-[10px] md:text-xs font-black transition-all uppercase tracking-widest whitespace-nowrap",
                  isActive 
                    ? "bg-white text-black shadow-lg" 
                    : "text-zinc-500 hover:text-zinc-300"
                )}
              >
                <Icon size={14} />
                <span>{tab.label}</span>
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
