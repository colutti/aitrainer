import {
  LayoutDashboard,
  MessageSquare,
  Dumbbell,
  LogOut,
  Scale,
  Flame,
  Settings as SettingsIcon
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { NavLink } from 'react-router-dom';

import { useAuthStore } from '../../hooks/useAuth';
import { cn } from '../../utils/cn';
import { UserAvatar } from '../ui/UserAvatar';

const PLAN_BADGE_STYLES: Record<string, string> = {
  Free: 'bg-zinc-700/60 text-zinc-300 border-zinc-600',
  Basic: 'bg-blue-900/50 text-blue-300 border-blue-700',
  Pro: 'bg-orange-900/50 text-orange-300 border-orange-700',
  Premium: 'bg-purple-900/50 text-purple-300 border-purple-700',
};

interface NavItemProps {
  to: string;
  icon: React.ElementType;
  label: string;
  dataTour?: string;
  end?: boolean;
}

function NavItem({ to, icon: Icon, label, dataTour, end = false }: NavItemProps) {
  return (
    <NavLink
      to={to}
      end={end}
      data-tour={dataTour}
      className={({ isActive }) => cn(
        "flex items-center gap-4 px-3 py-3 rounded-md transition-colors duration-150 font-bold text-base",
        isActive
          ? "bg-gradient-start text-white shadow-md shadow-gradient-start/20"
          : "text-text-secondary hover:bg-white/5 hover:text-text-primary"
      )}
    >
      <Icon size={22} className="shrink-0" />
      <span>{label}</span>
    </NavLink>
  );
}

/**
 * Sidebar component for Desktop navigation
 */
export function Sidebar() {
  const { logout, userInfo } = useAuthStore();
  const { t } = useTranslation();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-dark-card border-r border-white/10 hidden lg:flex flex-col px-4 pb-4 pt-5 z-50">
      {/* Brand */}
      <div className="flex items-center gap-4 px-2 mb-10">
        <img
          src="/brand_icon_final.png"
          alt="FityQ"
          className="h-14 w-14 object-contain shrink-0"
        />
        <div>
          <span className="text-3xl font-black text-white tracking-tighter block leading-none">
            FityQ
          </span>
          <span className="text-xs uppercase tracking-widest text-text-muted font-bold mt-1.5 block">
            {t('nav.brand_tagline')}
          </span>
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 flex flex-col gap-0.5 overflow-y-auto hide-scrollbar">
        <NavItem to="/dashboard" icon={LayoutDashboard} label={t('nav.home')} dataTour="tour-nav-home" end={true} />
        <NavItem to="/dashboard/chat" icon={MessageSquare} label={t('nav.trainer')} dataTour="tour-nav-trainer" />
        <NavItem to="/dashboard/workouts" icon={Dumbbell} label={t('nav.workouts')} dataTour="tour-nav-workouts" />
        <NavItem to="/dashboard/body/weight" icon={Scale} label={t('nav.body')} dataTour="tour-nav-body" />
        <NavItem to="/dashboard/body/nutrition" icon={Flame} label={t('nav.nutrition')} dataTour="tour-nav-nutrition" />
      </nav>

      {/* User Info Section */}
      {userInfo && (
        <div className="mt-auto pt-2 border-t border-white/10">
          <div className="flex items-center gap-4 px-1 py-1">
            <UserAvatar photo={userInfo.photo_base64} name={userInfo.name} size="lg" />
            <div className="flex-1 min-w-0">
              {/* Name + badge on the same line */}
              <div className="flex items-center gap-2 flex-wrap">
                <p className="text-lg font-bold text-text-primary leading-tight truncate">{userInfo.name}</p>
                {userInfo.subscription_plan && (
                  <span className={cn(
                    "inline-flex items-center px-2 py-0.5 rounded text-xs font-black uppercase tracking-wider border leading-none shadow-sm",
                    PLAN_BADGE_STYLES[userInfo.subscription_plan] ?? PLAN_BADGE_STYLES.Free
                  )}>
                    {userInfo.subscription_plan}
                  </span>
                )}
              </div>
              {/* Email */}
              <p className="text-[13px] text-text-muted truncate mt-1">{userInfo.email}</p>
              {/* Message count */}
              {typeof userInfo.effective_remaining_messages === 'number' && (
                <div className="mt-2 text-sm text-text-muted border-l-2 border-gradient-start/30 pl-2">
                  <div className="flex items-baseline gap-1">
                    <span className="text-text-primary font-bold">
                      {(userInfo.current_plan_limit ?? 100) - (userInfo.effective_remaining_messages ?? 0)}
                    </span>
                    <span className="text-xs opacity-50">/ {userInfo.current_plan_limit ?? 100}</span>
                  </div>
                  <span className="text-xs uppercase tracking-widest opacity-40 font-bold block">
                    {t('common.msgs')}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Bottom Actions */}
      <div className="pt-4 border-t border-white/10 flex flex-col gap-1">
        <NavLink
          to="/dashboard/settings"
          data-tour="tour-nav-settings"
          className={({ isActive }) => cn(
            "flex items-center gap-4 px-3 py-3 rounded-md transition-colors duration-150 font-bold text-base",
            isActive
              ? "bg-gradient-start text-white shadow-md shadow-gradient-start/20"
              : "text-text-secondary hover:bg-white/5 hover:text-text-primary"
          )}
        >
          <SettingsIcon size={22} className="shrink-0" />
          <span>{t('nav.settings')}</span>
        </NavLink>

        <button
          onClick={() => { logout(); }}
          className="flex items-center gap-4 px-3 py-3 rounded-md text-text-muted hover:bg-red-500/10 hover:text-red-400 transition-colors duration-150 font-bold text-base"
        >
          <LogOut size={22} className="shrink-0" />
          <span>{t('common.logout')}</span>
        </button>
      </div>
    </aside>
  );
}

