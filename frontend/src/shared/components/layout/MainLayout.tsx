import { Outlet } from 'react-router-dom';

import { useAuthStore } from '../../hooks/useAuth';
import { useInactivityLogout } from '../../hooks/useInactivityLogout';
import { useTokenRefresh } from '../../hooks/useTokenRefresh';
import { ConfirmationProvider } from '../ui/ConfirmationProvider';
import { GlobalErrorBoundary } from '../ui/GlobalErrorBoundary';
import { IntroTour } from '../ui/IntroTour';
import type { TourStep } from '../ui/IntroTour';
import { QuickAddFAB } from '../ui/QuickAddFAB';
import { ToastContainer } from '../ui/ToastContainer';

import { BottomNav } from './BottomNav';
import { Sidebar } from './Sidebar';

/**
 * MainLayout component
 *
 * Provides the core shell for the application, including:
 * - Desktop Sidebar
 * - Mobile Bottom Navigation
 * - Global notification system (Toasts)
 * - Global confirmation modals
 * - Automatic logout on inactivity
 * - Main content area via Router <Outlet />
 */
export function MainLayout() {
  const { userInfo } = useAuthStore();
  useInactivityLogout();
  useTokenRefresh();

  const TOUR_STEPS: TourStep[] = [
    { targetId: 'tour-nav-home', titleKey: 'dashboard.tour.home_title', descriptionKey: 'dashboard.tour.home_desc', imageUrl: '/assets/tour/home.png' },
    { targetId: 'tour-nav-trainer', titleKey: 'dashboard.tour.trainer_title', descriptionKey: 'dashboard.tour.trainer_desc', imageUrl: '/assets/tour/chat.webp' },
    { targetId: 'tour-nav-workouts', titleKey: 'dashboard.tour.workouts_title', descriptionKey: 'dashboard.tour.workouts_desc', imageUrl: '/assets/tour/workouts.png' },
    { targetId: 'tour-nav-body', titleKey: 'dashboard.tour.body_title', descriptionKey: 'dashboard.tour.body_desc', imageUrl: '/assets/tour/body.png' },
    { targetId: 'tour-nav-settings', titleKey: 'dashboard.tour.settings_title', descriptionKey: 'dashboard.tour.settings_desc', imageUrl: '/assets/tour/settings.png' }
  ];

  return (
    <div className="min-h-screen bg-dark-bg text-text-primary flex">
      {/* Platform Utilities */}
      <ToastContainer />
      <ConfirmationProvider />

      {/* Navigation - Desktop */}
      <GlobalErrorBoundary>
        <Sidebar />
      </GlobalErrorBoundary>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col lg:pl-64 pb-16 md:pb-20 lg:pb-0 min-h-screen transition-all duration-300 overflow-x-hidden">
        <div className="flex-1 max-w-7xl mx-auto w-full p-4 md:p-6 lg:p-8">
          <GlobalErrorBoundary>
            <Outlet />
          </GlobalErrorBoundary>
        </div>
      </main>

      {/* Navigation - Mobile */}
      <BottomNav />
      <QuickAddFAB />
      <IntroTour steps={TOUR_STEPS} tourKey={`dashboard-main-${userInfo?.email ?? 'guest'}`} />
    </div>
  );
}
