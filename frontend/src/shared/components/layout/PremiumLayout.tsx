import { ClipboardList, Home, Scale, Dumbbell, Settings, MessageCircle, LogOut, Flame } from 'lucide-react';
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

import { AppShell } from './AppShell';
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
    <AppShell
      testId="premium-layout-shell"
      className={cn(
        'h-[100dvh] text-text-primary font-sans selection:bg-[color:var(--color-surface-container)] relative overflow-hidden flex flex-col',
        layoutMode.shellClassName
      )}
    >
      {/* --- DESKTOP TOP NAV (DOCK) --- */}
      <nav
        data-testid="desktop-nav"
        id="desktop-nav"
        className={cn(
          'hidden md:flex fixed top-0 left-0 right-0 h-20 items-center z-50 bg-[color:var(--color-background)] border-b border-[color:var(--color-outline-variant)]',
          layoutMode.navClassName
        )}
      >
        <div className="flex-1 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[color:var(--color-surface-container)] border border-[color:var(--color-outline-variant)] flex items-center justify-center overflow-hidden p-1.5">
            <img src="/logo_icon.png" alt="FityQ Logo" className="w-full h-full object-contain" />
          </div>
          <span className="text-base font-semibold uppercase tracking-[0.05em] text-text-primary">FityQ</span>
          {isDemoUser && (
            <span className="px-3 py-1 rounded-[var(--radius-full)] text-[10px] font-semibold uppercase tracking-[0.05em] text-[color:var(--color-tertiary)] border border-[color:var(--color-tertiary)]/30 bg-[color:var(--color-tertiary)]/10">
              Demo Read-Only
            </span>
          )}
        </div>
        
        <div className="flex-1 flex justify-center">
          <div className="flex bg-[color:var(--color-surface-container)] rounded-[var(--radius-full)] p-1 border border-[color:var(--color-outline-variant)]">
            <NavLink to="/dashboard" end data-testid="desktop-nav-home" className={({ isActive }) => cn("px-6 py-2 rounded-[var(--radius-full)] text-sm font-semibold transition-colors whitespace-nowrap shrink-0", isActive ? "bg-[color:var(--color-surface-container-high)] text-text-primary" : "text-text-secondary hover:text-text-secondary")}>
              {t('nav.home')}
            </NavLink>
            <NavLink to="/dashboard/plan" data-testid="desktop-nav-plan" className={() => cn("px-6 py-2 rounded-[var(--radius-full)] text-sm font-semibold transition-colors whitespace-nowrap shrink-0", isPathActive('/dashboard/plan') ? "bg-[color:var(--color-surface-container-high)] text-text-primary" : "text-text-secondary hover:text-text-secondary")}>
              {t('nav.plan')}
            </NavLink>
            <NavLink to="/dashboard/workouts" data-testid="desktop-nav-workouts" className={() => cn("px-6 py-2 rounded-[var(--radius-full)] text-sm font-semibold transition-colors whitespace-nowrap shrink-0", isPathActive('/dashboard/workouts') ? "bg-[color:var(--color-surface-container-high)] text-text-primary" : "text-text-secondary hover:text-text-secondary")}>
              {t('nav.workouts')}
            </NavLink>
            <NavLink to="/dashboard/body" data-testid="desktop-nav-body" className={() => cn("px-6 py-2 rounded-[var(--radius-full)] text-sm font-semibold transition-colors whitespace-nowrap shrink-0", isPathActive('/dashboard/body') ? "bg-[color:var(--color-surface-container-high)] text-text-primary" : "text-text-secondary hover:text-text-secondary")}>
              {t('nav.body')}
            </NavLink>
            <NavLink to="/dashboard/nutrition" data-testid="desktop-nav-nutrition" className={() => cn("px-6 py-2 rounded-[var(--radius-full)] text-sm font-semibold transition-colors whitespace-nowrap shrink-0", isPathActive('/dashboard/nutrition') ? "bg-[color:var(--color-surface-container-high)] text-text-primary" : "text-text-secondary hover:text-text-secondary")}>
              {t('nav.nutrition')}
            </NavLink>
            <NavLink to="/dashboard/chat" data-testid="desktop-nav-chat" className={() => cn("px-6 py-2 rounded-[var(--radius-full)] text-sm font-semibold transition-colors whitespace-nowrap shrink-0", isPathActive('/dashboard/chat') ? "bg-[color:var(--color-surface-container-high)] text-text-primary" : "text-text-secondary hover:text-text-secondary")}>
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
             <span className="text-[9px] font-semibold uppercase tracking-[0.2em] text-text-muted">Membro</span>
             <span className="text-[10px] font-semibold text-[color:var(--color-primary)] border border-[color:var(--color-primary)]/20 bg-[color:var(--color-primary)]/5 px-2 py-0.5 rounded-[var(--radius-default)]">{userInfo?.subscription_plan ?? 'Free'}</span>
          </div>
          <NavLink to="/dashboard/settings" data-testid="desktop-nav-settings" className={({ isActive }) => cn("p-2.5 rounded-xl transition-all border", isActive ? "bg-[color:var(--color-surface-container-high)] border-[color:var(--color-outline-variant)] text-text-primary" : "border-transparent text-text-secondary hover:bg-[color:var(--color-surface-container)] hover:text-text-secondary")}>
            <Settings size={20} />
          </NavLink>
          <Button
            type="button"
            data-testid="desktop-logout"
            onClick={logout}
            className="px-4 py-2 rounded-xl border border-[color:var(--color-outline-variant)] bg-[color:var(--color-surface-container)] text-sm font-bold tracking-wide text-text-secondary transition-all hover:bg-[color:var(--color-surface-container-high)] hover:text-text-primary"
          >
            Logout
          </Button>
          <div className="w-10 h-10 rounded-[var(--radius-lg)] bg-[color:var(--color-surface-container)] border border-[color:var(--color-outline-variant)] overflow-hidden flex items-center justify-center">
            {userInfo?.photo_base64 ? (
              <img src={userInfo.photo_base64} alt="Profile" className="w-full h-full object-cover" />
            ) : (
              <span className="font-bold text-text-secondary">{userInfo?.name.charAt(0) ?? 'U'}</span>
            )}
          </div>
        </div>
      </nav>

      {/* --- MOBILE HEADER --- */}
      <header className="md:hidden sticky top-0 z-40 bg-[color:var(--color-background)] px-4 py-3 pt-7 flex flex-col gap-2 border-b border-[color:var(--color-outline-variant)]">
        <div className="flex items-center justify-between gap-3">
          <div className="w-9 h-9 rounded-xl bg-[color:var(--color-surface-container)] border border-[color:var(--color-outline-variant)] p-1 flex items-center justify-center">
             <img src="/logo_icon.png" alt="Logo" className="w-full h-full object-contain opacity-80" />
          </div>
          <div className="flex-1">
            <p className="text-[10px] font-bold text-text-muted uppercase tracking-[0.05em]">FityQ Premium</p>
            <p className="text-sm font-semibold text-text-primary leading-tight">{userInfo?.name.split(' ')[0] ?? 'Atleta'}</p>
            {isDemoUser && <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-amber-300">Demo Read-Only</p>}
          </div>
          <LanguageSelector />
        </div>
      </header>

      {/* --- CONTEÚDO PRINCIPAL (Expanded for 4K) --- */}
      <main
        data-testid="premium-layout-main"
        className={cn(
        "pb-32 pt-2 md:pt-28 min-h-0 flex-1 overflow-x-hidden",
        layoutMode.mainClassName,
        isChatPage ? "overflow-hidden md:pb-0" : "overflow-y-auto"
      )}
      >
        <div data-testid="app-shell-main" className={cn("mx-auto w-full h-full min-h-0", layoutMode.contentClassName)}>
          <Outlet />
        </div>
      </main>

      {/* --- MOBILE BOTTOM NAV (PÍLULA FLUTUANTE) --- */}
      <nav data-testid="mobile-nav" className="md:hidden fixed bottom-6 left-1/2 -translate-x-1/2 w-[92%] max-w-sm rounded-[var(--radius-full)] bg-[color:var(--color-surface-container-low)] border border-[color:var(--color-outline-variant)] z-50 flex items-center justify-between px-3 py-3">
        <NavLink to="/dashboard" end data-testid="nav-home" className={({ isActive }) => cn("p-3 rounded-full transition-all duration-300 flex-1 flex justify-center", isActive ? "bg-[color:var(--color-surface-container-high)] text-text-primary" : "text-text-muted hover:text-text-secondary")}>
          <Home size={22} />
        </NavLink>
        <NavLink to="/dashboard/plan" data-testid="nav-plan" className={() => cn("p-3 rounded-full transition-all duration-300 flex-1 flex justify-center", isPathActive('/dashboard/plan') ? "bg-[color:var(--color-surface-container-high)] text-text-primary" : "text-text-muted hover:text-text-secondary")}>
          <ClipboardList size={22} />
        </NavLink>
        <NavLink to="/dashboard/workouts" data-testid="nav-workouts" className={() => cn("p-3 rounded-full transition-all duration-300 flex-1 flex justify-center", isPathActive('/dashboard/workouts') ? "bg-[color:var(--color-surface-container-high)] text-text-primary" : "text-text-muted hover:text-text-secondary")}>
          <Dumbbell size={22} />
        </NavLink>
        
        <NavLink to="/dashboard/body" data-testid="nav-body" className={() => cn("p-3 rounded-full transition-all duration-300 flex-1 flex justify-center", isPathActive('/dashboard/body') ? "bg-[color:var(--color-surface-container-high)] text-text-primary" : "text-text-muted hover:text-text-secondary")}>
          <Scale size={22} />
        </NavLink>
        <NavLink to="/dashboard/nutrition" data-testid="nav-nutrition" className={() => cn("p-3 rounded-full transition-all duration-300 flex-1 flex justify-center", isPathActive('/dashboard/nutrition') ? "bg-[color:var(--color-surface-container-high)] text-text-primary" : "text-text-muted hover:text-text-secondary")}>
          <Flame size={22} />
        </NavLink>
        <NavLink to="/dashboard/chat" data-testid="nav-chat" className={() => cn("p-3 rounded-full transition-all duration-300 relative flex-1 flex justify-center", isPathActive('/dashboard/chat') ? "bg-[color:var(--color-surface-container-high)] text-text-primary" : "text-text-muted hover:text-text-secondary")}>
          <MessageCircle size={22} />
          <span className="absolute top-2 right-1/2 translate-x-3 w-2 h-2 rounded-full bg-[color:var(--color-primary)] border-2 border-[color:var(--color-background)]"></span>
        </NavLink>
        <NavLink to="/dashboard/settings" data-testid="nav-settings" className={() => cn("p-3 rounded-full transition-all duration-300 flex-1 flex justify-center", isPathActive('/dashboard/settings') ? "bg-[color:var(--color-surface-container-high)] text-text-primary" : "text-text-muted hover:text-text-secondary")}>
          <Settings size={22} />
        </NavLink>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          data-testid="mobile-logout"
          onClick={logout}
          className="p-3 rounded-full transition-all duration-300 flex-1 text-text-muted hover:text-text-secondary hover:bg-transparent"
          aria-label="Logout"
        >
          <LogOut size={22} aria-hidden="true" />
        </Button>
      </nav>

      {/* --- GLOBAL SYSTEM COMPONENTS --- */}
      {!isSubscriptionPage && !isChatPage && !isDemoUser && <QuickAddFAB />}

    </AppShell>
  );
}
