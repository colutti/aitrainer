import { 
  LayoutDashboard, 
  Dumbbell, 
  Utensils, 
  User, 
  MessageSquare, 
  Brain,
  Settings, 
  ShieldAlert, 
  LogOut 
} from 'lucide-react';
import { NavLink } from 'react-router-dom';

import { useAuthStore } from '../../hooks/useAuth';

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  label: string;
}

function NavItem({ to, icon, label }: NavItemProps) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) => `
        flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200
        ${isActive 
          ? 'bg-gradient-to-r from-gradient-start to-gradient-end text-white shadow-lg' 
          : 'text-text-secondary hover:bg-white/5 hover:text-text-primary'}
      `}
    >
      {icon}
      <span className="font-medium">{label}</span>
    </NavLink>
  );
}

/**
 * Sidebar component for Desktop navigation
 */
export function Sidebar() {
  const { isAdmin, logout } = useAuthStore();

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-dark-card border-r border-border hidden lg:flex flex-col p-4">
      {/* Brand */}
      <div className="flex items-center gap-2 px-2 py-6 mb-4">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-gradient-start to-gradient-end flex items-center justify-center font-bold text-white shadow-orange">
          F
        </div>
        <span className="text-xl font-bold bg-gradient-to-r from-gradient-start to-gradient-end bg-clip-text text-transparent">
          Fitiq
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 flex flex-col gap-1">
        <NavItem to="/" icon={<LayoutDashboard size={20} />} label="Home" />
        <NavItem to="/workouts" icon={<Dumbbell size={20} />} label="Treinos" />
        <NavItem to="/nutrition" icon={<Utensils size={20} />} label="Nutrição" />
        <NavItem to="/body" icon={<User size={20} />} label="Corpo" />
        <NavItem to="/chat" icon={<MessageSquare size={20} />} label="Chat AI" />
        <NavItem to="/memories" icon={<Brain size={20} />} label="Memórias" />
        <NavItem to="/settings" icon={<Settings size={20} />} label="Configurações" />
        
        {isAdmin && (
          <NavItem to="/admin" icon={<ShieldAlert size={20} />} label="Painel Admin" />
        )}
      </nav>

      {/* Logout */}
      <button
        onClick={logout}
        className="flex items-center gap-3 px-4 py-3 rounded-lg text-text-secondary hover:bg-red-500/10 hover:text-red-400 transition-all duration-200 mt-auto"
      >
        <LogOut size={20} />
        <span className="font-medium">Sair</span>
      </button>
    </aside>
  );
}
