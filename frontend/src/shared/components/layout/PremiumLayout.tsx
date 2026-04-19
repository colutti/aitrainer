import { ClipboardList, Home, Scale, Dumbbell, Settings, MessageCircle, LogOut } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Outlet, NavLink, useLocation } from 'react-router-dom';

import { useAuthStore } from '../../hooks/useAuth';
import { useDemoMode } from '../../hooks/useDemoMode';
import { useInactivityLogout } from '../../hooks/useInactivityLogout';
import { useTokenRefresh } from '../../hooks/useTokenRefresh';
import { cn } from '../../utils/cn';
import { Button } from '../ui/Button';
import { LanguageSelector } from '../ui/LanguageSelector';
import { QuickAddFAB } from '../ui/QuickAddFAB';

import { getLayoutMode } from './layoutModes';

/**
 * PremiumLayout component
 * 
 * Expanded max-width for 1080p/4k displays.
 * Integrated Language Switcher and Logo.
 */
export function PremiumLayout() {
  const { userInfo, logout } = useAuthStore();
  const { t } = useTranslation();
  const { isReadOnly: isDemoUser } = useDemoMode();
  const location = useLocation();
  
  // Initialize session management hooks
  useInactivityLogout();
  useTokenRefresh();

  const isChatPage = location.pathname.includes('/chat');
  const isSubscriptionPage = location.pathname.includes('/settings/subscription');
  const layoutMode = getLayoutMode(location.pathname);
  // Helper to check if a path is active (including sub-routes)
  const isPathActive = (path: string) => {
    if (path === '/dashboard') return location.pathname === '/dashboard';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="h-[100dvh] bg-[color:var(--color-app-bg)] text-zinc-50 font-sans selection:bg-white/15 relative overflow-hidden flex flex-col">
      {/* --- DESKTOP TOP NAV (DOCK) --- */}
      <nav
        data-testid="desktop-nav"
        id="desktop-nav"
        className={cn(
          'hidden md:flex fixed top-0 left-0 right-0 h-20 items-center z-50 bg-[color:var(--color-app-bg)] border-b border-white/8',
          layoutMode.navClassName
        )}
      >
        <div className="flex-1 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center overflow-hidden p-1.5">
            <img src="/logo_icon.png" alt="FityQ Logo" className="w-full h-full object-contain" />
          </div>
          <span className="font-black tracking-widest uppercase text-base bg-gradient-to-r from-white to-zinc-500 bg-clip-text text-transparent">FityQ</span>
          {isDemoUser && (
            <span className="px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-[0.2em] text-amber-300 border border-amber-500/30 bg-amber-500/10">
              Demo Read-Only
            </span>
          )}
        </div>
        
        <div className="flex-1 flex justify-center">
          <div className="flex bg-white/5 backdrop-blur-md rounded-full p-1 border border-white/5">
            <NavLink to="/dashboard" end data-testid="desktop-nav-home" className={({ isActive }) => cn("px-6 py-2 rounded-full text-sm font-semibold transition-all", isActive ? "bg-white/10 text-white shadow-lg" : "text-zinc-400 hover:text-zinc-200")}>
              {t('nav.home')}
            </NavLink>
            <NavLink to="/dashboard/plan" data-testid="desktop-nav-plan" className={() => cn("px-6 py-2 rounded-full text-sm font-semibold transition-all", isPathActive('/dashboard/plan') ? "bg-white/10 text-white shadow-lg" : "text-zinc-400 hover:text-zinc-200")}>
              {t('nav.plan')}
            </NavLink>
            <NavLink to="/dashboard/workouts" data-testid="desktop-nav-workouts" className={() => cn("px-6 py-2 rounded-full text-sm font-semibold transition-all", isPathActive('/dashboard/workouts') ? "bg-white/10 text-white shadow-lg" : "text-zinc-400 hover:text-zinc-200")}>
              {t('nav.workouts')}
            </NavLink>
            <NavLink to="/dashboard/body" data-testid="desktop-nav-body" className={() => cn("px-6 py-2 rounded-full text-sm font-semibold transition-all", isPathActive('/dashboard/body') ? "bg-white/10 text-white shadow-lg" : "text-zinc-400 hover:text-zinc-200")}>
              {t('nav.body')}
            </NavLink>
            <NavLink to="/dashboard/chat" data-testid="desktop-nav-chat" className={() => cn("px-6 py-2 rounded-full text-sm font-semibold transition-all", isPathActive('/dashboard/chat') ? "bg-white/10 text-white shadow-lg" : "text-zinc-400 hover:text-zinc-200")}>
              {t('nav.chat')}
            </NavLink>
          </div>
        </div>

        <div className="flex-1 flex justify-end items-center gap-4">
          {/* Language Switcher in Top Nav */}
          <div className="mr-2">
            <LanguageSelector />
          </div>

          <div data-testid="nav-subscription-status" className="hidden lg:flex flex-col items-end mr-2">
             <span className="text-[9px] font-black uppercase tracking-[0.2em] text-zinc-500">Membro</span>
             <span className="text-[10px] font-black text-indigo-400 border border-indigo-500/20 bg-indigo-500/5 px-2 py-0.5 rounded shadow-sm">{userInfo?.subscription_plan ?? 'Free'}</span>
          </div>
          <NavLink to="/dashboard/settings" data-testid="desktop-nav-settings" className={({ isActive }) => cn("p-2.5 rounded-xl transition-all border", isActive ? "bg-white/10 border-white/10 text-white" : "border-transparent text-zinc-400 hover:bg-white/5 hover:text-zinc-200")}>
            <Settings size={20} />
          </NavLink>
          <Button
            type="button"
            data-testid="desktop-logout"
            onClick={logout}
            className="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-sm font-bold tracking-wide text-zinc-300 transition-all hover:bg-white/10 hover:text-white"
          >
            Logout
          </Button>
          <div className="w-10 h-10 rounded-xl bg-zinc-800 border border-white/10 overflow-hidden flex items-center justify-center shadow-inner">
            {userInfo?.photo_base64 ? (
              <img src={userInfo.photo_base64} alt="Profile" className="w-full h-full object-cover" />
            ) : (
              <span className="font-bold text-zinc-400">{userInfo?.name.charAt(0) ?? 'U'}</span>
            )}
          </div>
        </div>
      </nav>

      {/* --- MOBILE HEADER --- */}
      <header className="md:hidden sticky top-0 z-40 bg-[color:var(--color-app-bg)] px-4 py-3 pt-7 flex flex-col gap-2 border-b border-white/8">
        <div className="flex items-center justify-between gap-3">
          <div className="w-9 h-9 rounded-xl bg-white/5 border border-white/10 p-1 flex items-center justify-center">
             <img src="/logo_icon.png" alt="Logo" className="w-full h-full object-contain opacity-80" />
          </div>
          <div className="flex-1">
            <p className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">FityQ Premium</p>
            <p className="text-sm font-black text-white leading-tight">{userInfo?.name.split(' ')[0] ?? 'Atleta'}</p>
            {isDemoUser && <p className="text-[10px] font-black uppercase tracking-[0.2em] text-amber-300">Demo Read-Only</p>}
          </div>
          <LanguageSelector />
        </div>
      </header>

      {/* --- CONTEÚDO PRINCIPAL (Expanded for 4K) --- */}
      <main className={cn(
        "pb-32 pt-2 md:pt-28 min-h-0 flex-1 overflow-x-hidden",
        isChatPage ? "overflow-hidden md:pb-0" : "overflow-y-auto"
      )}>
        <div data-testid="app-shell-main" className={cn("mx-auto w-full h-full min-h-0", layoutMode.contentClassName)}>
          <Outlet />
        </div>
      </main>

      {/* --- MOBILE BOTTOM NAV (PÍLULA FLUTUANTE) --- */}
      <nav data-testid="mobile-nav" className="md:hidden fixed bottom-6 left-1/2 -translate-x-1/2 w-[92%] max-w-sm rounded-[2.5rem] bg-zinc-900/80 backdrop-blur-2xl border border-white/10 shadow-2xl z-50 flex items-center justify-between px-3 py-3">
        <NavLink to="/dashboard" end data-testid="nav-home" className={({ isActive }) => cn("p-3 rounded-full transition-all duration-300 flex-1 flex justify-center", isActive ? "bg-white/10 text-white" : "text-zinc-500 hover:text-zinc-300")}>
          <Home size={22} />
        </NavLink>
        <NavLink to="/dashboard/plan" data-testid="nav-plan" className={() => cn("p-3 rounded-full transition-all duration-300 flex-1 flex justify-center", isPathActive('/dashboard/plan') ? "bg-white/10 text-white" : "text-zinc-500 hover:text-zinc-300")}>
          <ClipboardList size={22} />
        </NavLink>
        <NavLink to="/dashboard/workouts" data-testid="nav-workouts" className={() => cn("p-3 rounded-full transition-all duration-300 flex-1 flex justify-center", isPathActive('/dashboard/workouts') ? "bg-white/10 text-white" : "text-zinc-500 hover:text-zinc-300")}>
          <Dumbbell size={22} />
        </NavLink>
        
        <NavLink to="/dashboard/body" data-testid="nav-body" className={() => cn("p-3 rounded-full transition-all duration-300 flex-1 flex justify-center", isPathActive('/dashboard/body') ? "bg-white/10 text-white" : "text-zinc-500 hover:text-zinc-300")}>
          <Scale size={22} />
        </NavLink>
        <NavLink to="/dashboard/chat" data-testid="nav-chat" className={() => cn("p-3 rounded-full transition-all duration-300 relative flex-1 flex justify-center", isPathActive('/dashboard/chat') ? "bg-white/10 text-white" : "text-zinc-500 hover:text-zinc-300")}>
          <MessageCircle size={22} />
          <span className="absolute top-2 right-1/2 translate-x-3 w-2 h-2 rounded-full bg-indigo-500 border-2 border-zinc-900 shadow-glow shadow-indigo-500"></span>
        </NavLink>
        <NavLink to="/dashboard/settings" data-testid="nav-settings" className={() => cn("p-3 rounded-full transition-all duration-300 flex-1 flex justify-center", isPathActive('/dashboard/settings') ? "bg-white/10 text-white" : "text-zinc-500 hover:text-zinc-300")}>
          <Settings size={22} />
        </NavLink>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          data-testid="mobile-logout"
          onClick={logout}
          className="p-3 rounded-full transition-all duration-300 flex-1 text-zinc-500 hover:text-zinc-300 hover:bg-transparent"
          aria-label="Logout"
        >
          <LogOut size={22} aria-hidden="true" />
        </Button>
      </nav>

      {/* --- GLOBAL SYSTEM COMPONENTS --- */}
      {!isSubscriptionPage && !isChatPage && !isDemoUser && <QuickAddFAB />}

    </div>
  );
}
