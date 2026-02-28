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

interface NavItemProps {
  to: string;
  icon: React.ElementType; // Better way to pass icons
  label: string;
  end?: boolean;
}

function NavItem({ to, icon: Icon, label, end = false }: NavItemProps) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) => cn(
        "flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 font-medium",
        isActive 
          ? "bg-gradient-to-r from-gradient-start to-gradient-end text-white shadow-primary" 
          : "text-text-secondary hover:bg-white/5 hover:text-text-primary"
      )}
    >
      <Icon size={20} className="shrink-0" />
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
    <aside className="fixed left-0 top-0 h-screen w-72 bg-dark-card border-r border-white/5 hidden lg:flex flex-col p-6 z-50 shadow-2xl">
      {/* Brand */}
      <div className="flex flex-col items-center gap-4 py-8 mb-8 relative">
        <div className="absolute inset-0 bg-gradient-to-b from-gradient-start/5 to-transparent rounded-3xl -m-2 opacity-50" />
        <img 
          src="/brand_icon_final.png" 
          alt="FityQ"
          className="h-32 w-32 object-contain drop-shadow-[0_0_15px_rgba(235,93,29,0.4)] filter brightness-110 relative z-10"
        />
        <div className="text-center relative z-10">
          <span className="text-2xl font-black bg-gradient-to-r from-white to-white/60 bg-clip-text text-transparent tracking-[0.2em] block">
            FityQ
          </span>
          <span className="text-[10px] uppercase tracking-[0.4em] text-gradient-start font-bold">
            {t('nav.brand_tagline')}
          </span>
        </div>
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 flex flex-col gap-1 overflow-y-auto hide-scrollbar">
        <NavItem to="/dashboard" icon={LayoutDashboard} label={t('nav.home')} end={true} />
        <NavItem to="/dashboard/chat" icon={MessageSquare} label={t('nav.trainer')} />
        <NavItem to="/dashboard/workouts" icon={Dumbbell} label={t('nav.workouts')} />
        <NavItem to="/dashboard/body/weight" icon={Scale} label={t('nav.body')} />
        <NavItem to="/dashboard/body/nutrition" icon={Flame} label={t('nav.nutrition')} />
      </nav>

      {/* User Info Section */}
      {userInfo && (
        <div className="mt-auto pt-6 border-t border-border mb-4">
          <div className="flex items-center gap-3 px-3 py-3 bg-white/5 rounded-xl">
            <UserAvatar photo={userInfo.photo_base64} name={userInfo.name} size="md" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-text-primary truncate">{userInfo.name}</p>
              <p className="text-xs text-text-muted truncate">{userInfo.email}</p>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Actions / Settings Section */}
      <div className="pt-6 border-t border-border flex flex-col gap-1">
        <NavItem to="/dashboard/settings" icon={SettingsIcon} label={t('nav.settings')} />

        <button
          onClick={() => { logout(); }}
          className="flex items-center gap-3 px-4 py-3 rounded-xl text-text-muted hover:bg-red-500/10 hover:text-red-400 transition-all duration-200 mt-2"
        >
          <LogOut size={20} className="shrink-0" />
          <span className="font-medium">{t('common.logout')}</span>
        </button>
      </div>
    </aside>
  );
}

