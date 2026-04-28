import {
  User,
  Database,
  Target,
  Brain,
  CreditCard
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { NavLink, Outlet } from 'react-router-dom';

import { InsightScreen } from '../../shared/components/layout/InsightScreen';
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
    <div data-testid="settings-insight-screen">
      <InsightScreen
        title={t('settings.title')}
        subtitle={t('settings.subtitle')}
        actions={
          <nav className="grid grid-cols-5 gap-1 surface-card rounded-2xl p-1.5 border-[color:var(--color-outline-variant)] w-full lg:w-fit md:flex md:rounded-full md:overflow-x-auto hide-scrollbar max-w-full">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <NavLink
                  key={tab.to}
                  to={tab.to}
                  aria-label={tab.label}
                  className={({ isActive }) => cn(
                    "flex items-center justify-center gap-1.5 md:gap-2 px-0.5 md:px-4 lg:px-6 py-2 rounded-xl md:rounded-full text-[10px] md:text-xs font-semibold transition-all uppercase tracking-wider lg:tracking-[0.05em] whitespace-nowrap",
                    isActive
                      ? "bg-white text-black "
                      : "text-text-muted hover:text-text-secondary hover:bg-[color:var(--color-surface-container)]"
                  )}
                >
                  <Icon size={16} className="shrink-0" />
                  <span className="sr-only md:not-sr-only md:inline">{tab.label}</span>
                </NavLink>
              );
            })}
          </nav>
        }
        content={
          <div className={cn(PREMIUM_UI.animation.fadeIn, 'flex flex-col space-y-8 pb-20 min-h-[500px]')}>
            <Outlet />
          </div>
        }
      />
    </div>
  );
}
