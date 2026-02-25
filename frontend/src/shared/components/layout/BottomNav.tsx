import {
  LayoutDashboard,
  Dumbbell,
  Utensils,
  User,
  MessageSquare,
  ShieldAlert,
  Settings
} from 'lucide-react';
import { NavLink } from 'react-router-dom';

import { useAuthStore } from '../../hooks/useAuth';

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  testId: string;
}

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
  const { isAdmin } = useAuthStore();

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-dark-card border-t border-border flex items-center justify-center lg:hidden z-40 safe-area-bottom h-14 md:h-16">
      <div className="flex items-center justify-center w-full h-full">
        <NavItem
          to="/dashboard"
          icon={<LayoutDashboard size={20} />}
          label="Home"
          testId="nav-home"
          end={true}
        />
        <NavItem
          to="/dashboard/workouts"
          icon={<Dumbbell size={20} />}
          label="Treinos"
          testId="nav-workouts"
        />
        <NavItem
          to="/dashboard/body/nutrition"
          icon={<Utensils size={20} />}
          label="Nutrição"
          testId="nav-nutrition"
        />
        <NavItem
          to="/dashboard/body"
          icon={<User size={20} />}
          label="Corpo"
          testId="nav-body"
          end={true}
        />
        <NavItem
          to="/dashboard/chat"
          icon={<MessageSquare size={20} />}
          label="Chat"
          testId="nav-chat"
        />
        <NavItem
          to="/dashboard/settings"
          icon={<Settings size={20} />}
          label="Configurações"
          testId="nav-settings"
        />
        {isAdmin && (
          <NavItem
            to="/dashboard/admin"
            icon={<ShieldAlert size={20} />}
            label="Admin"
            testId="nav-admin"
          />
        )}
      </div>
    </nav>
  );
}
