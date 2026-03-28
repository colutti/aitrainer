import { AppRoutes } from './AppRoutes';
import { render, screen } from './shared/utils/test-utils';

vi.mock('./features/auth/LoginPage', () => ({
  default: () => <div>Login Page</div>,
}));
vi.mock('./features/body/BodyPage', () => ({
  default: () => <div>Body Page</div>,
}));
vi.mock('./features/chat/ChatPage', () => ({
  default: () => <div>Chat Page</div>,
}));
vi.mock('./features/dashboard/DashboardPage', () => ({
  default: () => <div>Dashboard Page</div>,
}));
vi.mock('./features/landing/LandingPage', () => ({
  default: () => <div>FityQ Landing</div>,
}));
vi.mock('./features/memories/MemoriesPage', () => ({
  default: () => <div>Memories Page</div>,
}));
vi.mock('./features/onboarding/components/OnboardingPage', () => ({
  default: () => <div>Onboarding Page</div>,
}));
vi.mock('./features/settings/components/IntegrationsPage', () => ({
  default: () => <div>Integrations Page</div>,
}));
vi.mock('./features/settings/components/SubscriptionPage', () => ({
  default: () => <div>Subscription Page</div>,
}));
vi.mock('./features/settings/components/TrainerSettingsPage', () => ({
  default: () => <div>Trainer Settings Page</div>,
}));
vi.mock('./features/settings/components/UserProfilePage', () => ({
  default: () => <div>User Profile Page</div>,
}));
vi.mock('./features/settings/SettingsPage', () => ({
  default: () => <div>Settings Page</div>,
}));
vi.mock('./features/workouts/WorkoutsPage', () => ({
  default: () => <div>Workouts Page</div>,
}));
vi.mock('./shared/components/auth/AuthGuard', () => ({
  AuthGuard: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));
vi.mock('./shared/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));
vi.mock('./shared/components/layout/PremiumLayout', () => ({
  PremiumLayout: () => <div>Premium Layout</div>,
}));
vi.mock('./shared/components/ui/Skeleton', () => ({
  Skeleton: () => <div>Skeleton</div>,
}));
describe('AppRoutes', () => {
  it('redirects unknown routes to the landing page', async () => {
    render(<AppRoutes />, { route: '/totally-unknown' });
    expect(await screen.findByText(/fityq/i)).toBeInTheDocument();
  });
});
