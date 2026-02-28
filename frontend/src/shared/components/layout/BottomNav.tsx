import {
  LayoutDashboard,
  Dumbbell,
  Utensils,
  User,
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
  end?: boolean;
}

function NavItem({ to, icon, label, testId, end = false }: NavItemProps) {
  return (
    <NavLink
      to={to}
      end={end}
      data-testid={testId}
      className={({ isActive }) => `
        flex flex-col items-center justify-center flex-1 py-1 px-1 transition-colors duration-200 min-w-0
        ${isActive ? 'text-gradient-start' : 'text-text-secondary hover:text-text-primary'}
      `}
    >
      {icon}
      <span className="text-[8px] md:text-[10px] font-medium mt-0.5 truncate">{label}</span>
    </NavLink>
  );
}

/**
 * BottomNav component for Mobile navigation
 */
export function BottomNav() {
  const { t } = useTranslation();

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-dark-card border-t border-border flex items-center justify-center lg:hidden z-40 safe-area-bottom h-14 md:h-16">
      <div className="flex items-center justify-center w-full h-full">
        <NavItem
          to="/dashboard"
          icon={<LayoutDashboard size={20} />}
          label={t('nav.home')}
          testId="nav-home"
          end={true}
        />
        <NavItem
          to="/dashboard/workouts"
          icon={<Dumbbell size={20} />}
          label={t('nav.workouts')}
          testId="nav-workouts"
        />
        <NavItem
          to="/dashboard/body/nutrition"
          icon={<Utensils size={20} />}
          label={t('nav.nutrition')}
          testId="nav-nutrition"
        />
        <NavItem
          to="/dashboard/body"
          icon={<User size={20} />}
          label={t('nav.body')}
          testId="nav-body"
          end={true}
        />
        <NavItem
          to="/dashboard/chat"
          icon={<MessageSquare size={20} />}
          label={t('nav.trainer')}
          testId="nav-chat"
        />
        <NavItem
          to="/dashboard/settings"
          icon={<Settings size={20} />}
          label={t('nav.settings')}
          testId="nav-settings"
        />
      </div>
    </nav>
  );
}
