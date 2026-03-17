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
      className={({ isActive }: { isActive: boolean }) => `
        flex flex-col items-center justify-center flex-1 py-1.5 px-1 transition-colors duration-150 min-w-0 relative
        ${isActive ? 'text-primary' : 'text-text-muted hover:text-text-primary'}
      `}
    >
      <div className="flex items-center justify-center">
        {icon}
      </div>
      <span className="text-[10px] font-black tracking-tight mt-1 truncate max-w-full hidden xs:block uppercase">{label}</span>
    </NavLink>
  );
}

/**
 * BottomNav component for Mobile navigation
 */
export function BottomNav() {
  const { t } = useTranslation();

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-dark-card/80 backdrop-blur-xl border-t border-white/5 flex flex-col items-center justify-center lg:hidden z-90 safe-area-bottom h-auto">
      <div className="flex items-center justify-between w-full h-16 md:h-18 max-w-md px-2">
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
