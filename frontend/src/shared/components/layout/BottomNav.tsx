import { 
  LayoutDashboard, 
  Dumbbell, 
  Utensils, 
  User, 
  MessageSquare
} from 'lucide-react';
import { NavLink } from 'react-router-dom';

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
  testId: string;
}

function NavItem({ to, icon, label, testId }: NavItemProps) {
  return (
    <NavLink
      to={to}
      data-testid={testId}
      className={({ isActive }) => `
        flex flex-col items-center justify-center flex-1 py-2 transition-colors duration-200
        ${isActive ? 'text-gradient-start' : 'text-text-secondary hover:text-text-primary'}
      `}
    >
      {icon}
      <span className="text-[10px] font-medium mt-1">{label}</span>
    </NavLink>
  );
}

/**
 * BottomNav component for Mobile navigation
 */
export function BottomNav() {
  return (
    <nav className="fixed bottom-0 left-0 right-0 h-16 bg-dark-card border-t border-border flex items-center lg:hidden z-40 safe-area-bottom">
      <NavItem 
        to="/" 
        icon={<LayoutDashboard size={22} />} 
        label="Home" 
        testId="nav-home" 
      />
      <NavItem 
        to="/workouts" 
        icon={<Dumbbell size={22} />} 
        label="Treinos" 
        testId="nav-workouts" 
      />
      <NavItem 
        to="/nutrition" 
        icon={<Utensils size={22} />} 
        label="Nutrição" 
        testId="nav-nutrition" 
      />
      <NavItem 
        to="/body" 
        icon={<User size={22} />} 
        label="Corpo" 
        testId="nav-body" 
      />
      <NavItem 
        to="/chat" 
        icon={<MessageSquare size={22} />} 
        label="Chat" 
        testId="nav-chat" 
      />
    </nav>
  );
}
