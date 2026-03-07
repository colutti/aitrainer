import { Button } from '@shared/components/ui/Button';
import { LanguageSelector } from '@shared/components/ui/LanguageSelector';
import { useAuthStore } from '@shared/hooks/useAuth';
import {
  Brain,
  ChevronRight,
  Clock,
  Menu,
  X,
  Zap,
  LayoutGrid as Zest,
  Users,
  MessageSquare as MemorySquare,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

import { AnimatedCounters } from './AnimatedCounters';
import { ChatCarousel } from './ChatCarousel';
import { ComparisonTable } from './ComparisonTable';
import { FAQAccordion } from './FAQAccordion';
import { HeroProductPreview } from './HeroProductPreview';
import { IntegrationLogos } from './IntegrationLogos';
import { ProductShowcase } from './ProductShowcase';
import { StickyMobileCTA } from './StickyMobileCTA';
import { TrainerShowcase } from './TrainerShowcase';

/**
 * LandingPage
 * O ponto de entrada principal para usuários não autenticados.
 * Design premium, dark mode, focado em conversão e estética.
 */
const LandingPage = () => {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  const isPt = i18n.language.startsWith('pt');
  const currencySymbol = isPt ? 'R$ ' : '$';

  const { isAuthenticated, isLoading } = useAuthStore();

  // Se já estiver autenticado, redireciona para o dashboard
  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      void navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, isLoading, navigate]);

  // Controle de scroll para mudar o estilo da navbar
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => { window.removeEventListener('scroll', handleScroll); };
  }, []);

  const navLinks = [
    { name: t('landing.nav.differentiators'), href: '#diferenciais' },
    { name: t('landing.nav.how_it_works'), href: '#como-funciona' },
    { name: t('landing.nav.trainers'), href: '#treinadores' },
    { name: t('landing.nav.plans'), href: '#planos' },
  ];

  return (
    <div className="min-h-screen bg-dark-bg text-text-primary selection:bg-primary/30 selection:text-white font-sans overflow-x-hidden">
      {/* Dynamic Background */}
      <div className="fixed inset-0 z-0 pointer-events-none">
        <div
          className="absolute inset-0 opacity-[0.15]"
          style={{
            backgroundImage: 'radial-gradient(rgba(139, 92, 246, 0.1) 1px, transparent 1px)',
            backgroundSize: '32px 32px',
          }}
        />
        <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-primary/5 rounded-full blur-[120px] -translate-y-1/2 translate-x-1/3" />
        <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-accent/5 rounded-full blur-[100px] translate-y-1/3 -translate-x-1/4" />
      </div>

      {/* Navbar */}
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 px-4 sm:px-6 lg:px-8 ${
          scrolled
            ? 'py-3 bg-dark-bg/80 backdrop-blur-lg border-b border-border shadow-lg'
            : 'py-6 bg-transparent'
        }`}
      >
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          {/* Logo */}
          <div
            className="flex items-center gap-2 cursor-pointer group"
            onClick={() => { window.scrollTo({ top: 0, behavior: 'smooth' }); }}
          >
            <div className="w-10 h-10 rounded-xl bg-linear-to-br from-primary to-accent p-0.5 shadow-lg group-hover:scale-105 transition-transform duration-300">
              <div className="w-full h-full rounded-[9px] bg-dark-bg flex items-center justify-center">
                <img src="/logo_icon.png" alt="FityQ" className="w-6 h-6" />
              </div>
            </div>
            <span className="font-display text-2xl font-bold tracking-tight bg-clip-text text-transparent bg-linear-to-r from-white to-white/70">
              FityQ
            </span>
          </div>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                className="text-sm font-medium text-text-secondary hover:text-white transition-colors"
                onClick={(e) => {
                  e.preventDefault();
                  document.querySelector(link.href)?.scrollIntoView({ behavior: 'smooth' });
                }}
              >
                {link.name}
              </a>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-4">
            <LanguageSelector />
            <Button
              onClick={() => { void navigate('/login'); }}
              variant="secondary"
              size="sm"
            >
              {t('landing.nav.login')}
            </Button>
          </div>

          {/* Mobile menu toggle */}
          <button
            className="md:hidden text-white p-2"
            onClick={() => { setIsMenuOpen(!isMenuOpen); }}
            aria-label="Toggle menu"
          >
            {isMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile menu dropdown */}
        {isMenuOpen && (
          <div className="md:hidden absolute top-full left-0 right-0 bg-dark-bg/95 backdrop-blur-xl border-b border-border p-6 flex flex-col gap-6 animate-in slide-in-from-top duration-300">
            {navLinks.map((link) => (
              <a
                key={link.name}
                href={link.href}
                className="text-lg font-medium text-white/80"
                onClick={() => { setIsMenuOpen(false); }}
              >
                {link.name}
              </a>
            ))}
            <div className="h-px bg-border my-2" />
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-text-secondary">{t('settings.language')}</span>
              <LanguageSelector />
            </div>
            <Button
              onClick={() => { void navigate('/login'); }}
              variant="primary"
              fullWidth
            >
              {t('landing.nav.login')}
            </Button>
          </div>
        )}
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-12 lg:pt-44 lg:pb-20 px-4 sm:px-6 lg:px-8 z-10 overflow-hidden">
        <div className="max-w-7xl mx-auto grid lg:grid-cols-[55%_45%] gap-12 items-center">
          {/* Left: Text content */}
          <div>
            <div className="mb-6 inline-block">
              <span className="px-4 py-2 rounded-full text-sm font-semibold text-accent bg-accent/10 border border-accent/20">
                {t('landing.hero.badge')}
              </span>
            </div>
            <h1 className="font-display text-4xl sm:text-6xl lg:text-7xl font-bold text-white leading-[1.1] mb-6 tracking-tight">
              {t('landing.hero.title')}{' '}
              <span className="bg-clip-text text-transparent bg-linear-to-r from-primary via-accent to-primary bg-size-[200%_auto] animate-shimmer">
                {t('landing.hero.title_gradient')}
              </span>
            </h1>
            <p className="text-base sm:text-xl text-text-secondary mb-10 leading-relaxed max-w-xl">
              {t('landing.hero.description')}
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Button
                onClick={() => { void navigate('/login?mode=register'); }}
                variant="primary"
                size="lg"
                className="h-14 px-8 text-lg group"
              >
                {t('landing.hero.cta')}
                <ChevronRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Button>
              <Button
                onClick={() => {
                  document.querySelector('#treinadores')?.scrollIntoView({ behavior: 'smooth' });
                }}
                variant="secondary"
                size="lg"
                className="h-14 px-8 text-lg"
              >
                {t('landing.nav.trainers')}
              </Button>
            </div>

            {/* Trust Badges */}
            <div className="mt-6 flex flex-wrap gap-4">
              <span className="flex items-center gap-1.5 text-sm text-text-secondary">
                {t('landing.trust_badge_free')}
              </span>
              <span className="flex items-center gap-1.5 text-sm text-text-secondary">
                {t('landing.trust_badge_card')}
              </span>
            </div>

            {/* Trusted elements - Placeholder for future social proof */}
            <div className="mt-8 empty:hidden">
            </div>
          </div>

          {/* Right: Visual preview */}
          <div className="hidden lg:block">
            <HeroProductPreview />
          </div>
        </div>
        
        {/* Abstract shape decoration */}
        <div className="absolute top-32 right-0 w-96 h-96 bg-primary/6 rounded-full blur-[100px] -z-10" />
      </section>

      {/* Animated Counters */}
      <AnimatedCounters />

      {/* Section divider */}
      <div className="w-full h-px bg-linear-to-r from-transparent via-primary/20 to-transparent" />

      {/* Chat Carousel Section */}
      <div className="relative z-10">
        <ChatCarousel />
      </div>

      {/* Section divider */}
      <div className="w-full h-px bg-linear-to-r from-transparent via-primary/20 to-transparent" />

      {/* Trainer Showcase */}
      <div className="relative z-10">
        <TrainerShowcase />
      </div>

      {/* Section divider */}
      <div className="w-full h-px bg-linear-to-r from-transparent via-primary/20 to-transparent" />

      {/* Product Showcase */}
      <div className="relative z-10">
        <ProductShowcase />
      </div>

      {/* Section divider */}
      <div className="w-full h-px bg-linear-to-r from-transparent via-primary/20 to-transparent" />

      {/* Comparison Table */}
      <ComparisonTable />

      {/* Section divider */}
      <div className="w-full h-px bg-linear-to-r from-transparent via-primary/20 to-transparent" />

      {/* Diferenciais Section — Bento Grid */}
      <section id="diferenciais" className="py-12 md:py-16 px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display text-4xl sm:text-5xl font-bold text-white mb-4">
              {t('landing.diff.title')}
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mx-auto">
              {t('landing.diff.subtitle')}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-4">
            {[
              {
                icon: Zap as React.ElementType,
                title: t('landing.diff.features.meta.title'),
                description: t('landing.diff.features.meta.description'),
                extra: null as React.ReactNode,
                delay: 0,
              },
              {
                icon: Brain as React.ElementType,
                title: t('landing.diff.features.vision.title'),
                description: t('landing.diff.features.vision.description'),
                extra: null as React.ReactNode,
                delay: 0.05,
              },
              {
                icon: Users as React.ElementType,
                title: t('landing.diff.features.trainers.title'),
                description: t('landing.diff.features.trainers.description'),
                extra: (
                  <div className="flex items-center mt-4">
                    {['atlas', 'luna', 'sofia', 'sargento', 'gymbro'].map((trainer, i) => (
                      <img
                        key={trainer}
                        src={`/assets/avatars/${trainer}.png`}
                        alt={trainer}
                        className="w-8 h-8 rounded-full border-2 border-dark-bg object-cover"
                        style={{ marginLeft: i === 0 ? 0 : '-8px', zIndex: 5 - i }}
                        loading="lazy"
                        width="32"
                        height="32"
                      />
                    ))}
                  </div>
                ),
                delay: 0.1,
              },
              {
                icon: Zest as React.ElementType,
                title: t('landing.diff.features.integrations.title'),
                description: t('landing.diff.features.integrations.description'),
                extra: (
                  <div className="flex flex-wrap gap-1 mt-4">
                    {['Hevy', 'MyFitnessPal', 'Zepp Life'].map((app) => (
                      <span key={app} className="text-xs font-semibold text-accent bg-accent/10 rounded px-2 py-0.5">
                        {app}
                      </span>
                    ))}
                  </div>
                ),
                delay: 0.15,
              },
              {
                icon: MemorySquare as React.ElementType,
                title: t('landing.diff.features.journey.title'),
                description: t('landing.diff.features.journey.description'),
                extra: (
                  <div className="space-y-2 mt-4">
                    {(t('landing.diff.features.journey.items', { returnObjects: true }) as string[]).map((label, i) => {
                      const dots = ['bg-indigo-400', 'bg-cyan-400', 'bg-green-400'];
                      return (
                        <div key={i} className="flex items-center gap-2">
                          <div className={`w-2 h-2 rounded-full ${dots[i % dots.length] ?? ''} shrink-0`} />
                          <span className="text-xs text-text-secondary">{label}</span>
                        </div>
                      );
                    })}
                  </div>
                ),
                delay: 0.2,
              },
              {
                icon: Clock as React.ElementType,
                title: t('landing.diff.features.available.title'),
                description: t('landing.diff.features.available.description'),
                extra: (
                  <div className="flex items-center gap-1.5 mt-4">
                    <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                    <span className="text-xs text-green-400 font-medium">{t('landing.diff.features.available.online')}</span>
                  </div>
                ),
                delay: 0.25,
              },
            ].map((feature, idx) => {
              const Icon = feature.icon;
              return (
                <RevealOnScroll key={idx} delay={feature.delay}>
                  <div className="group relative p-6 rounded-2xl border border-border bg-secondary/80 backdrop-blur-sm hover:border-primary/40 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-primary/10 transition-all duration-300 h-full">
                    <div className="absolute inset-0 rounded-2xl bg-linear-to-br from-primary/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    <div className="relative z-10">
                      <div className="w-12 h-12 rounded-lg bg-linear-to-br from-primary to-accent flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                        <Icon className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="font-display text-xl font-bold text-white mb-2">{feature.title}</h3>
                      <p className="text-text-secondary text-sm">{feature.description}</p>
                      {feature.extra}
                    </div>
                  </div>
                </RevealOnScroll>
              );
            })}
          </div>
        </div>
      </section>

      {/* Integration Logos */}
      <IntegrationLogos />

      {/* Section divider */}
      <div className="w-full h-px bg-linear-to-r from-transparent via-primary/20 to-transparent" />

      {/* Como Funciona Section */}
      <section id="como-funciona" className="py-12 md:py-16 px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display text-4xl sm:text-5xl font-bold text-white mb-4">
              {t('landing.how.title')}
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mx-auto">
              {t('landing.how.subtitle')}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {(t('landing.how.steps', { returnObjects: true }) as { title: string; description: string }[]).map((item, idx) => (
              <RevealOnScroll key={idx} delay={idx * 0.15}>
                <div className="relative p-6">
                  <div className="font-display text-8xl font-extrabold text-primary/10 mb-4 leading-none">
                    {`0${(idx + 1).toString()}`}
                  </div>
                  <h3 className="font-display text-2xl font-bold text-white mb-3">
                    {item.title}
                  </h3>
                  <p className="text-text-secondary text-lg">
                    {item.description}
                  </p>
                  {idx < 2 && (
                    <div className="hidden md:block absolute top-16 -right-4 text-accent/40">
                      <ChevronRight className="w-6 h-6" />
                    </div>
                  )}
                </div>
              </RevealOnScroll>
            ))}
          </div>
        </div>
      </section>

      {/* Planos Section */}
      <section id="planos" className="py-12 md:py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display text-4xl sm:text-5xl font-bold text-white mb-4">
              {t('landing.plans.title')}
            </h2>
            <p className="text-lg text-text-secondary max-w-2xl mx-auto">
              {t('landing.plans.subtitle')}
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 lg:gap-8">
            {[
              {
                id: 'free',
                price: 0,
                suffix: t('landing.plans.total', 'total'),
                highlight: true,
                isFree: true,
              },
              {
                id: 'basic',
                price: isPt ? 24.90 : 4.99,
                suffix: t('landing.plans.per_month', '/mês'),
                highlight: false,
                isFree: false,
              },
              {
                id: 'pro',
                price: isPt ? 49.90 : 9.99,
                suffix: t('landing.plans.per_month', '/mês'),
                highlight: false,
                isFree: false,
              },
              {
                id: 'premium',
                price: isPt ? 99.90 : 19.99,
                suffix: t('landing.plans.per_month', '/mês'),
                highlight: false,
                isFree: false,
              },
            ].map((plan, idx) => {
              const planData = t(`landing.plans.items.${plan.id}`, { returnObjects: true }) as {
                name: string;
                description: string;
                features: string[];
                button: string;
              };

              return (
                <RevealOnScroll key={idx} delay={idx * 0.1}>
                  <div
                    className={`relative rounded-2xl p-6 transition-all duration-300 h-full flex flex-col ${
                      plan.highlight
                        ? 'border border-accent bg-accent/5 md:scale-105 shadow-xl shadow-accent/10 z-10'
                        : 'border border-border bg-secondary/80'
                    } hover:border-accent/50`}
                  >
                    {plan.highlight && (
                      <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-linear-to-r from-primary to-accent text-white text-xs font-bold whitespace-nowrap">
                        {t('landing.plans.recommended')}
                      </div>
                    )}
                    <h3 className="font-display text-xl font-bold text-white mb-2">
                       {planData.name}
                    </h3>
                    <p className="text-text-secondary mb-6 text-sm grow">
                      {planData.description}
                    </p>
                    <div className="mb-6">
                      <span className="font-display text-3xl font-extrabold text-white">
                        {plan.price === 0 ? (isPt ? t('landing.plans.items.free.price_free', 'Grátis') : t('landing.plans.items.free.price_free', 'Free')) : `${currencySymbol}${plan.price.toFixed(2).replace('.', isPt ? ',' : '.')}`}
                      </span>
                      {plan.price !== 0 && (
                          <span className="text-text-secondary ml-1 text-sm">
                            {plan.suffix}
                          </span>
                      )}
                    </div>
                    <Button
                      onClick={() => {
                        void navigate('/login?mode=register');
                      }}
                      variant={plan.highlight ? 'primary' : 'secondary'}
                      disabled={!plan.isFree}
                      fullWidth
                      className="mb-8"
                    >
                      {planData.button}
                    </Button>
                    <ul className="space-y-3">
                      {planData.features.map((feature, fidx) => (
                        <li
                          key={fidx.toString()}
                          className="flex items-start gap-3 text-text-secondary text-sm"
                        >
                          <span className="text-accent font-bold">
                            ✓
                          </span>
                          <span>{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </RevealOnScroll>
              );
            })}
          </div>
        </div>
      </section>

      {/* Section divider */}
      <div className="w-full h-px bg-linear-to-r from-transparent via-primary/20 to-transparent" />

      {/* FAQ Accordion */}
      <FAQAccordion />

      {/* Final CTA */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Glow */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-[500px] h-[300px] bg-linear-to-r from-primary to-accent opacity-5 rounded-full blur-3xl" />
        </div>
        <div className="max-w-3xl mx-auto text-center relative z-10">
          <h2 className="font-display text-4xl sm:text-5xl font-bold text-white mb-6">
            {t('landing.cta.title')}
          </h2>
          <p className="text-lg text-text-secondary mb-8">
            {t('landing.cta.subtitle')}
          </p>
          <Button
            onClick={() => {
              void navigate('/login?mode=register');
            }}
            variant="primary"
            size="lg"
            className="animate-pulse-glow"
          >
            {t('landing.cta.button')}
            <ChevronRight className="w-5 h-5" />
          </Button>
          <p className="text-xs text-text-secondary mt-4">
            {t('landing.cta.trial')}
          </p>
        </div>
      </section>

      {/* Sticky Mobile CTA */}
      <StickyMobileCTA />

      {/* Footer */}
      <footer className="border-t border-border bg-dark-bg/50 py-8 px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <img src="/logo_icon.png" alt="FityQ" className="h-7 w-7" />
            <span className="font-display text-base font-bold text-white">FityQ</span>
          </div>
          <p className="text-text-secondary text-sm">
            {t('landing.footer.rights', { year: new Date().getFullYear() })}
          </p>
        </div>
        {/* TODO: Restore footer columns when Produto/Legal/Social links are ready */}
      </footer>
    </div>
  );
};

// Reveal on scroll component
const RevealOnScroll = ({
  children,
  delay = 0,
}: {
  children: React.ReactNode;
  delay?: number;
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries: IntersectionObserverEntry[]) => {
        if (entries[0]?.isIntersecting) {
          setIsVisible(true);
          observer.unobserve(entries[0].target);
        }
      },
      { threshold: 0.1 },
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => { observer.disconnect(); };
  }, []);

  return (
    <div
      ref={ref}
      className={`transition-all duration-700 ${
        isVisible
          ? 'opacity-100 translate-y-0'
          : 'opacity-0 translate-y-10'
      }`}
      style={{ transitionDelay: `${delay.toString()}s` }}
    >
      {children}
    </div>
  );
};

export default LandingPage;
