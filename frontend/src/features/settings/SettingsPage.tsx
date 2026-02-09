import { 
  User, 
  Settings as SettingsIcon, 
  ChevronRight, 
  Database, 
  Target,
  Brain
} from 'lucide-react';
import { NavLink, Outlet } from 'react-router-dom';

import { useAuthStore } from '../../shared/hooks/useAuth';
import { cn } from '../../shared/utils/cn';

export function SettingsPage() {
  const { userInfo } = useAuthStore();

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700 pb-20 h-full flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between flex-shrink-0">
        <div>
          <h1 className="text-3xl font-bold text-text-primary flex items-center gap-3">
            <SettingsIcon className="text-gradient-start" size={32} />
            Configurações
          </h1>
          <p className="text-text-secondary mt-1">Gerencie seu perfil e preferências do app.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8 flex-1 min-h-0 overflow-hidden">
        {/* Navigation Sidebar */}
        <div className="md:col-span-3 space-y-4 overflow-y-auto pr-2">
          <nav className="space-y-1">
            <TabNavLink 
              to="profile" 
              icon={<User size={20} />} 
              label="Perfil Pessoal" 
            />
            <TabNavLink 
              to="memories" 
              icon={<Brain size={20} />} 
              label="Memórias" 
            />
            <TabNavLink 
              to="trainer" 
              icon={<Target size={20} />} 
              label="Treinador AI" 
            />
            <TabNavLink 
              to="integrations" 
              icon={<Database size={20} />} 
              label="Integrações" 
            />
          </nav>

          <div className="pt-4">
            <div className="bg-dark-card border border-border rounded-2xl p-4 text-center">
              <div className="w-16 h-16 rounded-full bg-gradient-start mx-auto mb-3 flex items-center justify-center text-2xl font-bold text-white shadow-orange">
                {userInfo?.name.charAt(0).toUpperCase() ?? 'U'}
              </div>
              <p className="font-bold text-text-primary truncate">{userInfo?.name ?? 'Usuário'}</p>
              <p className="text-xs text-text-muted mt-0.5 truncate">{userInfo?.email}</p>
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="md:col-span-9 h-full overflow-y-auto pr-2 pb-10">
          <Outlet />
        </div>
      </div>
    </div>
  );
}

function TabNavLink({ to, icon, label }: { to: string; icon: React.ReactNode; label: string }) {
  return (
    <NavLink 
      to={to}
      className={({ isActive }) => cn(
        "w-full flex items-center justify-between p-3 rounded-xl transition-all",
        isActive 
          ? "bg-gradient-start/10 text-gradient-start font-bold border border-gradient-start/20 shadow-orange-sm/5" 
          : "text-text-secondary hover:bg-white/5 hover:text-text-primary"
      )}
    >
      {({ isActive }) => (
        <>
          <div className="flex items-center gap-3">
            {icon}
            {label}
          </div>
          <ChevronRight size={16} className={cn("transition-transform duration-200", isActive && "rotate-90 text-gradient-start")} />
        </>
      )}
    </NavLink>
  );
}

