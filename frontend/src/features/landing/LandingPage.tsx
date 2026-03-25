import { useAuthStore } from '@shared/hooks/useAuth';
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

import { ChatCarousel } from './components/ChatCarousel';
import { ComparisonTable } from './components/ComparisonTable';
import { Counters } from './components/Counters';
import { FAQ } from './components/FAQ';
import { Features } from './components/Features';
import { FinalCTA } from './components/FinalCTA';
import { Footer } from './components/Footer';
import { Hero } from './components/Hero';
import { HowItWorks } from './components/HowItWorks';
import { IntegrationLogos } from './components/IntegrationLogos';
import { Navbar } from './components/Navbar';
import { Pricing } from './components/Pricing';
import { ProductShowcase } from './components/ProductShowcase';
import { StickyMobileCTA } from './components/StickyMobileCTA';
import { TrainerShowcase } from './components/TrainerShowcase';

/**
 * LandingPage
 * The official version of the landing page following the Uncodixify guide.
 * Clean, functional, mobile-first, and avoids "AI defaults" like complex gradients.
 */
const LandingPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated, isLoading } = useAuthStore();

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      void navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);

  return (
    <div className="min-h-screen bg-dark-bg text-text-primary font-sans selection:bg-primary/30 selection:text-white overflow-x-hidden">
      <Navbar />
      
      <main>
        <Hero />
        <Counters />
        <ChatCarousel />
        <TrainerShowcase />
        <ProductShowcase />
        <ComparisonTable />
        <Features />
        <IntegrationLogos />
        <HowItWorks />
        <Pricing />
        <FAQ />
        <FinalCTA />
      </main>

      <Footer />
      <StickyMobileCTA />
    </div>
  );
};



export default LandingPage;
