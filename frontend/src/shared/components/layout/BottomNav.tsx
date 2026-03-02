import {
  LayoutDashboard,
  Dumbbell,
  Flame,
  Scale,
  MessageSquare,
  Settings
} from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { NavLink } from 'react-router-dom';

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  testId: string;
  dataTour?: string;
  end?: boolean;
}

function NavItem({ to, icon, label, testId, dataTour, end = false }: NavItemProps) {
  return (
    <NavLink
      to={to}
      end={end}
      data-testid={testId}
      data-tour={dataTour}
      className={({ isActive }) => `
        flex flex-col items-center justify-center flex-1 py-2 px-1 transition-all duration-300 min-w-0 relative
        ${isActive ? 'text-gradient-start' : 'text-text-muted hover:text-text-primary'}
      `}
    >
      <div className="relative">
        {icon}
        {/* Subtle active indicator dot */}
        <span className="absolute -top-1 -right-1 w-1.5 h-1.5 rounded-full bg-gradient-start opacity-0 scale-0 transition-all ui-active:opacity-100 ui-active:scale-100" />
      </div>
      <span className="text-[10px] font-bold mt-1 truncate max-w-full hidden xs:block">{label}</span>
    </NavLink>
  );
}

/**
 * BottomNav component for Mobile navigation
 */
export function BottomNav() {
  const { t } = useTranslation();

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-dark-card/80 backdrop-blur-xl border-t border-white/5 flex items-center justify-center lg:hidden z-90 safe-area-bottom h-16 md:h-20 shadow-[0_-10px_40px_rgba(0,0,0,0.5)]">
      <div className="flex items-center justify-between w-full h-full max-w-md px-2">
        <NavItem
          to="/dashboard"
          icon={<LayoutDashboard size={20} />}
          label={t('nav.home')}
          testId="nav-home"
          dataTour="tour-nav-home"
          end={true}
        />
        <NavItem
          to="/dashboard/chat"
          icon={<MessageSquare size={20} />}
          label={t('nav.trainer')}
          testId="nav-chat"
          dataTour="tour-nav-trainer"
        />
        <NavItem
          to="/dashboard/workouts"
          icon={<Dumbbell size={20} />}
          label={t('nav.workouts')}
          testId="nav-workouts"
          dataTour="tour-nav-workouts"
        />
        <NavItem
          to="/dashboard/body/weight"
          icon={<Scale size={20} />}
          label={t('nav.body')}
          testId="nav-body"
          dataTour="tour-nav-body"
          end={true}
        />
        <NavItem
          to="/dashboard/body/nutrition"
          icon={<Flame size={20} />}
          label={t('nav.nutrition')}
          testId="nav-nutrition"
          dataTour="tour-nav-nutrition"
        />
        <NavItem
          to="/dashboard/settings"
          icon={<Settings size={20} />}
          label={t('nav.settings')}
          testId="nav-settings"
          dataTour="tour-nav-settings"
        />
      </div>
    </nav>
  );
}
