import { Button } from '@shared/components/ui/Button';
import { LanguageSelector } from '@shared/components/ui/LanguageSelector';
import { useAuthStore } from '@shared/hooks/useAuth';
import {
  Zap,
  Brain,
  Users,
  Zap as Zest,
  Share2 as MemorySquare,
  Clock,
  ChevronRight,
  Menu,
  X,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

import { ChatCarousel } from './ChatCarousel';
import { HeroProductPreview } from './HeroProductPreview';
import { ProductShowcase } from './ProductShowcase';
import { TrainerShowcase } from './TrainerShowcase';


const LandingPage = (): React.ReactNode => {
  const navigate = useNavigate();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-return, @typescript-eslint/no-unsafe-member-access
  const isAuthenticated = Boolean(useAuthStore((state: any) => state.isAuthenticated));
  const [navScrolled, setNavScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { t } = useTranslation();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      void navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  // Handle navbar scroll effect
  useEffect(() => {
    const handleScroll = (): void => {
      setNavScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, []);

  // Smooth scroll for anchor links
  useEffect(() => {
    const handleAnchorClick = (e: MouseEvent): void => {
      const target = e.target as HTMLAnchorElement;
      if (target.getAttribute('data-anchor')) {
        e.preventDefault();
        const id = target.getAttribute('href')?.slice(1);
        if (id) {
          const element = document.getElementById(id);
          element?.scrollIntoView({ behavior: 'smooth' });
        }
      }
    };
    document.addEventListener('click', handleAnchorClick);
    return () => {
      document.removeEventListener('click', handleAnchorClick);
    };
  }, []);

  const navLinks = [
    { href: '#treinadores', label: t('landing.nav.trainers') },
    { href: '#diferenciais', label: t('landing.nav.differentiators') },
    { href: '#como-funciona', label: t('landing.nav.how_it_works') },
  ];

  return (
    <div className="bg-[var(--color-dark-bg)] overflow-hidden">
      {/* Dot grid background global */}
      <div
        className="fixed inset-0 pointer-events-none z-0 opacity-40"
        style={{
          backgroundImage: 'radial-gradient(rgba(99,102,241,0.06) 1px, transparent 1px)',
          backgroundSize: '28px 28px',
        }}
      />

      {/* Navbar */}
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          navScrolled
            ? 'bg-[rgba(10,10,11,0.9)] backdrop-blur-md border-b border-[var(--color-border)]'
            : 'bg-transparent'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <img
              src="/logo_icon.png"
              alt="FityQ"
              className="h-8 w-8"
            />
            <span className="text-xl font-bold text-white font-display">FityQ</span>
          </div>

          {/* Desktop Links */}
          <div className="hidden md:flex gap-8 items-center">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                data-anchor
                className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors text-sm font-medium"
              >
                {link.label}
              </a>
            ))}
          </div>

          {/* Right side */}
          <div className="flex items-center gap-3">
            <div className="hidden md:block">
              <LanguageSelector />
            </div>
            <Button
              onClick={() => {
                void navigate('/login');
              }}
              variant="primary"
              size="sm"
            >
              {t('landing.nav.login')}
            </Button>
            {/* Mobile hamburger */}
            <button
              className="md:hidden p-2 text-[var(--color-text-secondary)] hover:text-white transition-colors"
              onClick={() => { setMobileMenuOpen(!mobileMenuOpen); }}
              aria-label="Menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        <div
          className={`md:hidden overflow-hidden transition-all duration-300 ${
            mobileMenuOpen ? 'max-h-64 opacity-100' : 'max-h-0 opacity-0'
          } bg-[rgba(10,10,11,0.95)] border-b border-[var(--color-border)]`}
        >
          <div className="px-4 py-4 flex flex-col gap-4">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                data-anchor
                className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors text-base font-medium py-1"
                onClick={() => { setMobileMenuOpen(false); }}
              >
                {link.label}
              </a>
            ))}
            <div className="pt-4 border-t border-[var(--color-border)]">
              <LanguageSelector />
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section — Assimétrico */}
      <section className="min-h-screen flex items-center px-4 sm:px-6 lg:px-8 pt-20 relative overflow-hidden z-10">
        {/* Glow behind preview */}
        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-[var(--color-primary)] opacity-[0.06] rounded-full blur-3xl pointer-events-none" />

        <div className="max-w-7xl w-full mx-auto grid lg:grid-cols-[55%_45%] gap-12 lg:gap-16 items-center relative z-10">
          {/* Left: Text content */}
          <div>
            <div className="mb-6 inline-block">
              <span className="px-4 py-2 rounded-full text-sm font-semibold text-[var(--color-accent)] bg-[rgba(34,211,238,0.1)] border border-[var(--color-accent)]/20">
                {t('landing.hero.badge')}
              </span>
            </div>

            <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl font-extrabold leading-tight mb-6 text-white animate-slide-in-fade">
              {t('landing.hero.title')}{' '}
              <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">
                {t('landing.hero.title_gradient')}
              </span>
            </h1>

            <p
              className="text-lg sm:text-xl text-[var(--color-text-secondary)] mb-8 max-w-2xl leading-relaxed animate-slide-in-fade"
              style={{ animationDelay: '0.1s' }}
            >
              {t('landing.hero.description')}
            </p>

            <div className="animate-slide-in-fade mb-4" style={{ animationDelay: '0.2s' }}>
              <Button
                onClick={() => {
                  void navigate('/login');
                }}
                variant="primary"
                size="lg"
                className="animate-pulse-glow"
              >
                {t('landing.hero.cta')}
                <ChevronRight className="w-5 h-5" />
              </Button>
            </div>

            <p className="text-xs text-[var(--color-text-secondary)] mb-10 animate-slide-in-fade" style={{ animationDelay: '0.25s' }}>
              {t('landing.hero.trial_desc')}
            </p>

            {/* Feature badges */}
            <div
              className="flex flex-wrap gap-4 text-sm text-[var(--color-text-secondary)] animate-slide-in-fade"
              style={{ animationDelay: '0.3s' }}
            >
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-[var(--color-accent)]" />
                {t('landing.hero.feature_247')}
              </div>
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-[var(--color-accent)]" />
                {t('landing.hero.feature_ai')}
              </div>
              <div className="flex items-center gap-2">
                <Zest className="w-4 h-4 text-[var(--color-accent)]" />
                {t('landing.hero.feature_integrations')}
              </div>
            </div>
          </div>

          {/* Right: Product preview — hidden on mobile */}
          <div className="hidden lg:block">
            <HeroProductPreview />
          </div>
        </div>
      </section>

      {/* Section divider */}
      <div className="w-full h-px bg-gradient-to-r from-transparent via-[var(--color-primary)]/20 to-transparent" />

      {/* Chat Carousel Section */}
      <div className="relative z-10">
        <ChatCarousel />
      </div>

      {/* Section divider */}
      <div className="w-full h-px bg-gradient-to-r from-transparent via-[var(--color-primary)]/20 to-transparent" />

      {/* Trainer Showcase */}
      <div className="relative z-10">
        <TrainerShowcase />
      </div>

      {/* Section divider */}
      <div className="w-full h-px bg-gradient-to-r from-transparent via-[var(--color-primary)]/20 to-transparent" />

      {/* Product Showcase */}
      <div className="relative z-10">
        <ProductShowcase />
      </div>

      {/* Section divider */}
      <div className="w-full h-px bg-gradient-to-r from-transparent via-[var(--color-primary)]/20 to-transparent" />

      {/* Diferenciais Section — Bento Grid */}
      <section id="diferenciais" className="py-20 px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display text-4xl sm:text-5xl font-bold text-white mb-4">
              {t('landing.diff.title')}
            </h2>
            <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
              {t('landing.diff.subtitle')}
            </p>
          </div>

          {/* Grid uniforme de 3 colunas */}
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
                        className="w-8 h-8 rounded-full border-2 border-[var(--color-dark-bg)] object-cover"
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
                      <span key={app} className="text-xs font-semibold text-[var(--color-accent)] bg-[var(--color-accent)]/10 rounded px-2 py-0.5">
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
                          <span className="text-xs text-[var(--color-text-secondary)]">{label}</span>
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
                  <div className="group relative p-6 rounded-2xl border border-[var(--color-border)] bg-[rgba(18,18,20,0.8)] backdrop-blur-sm hover:border-[var(--color-primary)]/40 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-[var(--color-primary)]/10 transition-all duration-300 h-full">
                    <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-[var(--color-primary)]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    <div className="relative z-10">
                      <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                        <Icon className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="font-display text-xl font-bold text-white mb-2">{feature.title}</h3>
                      <p className="text-[var(--color-text-secondary)] text-sm">{feature.description}</p>
                      {feature.extra}
                    </div>
                  </div>
                </RevealOnScroll>
              );
            })}
          </div>
        </div>
      </section>

      {/* Section divider */}
      <div className="w-full h-px bg-gradient-to-r from-transparent via-[var(--color-primary)]/20 to-transparent" />

      {/* Como Funciona Section */}
      <section
        id="como-funciona"
        className="py-20 px-4 sm:px-6 lg:px-8 relative z-10"
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display text-4xl sm:text-5xl font-bold text-white mb-4">
              {t('landing.how.title')}
            </h2>
            <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
              {t('landing.how.subtitle')}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {(t('landing.how.steps', { returnObjects: true }) as { title: string; description: string }[]).map((item, idx) => (
              <RevealOnScroll key={idx} delay={idx * 0.15}>
                <div className="relative">
                  <div className="font-display text-8xl font-extrabold text-[var(--color-primary)]/10 mb-4 leading-none">
                    {`0${(idx + 1).toString()}`}
                  </div>
                  <h3 className="font-display text-2xl font-bold text-white mb-3">
                    {item.title}
                  </h3>
                  <p className="text-[var(--color-text-secondary)] text-lg">
                    {item.description}
                  </p>
                  {idx < 2 && (
                    <div className="hidden md:block absolute top-16 -right-4 text-[var(--color-accent)]/40">
                      <ChevronRight className="w-6 h-6" />
                    </div>
                  )}
                </div>
              </RevealOnScroll>
            ))}
          </div>
        </div>
      </section>

      {/* Planos Section - HIDDEN PENDING CLARITY */}
      <section id="planos" className="hidden py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display text-4xl sm:text-5xl font-bold text-white mb-4">
              {t('landing.plans.title')}
            </h2>
            <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
              {t('landing.plans.subtitle')}
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
            {[
              {
                id: 'basic',
                price: 29,
                highlight: false,
              },
              {
                id: 'pro',
                price: 59,
                highlight: true,
              },
              {
                id: 'premium',
                price: 99,
                highlight: false,
              },
            ].map((plan, idx) => {
              const planData = t(`landing.plans.items.${plan.id}`, { returnObjects: true }) as {
                name: string;
                description: string;
                features: string[];
              };

              return (
                <RevealOnScroll key={idx} delay={idx * 0.1}>
                  <div
                    className={`relative rounded-2xl p-8 transition-all duration-300 ${
                      plan.highlight
                        ? 'border border-[var(--color-accent)] bg-[rgba(34,211,238,0.05)] scale-105 md:scale-110'
                        : 'border border-[var(--color-border)] bg-[rgba(18,18,20,0.8)]'
                    } hover:border-[var(--color-accent)]/50`}
                  >
                    {plan.highlight && (
                      <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-3 py-1 rounded-full bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] text-white text-sm font-bold">
                        {t('landing.plans.recommended')}
                      </div>
                    )}
                    <h3 className="font-display text-2xl font-bold text-white mb-2">
                      {planData.name}
                    </h3>
                    <p className="text-[var(--color-text-secondary)] mb-6">
                      {planData.description}
                    </p>
                    <div className="mb-6">
                      <span className="font-display text-4xl font-extrabold text-white">
                        R${plan.price}
                      </span>
                      <span className="text-[var(--color-text-secondary)] ml-2">
                        {t('landing.plans.per_month')}
                      </span>
                    </div>
                    <Button
                      onClick={() => {
                        void navigate('/login');
                      }}
                      variant={plan.highlight ? 'primary' : 'secondary'}
                      fullWidth
                      className="mb-8"
                    >
                      {t('landing.plans.button')}
                    </Button>
                    <ul className="space-y-3">
                      {planData.features.map((feature, fidx) => (
                        <li
                          key={fidx}
                          className="flex items-start gap-3 text-[var(--color-text-secondary)]"
                        >
                          <span className="text-[var(--color-accent)] font-bold mt-1">
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
      <div className="w-full h-px bg-gradient-to-r from-transparent via-[var(--color-primary)]/20 to-transparent" />

      {/* Final CTA */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Glow */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="w-[500px] h-[300px] bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] opacity-[0.04] rounded-full blur-3xl" />
        </div>
        <div className="max-w-3xl mx-auto text-center relative z-10">
          <h2 className="font-display text-4xl sm:text-5xl font-bold text-white mb-6">
            {t('landing.cta.title')}
          </h2>
          <p className="text-lg text-[var(--color-text-secondary)] mb-8">
            {t('landing.cta.subtitle')}
          </p>
          <Button
            onClick={() => {
              void navigate('/login');
            }}
            variant="primary"
            size="lg"
            className="animate-pulse-glow"
          >
            {t('landing.cta.button')}
            <ChevronRight className="w-5 h-5" />
          </Button>
          <p className="text-xs text-[var(--color-text-secondary)] mt-4">
            {t('landing.cta.trial')}
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[var(--color-border)] bg-[rgba(10,10,11,0.5)] py-8 px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <img src="/logo_icon.png" alt="FityQ" className="h-7 w-7" />
            <span className="font-display text-base font-bold text-white">FityQ</span>
          </div>
          <p className="text-[var(--color-text-secondary)] text-sm">
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
