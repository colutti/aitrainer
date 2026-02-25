import { Button } from '@shared/components/ui/Button';
import { useAuthStore } from '@shared/hooks/useAuth';
import {
  Zap,
  Brain,
  Users,
  Zap as Zest,
  Share2 as MemorySquare,
  Clock,
  ChevronRight,
  ExternalLink,
  Menu,
  X,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ChatCarousel } from './ChatCarousel';
import { HeroProductPreview } from './HeroProductPreview';
import { ProductShowcase } from './ProductShowcase';
import { SocialProof } from './SocialProof';
import { TrainerShowcase } from './TrainerShowcase';


const LandingPage = (): React.ReactNode => {
  const navigate = useNavigate();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-return, @typescript-eslint/no-unsafe-member-access
  const isAuthenticated = Boolean(useAuthStore((state: any) => state.isAuthenticated));
  const [navScrolled, setNavScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
    { href: '#treinadores', label: 'Treinadores' },
    { href: '#diferenciais', label: 'Diferenciais' },
    { href: '#como-funciona', label: 'Como Funciona' },
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
            <Button
              onClick={() => {
                void navigate('/login');
              }}
              variant="primary"
              size="sm"
            >
              Entrar
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
                Nutrição & Treino Inteligente
              </span>
            </div>

            <h1 className="font-display text-5xl sm:text-6xl lg:text-7xl font-extrabold leading-tight mb-6 text-white animate-slide-in-fade">
              Seu personal trainer com IA{' '}
              <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">
                que realmente te conhece
              </span>
            </h1>

            <p
              className="text-lg sm:text-xl text-[var(--color-text-secondary)] mb-8 max-w-2xl leading-relaxed animate-slide-in-fade"
              style={{ animationDelay: '0.1s' }}
            >
              TDEE adaptativo ao seu metabolismo real, IA com acesso ao seu histórico completo de treinos e nutrição, e 5 personalidades de treinadores disponíveis 24/7.
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
                Experimentar Grátis
                <ChevronRight className="w-5 h-5" />
              </Button>
            </div>

            <p className="text-xs text-[var(--color-text-secondary)] mb-10 animate-slide-in-fade" style={{ animationDelay: '0.25s' }}>
              Sem cartão de crédito. Comece em 2 minutos.
            </p>

            {/* Feature badges */}
            <div
              className="flex flex-wrap gap-4 text-sm text-[var(--color-text-secondary)] animate-slide-in-fade"
              style={{ animationDelay: '0.3s' }}
            >
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-[var(--color-accent)]" />
                24/7 Disponível
              </div>
              <div className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-[var(--color-accent)]" />
                IA Contextual
              </div>
              <div className="flex items-center gap-2">
                <Zest className="w-4 h-4 text-[var(--color-accent)]" />
                Integrações
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
              O que torna FityQ diferente
            </h2>
            <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
              Combinação única de tecnologia, personalização e acesso real aos seus dados
            </p>
          </div>

          {/* Bento grid */}
          <div className="grid md:grid-cols-3 gap-4">

            {/* TDEE — col-span-2, large */}
            <RevealOnScroll delay={0}>
              <div className="group relative p-8 rounded-2xl border border-[var(--color-border)] bg-[rgba(18,18,20,0.8)] backdrop-blur-sm hover:border-[var(--color-primary)]/40 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-[var(--color-primary)]/10 transition-all duration-300 md:col-span-2 h-full">
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-[var(--color-primary)]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="relative z-10 flex flex-col sm:flex-row gap-8 items-start">
                  <div className="flex-1">
                    <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center mb-4">
                      <Zap className="w-6 h-6 text-white" />
                    </div>
                    <h3 className="font-display text-2xl font-bold text-white mb-3">TDEE Adaptativo</h3>
                    <p className="text-[var(--color-text-secondary)] text-base leading-relaxed">
                      Cálculo metabólico que evolui com seus dados reais de treino, sono, estresse e composição corporal. Não é tabela genérica — é inteligência metabólica personalizada.
                    </p>
                  </div>
                  {/* Mini chart decoration */}
                  <div className="shrink-0 hidden sm:block">
                    <svg width="120" height="64" viewBox="0 0 120 64" fill="none" className="opacity-60">
                      <polyline
                        points="0,52 20,44 40,48 60,32 80,24 100,16 120,8"
                        stroke="url(#grad)"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        fill="none"
                      />
                      <defs>
                        <linearGradient id="grad" x1="0" y1="0" x2="120" y2="0">
                          <stop offset="0%" stopColor="#6366f1" />
                          <stop offset="100%" stopColor="#22d3ee" />
                        </linearGradient>
                      </defs>
                    </svg>
                    <p className="text-xs text-[var(--color-text-secondary)] text-center mt-1">TDEE ao longo do tempo</p>
                  </div>
                </div>
              </div>
            </RevealOnScroll>

            {/* IA Contextual */}
            <RevealOnScroll delay={0.05}>
              <div className="group relative p-8 rounded-2xl border border-[var(--color-border)] bg-[rgba(18,18,20,0.8)] backdrop-blur-sm hover:border-[var(--color-accent)]/40 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-[var(--color-accent)]/10 transition-all duration-300 h-full">
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-[var(--color-accent)]/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="relative z-10">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center mb-4">
                    <Brain className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="font-display text-xl font-bold text-white mb-2">IA Contextual</h3>
                  <p className="text-[var(--color-text-secondary)]">
                    Acesso completo ao seu histórico de treinos, nutrição, peso e composição corporal. A IA vê o quadro completo.
                  </p>
                </div>
              </div>
            </RevealOnScroll>

            {/* 5 Treinadores */}
            <RevealOnScroll delay={0.1}>
              <div className="group relative p-6 rounded-2xl border border-[var(--color-border)] bg-[rgba(18,18,20,0.8)] backdrop-blur-sm hover:border-pink-500/40 hover:-translate-y-0.5 hover:shadow-lg hover:shadow-pink-500/10 transition-all duration-300 h-full">
                <div className="relative z-10">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center mb-4">
                    <Users className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="font-display text-xl font-bold text-white mb-2">5 Treinadores</h3>
                  <p className="text-[var(--color-text-secondary)] text-sm mb-4">
                    Atlas, Luna, Sofia, Sargento e GymBro. Cada um com personalidade única.
                  </p>
                  {/* Overlapping avatars */}
                  <div className="flex items-center">
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
                </div>
              </div>
            </RevealOnScroll>

            {/* Integrações */}
            <RevealOnScroll delay={0.15}>
              <div className="group relative p-6 rounded-2xl border border-[var(--color-border)] bg-[rgba(18,18,20,0.8)] backdrop-blur-sm hover:border-amber-500/40 hover:-translate-y-0.5 transition-all duration-300 h-full">
                <div className="relative z-10">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center mb-4">
                    <Zest className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="font-display text-xl font-bold text-white mb-2">Integrações</h3>
                  <p className="text-[var(--color-text-secondary)] text-sm mb-3">
                    Sincroniza com os apps que você já usa:
                  </p>
                  <div className="flex flex-col gap-1">
                    {['Hevy', 'MyFitnessPal', 'Zepp Life'].map((app) => (
                      <span key={app} className="text-xs font-semibold text-[var(--color-accent)] bg-[var(--color-accent)]/10 rounded px-2 py-0.5 w-fit">
                        {app}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </RevealOnScroll>

            {/* Memória Longa */}
            <RevealOnScroll delay={0.2}>
              <div className="group relative p-6 rounded-2xl border border-[var(--color-border)] bg-[rgba(18,18,20,0.8)] backdrop-blur-sm hover:border-indigo-400/40 hover:-translate-y-0.5 transition-all duration-300 h-full">
                <div className="relative z-10">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center mb-4">
                    <MemorySquare className="w-6 h-6 text-white" />
                  </div>
                  <h3 className="font-display text-xl font-bold text-white mb-2">Memória Longa</h3>
                  <p className="text-[var(--color-text-secondary)] text-sm mb-4">A IA lembra da sua jornada completa.</p>
                  {/* Mini timeline */}
                  <div className="space-y-2">
                    {[
                      { label: 'Iniciou treino', dot: 'bg-indigo-400' },
                      { label: 'Atingiu meta de peso', dot: 'bg-cyan-400' },
                      { label: 'Novo PR pessoal', dot: 'bg-green-400' },
                    ].map((item, i) => (
                      <div key={i} className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${item.dot} shrink-0`} />
                        <span className="text-xs text-[var(--color-text-secondary)]">{item.label}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </RevealOnScroll>

            {/* 24/7 — full width */}
            <RevealOnScroll delay={0.25}>
              <div className="group relative p-6 rounded-2xl border border-[var(--color-border)] bg-[rgba(18,18,20,0.8)] backdrop-blur-sm hover:border-green-500/40 hover:-translate-y-0.5 transition-all duration-300 md:col-span-3">
                <div className="relative z-10 flex items-center gap-6 flex-wrap">
                  <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center shrink-0">
                    <Clock className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-1">
                      <h3 className="font-display text-xl font-bold text-white">Disponível 24/7</h3>
                      <div className="flex items-center gap-1.5">
                        <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                        <span className="text-xs text-green-400 font-medium">Online agora</span>
                      </div>
                    </div>
                    <p className="text-[var(--color-text-secondary)]">
                      Seu treinador está sempre lá. Às 3 da manhã, no fim de semana, ou quando você mais precisar.
                    </p>
                  </div>
                </div>
              </div>
            </RevealOnScroll>

          </div>
        </div>
      </section>

      {/* Section divider */}
      <div className="w-full h-px bg-gradient-to-r from-transparent via-[var(--color-primary)]/20 to-transparent" />

      {/* Social Proof */}
      <div className="relative z-10">
        <SocialProof />
      </div>

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
              Como Funciona
            </h2>
            <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
              Começar é simples. Três passos e você está em ação.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                title: 'Crie sua Conta',
                description:
                  'Registre-se com email em segundos. Leva menos de 2 minutos.',
              },
              {
                step: '02',
                title: 'Escolha seu Treinador',
                description:
                  'Conheça Atlas, Luna, Sofia, Sargento ou GymBro. Cada um tem uma abordagem única.',
              },
              {
                step: '03',
                title: 'Converse e Evolua',
                description:
                  'Chat com seu treinador, registre treinos e nutrição, acompanhe progresso em tempo real.',
              },
            ].map((item, idx) => (
              <RevealOnScroll key={idx} delay={idx * 0.15}>
                <div className="relative">
                  <div className="font-display text-8xl font-extrabold text-[var(--color-primary)]/10 mb-4 leading-none">
                    {item.step}
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
              Escolha seu Plano
            </h2>
            <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
              Todos os planos incluem suporte e atualizações. Cancele quando quiser.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
            {[
              {
                name: 'Básico',
                price: 29,
                description: 'Perfeito para começar',
                features: [
                  '1 Treinador',
                  'Chat Limitado (50/mês)',
                  'Tracking Básico',
                  'TDEE Padrão',
                  'Suporte por Email',
                ],
                highlight: false,
              },
              {
                name: 'Pro',
                price: 59,
                description: 'Recomendado para resultados',
                features: [
                  'Todos os 5 Treinadores',
                  'Chat Ilimitado',
                  'TDEE Adaptativo',
                  'Integrações (Hevy, MyFitnessPal, Zepp)',
                  'Memória Ilimitada',
                  'Suporte Prioritário',
                ],
                highlight: true,
              },
              {
                name: 'Premium',
                price: 99,
                description: 'Para máximo impacto',
                features: [
                  'Tudo do Pro',
                  'Chat com Prioridade',
                  'Relatórios Avançados',
                  'Análise de Composição Corporal',
                  'Suporte 24/7',
                  'Customizações Personalizadas',
                ],
                highlight: false,
              },
            ].map((plan, idx) => (
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
                      Recomendado
                    </div>
                  )}
                  <h3 className="font-display text-2xl font-bold text-white mb-2">
                    {plan.name}
                  </h3>
                  <p className="text-[var(--color-text-secondary)] mb-6">
                    {plan.description}
                  </p>
                  <div className="mb-6">
                    <span className="font-display text-4xl font-extrabold text-white">
                      R${plan.price}
                    </span>
                    <span className="text-[var(--color-text-secondary)] ml-2">
                      /mês
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
                    Experimentar Grátis
                  </Button>
                  <ul className="space-y-3">
                    {plan.features.map((feature, fidx) => (
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
            ))}
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
            Pronto para ter um treinador que realmente entende você?
          </h2>
          <p className="text-lg text-[var(--color-text-secondary)] mb-8">
            Tecnologia que se adapta ao seu metabolismo, treinadores com personalidade, e IA que lembra da sua jornada.
          </p>
          <Button
            onClick={() => {
              void navigate('/login');
            }}
            variant="primary"
            size="lg"
            className="animate-pulse-glow"
          >
            Experimentar Grátis
            <ChevronRight className="w-5 h-5" />
          </Button>
          <p className="text-xs text-[var(--color-text-secondary)] mt-4">
            Sem cartão de crédito. Comece em 2 minutos.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[var(--color-border)] bg-[rgba(10,10,11,0.5)] py-12 px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <img src="/logo_icon.png" alt="FityQ" className="h-8 w-8" />
                <span className="font-display text-lg font-bold text-white">FityQ</span>
              </div>
              <p className="text-[var(--color-text-secondary)] text-sm">
                Treinador pessoal com IA que evolui com você.
              </p>
            </div>
            <div>
              <h4 className="font-display text-white font-bold mb-4">Produto</h4>
              <ul className="space-y-2">
                <li>
                  <a
                    href="#treinadores"
                    data-anchor
                    className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors text-sm"
                  >
                    Treinadores
                  </a>
                </li>
                <li>
                  <a
                    href="#diferenciais"
                    data-anchor
                    className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors text-sm"
                  >
                    Recursos
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-display text-white font-bold mb-4">Legal</h4>
              <ul className="space-y-2">
                <li>
                  <a
                    href="#"
                    className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors text-sm"
                  >
                    Privacidade
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors text-sm"
                  >
                    Termos
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="font-display text-white font-bold mb-4">Social</h4>
              <ul className="space-y-2">
                <li>
                  <a
                    href="#"
                    className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors flex items-center gap-2 text-sm"
                  >
                    Twitter <ExternalLink className="w-3 h-3" />
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors flex items-center gap-2 text-sm"
                  >
                    Instagram <ExternalLink className="w-3 h-3" />
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-[var(--color-border)] pt-8 text-center text-[var(--color-text-secondary)] text-sm">
            <p>© {new Date().getFullYear()} FityQ. Todos os direitos reservados.</p>
          </div>
        </div>
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
