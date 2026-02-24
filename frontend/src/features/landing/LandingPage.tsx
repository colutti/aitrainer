import { Button } from '@shared/components/ui/Button';
import { useAuthStore } from '@shared/hooks/useAuth';
import {
  Zap,
  Brain,
  Users,
  Zap as Zest,
  Share2 as MemorySquare,
  Clock,
  ChevronDown,
  ExternalLink,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';


const LandingPage = (): React.ReactNode => {
  const navigate = useNavigate();
  // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/no-unsafe-return, @typescript-eslint/no-unsafe-member-access
  const isAuthenticated = Boolean(useAuthStore((state: any) => state.isAuthenticated));
  const [navScrolled, setNavScrolled] = useState(false);

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

  return (
    <div className="bg-gradient-to-br from-[var(--color-dark-bg)] via-[var(--color-dark-bg)] to-[#0f0f12] overflow-hidden">
      {/* Navbar */}
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          navScrolled
            ? 'bg-[rgba(10,10,11,0.8)] backdrop-blur-md border-b border-[var(--color-border)]'
            : 'bg-transparent'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">FityQ</span>
          </div>

          {/* Links */}
          <div className="hidden md:flex gap-8 items-center">
            <a
              href="#diferenciais"
              data-anchor
              className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors"
            >
              Diferenciais
            </a>
            <a
              href="#como-funciona"
              data-anchor
              className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors"
            >
              Como Funciona
            </a>
            <a
              href="#planos"
              data-anchor
              className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors"
            >
              Planos
            </a>
          </div>

          {/* CTA Button */}
          <Button
            onClick={() => {
              void navigate('/login');
            }}
            variant="primary"
            size="sm"
          >
            Entrar
          </Button>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="min-h-screen flex items-center justify-center px-4 sm:px-6 lg:px-8 pt-20 relative overflow-hidden">
        {/* Background gradient orbs */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-[var(--color-primary)] opacity-10 rounded-full blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-[var(--color-accent)] opacity-10 rounded-full blur-3xl" />
        </div>

        <div className="max-w-5xl w-full text-center relative z-10">
          <div className="mb-6 inline-block">
            <span className="px-4 py-2 rounded-full text-sm font-semibold text-[var(--color-accent)] bg-[rgba(34,211,238,0.1)] border border-[var(--color-accent)]/20">
              Nutrição & Treino Inteligente
            </span>
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-black leading-tight mb-6 text-white animate-slide-in-fade">
            Seu personal trainer com IA{' '}
            <span className="bg-gradient-to-r from-[var(--color-primary)] to-[var(--color-accent)] bg-clip-text text-transparent">
              que realmente te conhece
            </span>
          </h1>

          <p className="text-lg sm:text-xl text-[var(--color-text-secondary)] mb-8 max-w-3xl mx-auto leading-relaxed animate-slide-in-fade"
            style={{ animationDelay: '0.1s' }}>
            TDEE adaptativo ao seu metabolismo real, IA com acesso a seu histórico completo de treinos e nutrição, e 5 personalidades de treinadores disponíveis 24/7. Tudo integrado.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16 animate-slide-in-fade"
            style={{ animationDelay: '0.2s' }}>
            <Button
              onClick={() => {
                void navigate('/login');
              }}
              variant="primary"
              size="lg"
              fullWidth
              className="sm:w-auto"
            >
              Começar Agora
              <ChevronDown className="w-5 h-5 rotate-270" />
            </Button>
            <Button
              variant="secondary"
              size="lg"
              fullWidth
              className="sm:w-auto"
              onClick={() => {
                void navigate('/login');
              }}
            >
              Conhecer Mais
            </Button>
          </div>

          {/* Feature badges */}
          <div className="flex flex-wrap justify-center gap-6 text-sm text-[var(--color-text-secondary)] animate-slide-in-fade"
            style={{ animationDelay: '0.3s' }}>
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
      </section>

      {/* Diferenciais Section */}
      <section id="diferenciais" className="py-20 px-4 sm:px-6 lg:px-8 relative">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-black text-white mb-4">
              O que torna FityQ diferente
            </h2>
            <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
              Combinação única de tecnologia, personalização e acesso real aos seus dados
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: Zap as React.ElementType,
                title: 'TDEE Adaptativo',
                description:
                  'Cálculo metabólico que evolui com seus dados reais. Não é tabela genérica.',
              },
              {
                icon: Brain as React.ElementType,
                title: 'IA Contextual',
                description:
                  'Acesso completo ao seu histórico de treinos, nutrição, peso e composição corporal.',
              },
              {
                icon: Users as React.ElementType,
                title: '5 Treinadores',
                description:
                  'Atlas, Luna, Sofia, Sargento e GymBro. Escolha a personalidade que combina com você.',
              },
              {
                icon: Zest as React.ElementType,
                title: 'Integrações',
                description:
                  'Sincroniza com Hevy, MyFitnessPal, Zepp Life e outros apps que você usa.',
              },
              {
                icon: MemorySquare as React.ElementType,
                title: 'Memória Longa',
                description:
                  'A IA lembra de sua evolução, objetivos e preferências ao longo do tempo.',
              },
              {
                icon: Clock as React.ElementType,
                title: 'Disponível 24/7',
                description:
                  'Seu treinador está sempre lá. Às 3 da manhã, no fim de semana ou quando precisar.',
              },
            ].map((feature, idx) => {
              const Icon = feature.icon;
              return (
                <RevealOnScroll key={idx} delay={idx * 0.1}>
                  <div className="group relative p-8 rounded-2xl border border-[var(--color-border)] bg-[rgba(18,18,20,0.8)] backdrop-blur-sm hover:bg-[rgba(18,18,20,0.95)] hover:border-[var(--color-accent)]/50 transition-all duration-300">
                    <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-[var(--color-primary)]/5 to-[var(--color-accent)]/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                    <div className="relative z-10">
                      <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                        <Icon className="w-6 h-6 text-white" />
                      </div>
                      <h3 className="text-xl font-bold text-white mb-2">
                        {feature.title}
                      </h3>
                      <p className="text-[var(--color-text-secondary)]">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                </RevealOnScroll>
              );
            })}
          </div>
        </div>
      </section>

      {/* Como Funciona Section */}
      <section
        id="como-funciona"
        className="py-20 px-4 sm:px-6 lg:px-8 relative"
      >
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-black text-white mb-4">
              Como Funciona
            </h2>
            <p className="text-lg text-[var(--color-text-secondary)] max-w-2xl mx-auto">
              Começar é simples. Três passos e você está treino.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: '01',
                title: 'Crie sua Conta',
                description:
                  'Registre-se com email ou integre com sua conta existente. Leva 2 minutos.',
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
                  <div className="text-7xl font-black text-[var(--color-primary)]/10 mb-4">
                    {item.step}
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-3">
                    {item.title}
                  </h3>
                  <p className="text-[var(--color-text-secondary)] text-lg">
                    {item.description}
                  </p>
                  {idx < 2 && (
                    <div className="hidden md:block absolute top-20 -right-4 text-[var(--color-accent)]/50">
                      <ChevronDown className="w-6 h-6 rotate-270" />
                    </div>
                  )}
                </div>
              </RevealOnScroll>
            ))}
          </div>
        </div>
      </section>

      {/* Planos Section */}
      <section id="planos" className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-black text-white mb-4">
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
                  <h3 className="text-2xl font-bold text-white mb-2">
                    {plan.name}
                  </h3>
                  <p className="text-[var(--color-text-secondary)] mb-6">
                    {plan.description}
                  </p>
                  <div className="mb-6">
                    <span className="text-4xl font-black text-white">
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
                    Começar Agora
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

      {/* Final CTA */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 relative">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-4xl sm:text-5xl font-black text-white mb-6">
            Pronto para transformar seu treino?
          </h2>
          <p className="text-lg text-[var(--color-text-secondary)] mb-8">
            Junte-se a milhares de pessoas que já estão alcançando seus objetivos com um treinador IA personalizado.
          </p>
          <Button
            onClick={() => {
              void navigate('/login');
            }}
            variant="primary"
            size="lg"
          >
            Começar Gratuitamente
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-[var(--color-border)] bg-[rgba(10,10,11,0.5)] py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[var(--color-primary)] to-[var(--color-accent)] flex items-center justify-center">
                  <Zap className="w-5 h-5 text-white" />
                </div>
                <span className="text-lg font-bold text-white">FityQ</span>
              </div>
              <p className="text-[var(--color-text-secondary)]">
                Seu personal trainer com IA que realmente te conhece.
              </p>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Produto</h4>
              <ul className="space-y-2">
                <li>
                  <a
                    href="#diferenciais"
                    data-anchor
                    className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors"
                  >
                    Recursos
                  </a>
                </li>
                <li>
                  <a
                    href="#planos"
                    data-anchor
                    className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors"
                  >
                    Preços
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Legal</h4>
              <ul className="space-y-2">
                <li>
                  <a
                    href="#"
                    className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors"
                  >
                    Privacidade
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors"
                  >
                    Termos
                  </a>
                </li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-bold mb-4">Social</h4>
              <ul className="space-y-2">
                <li>
                  <a
                    href="#"
                    className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors flex items-center gap-2"
                  >
                    Twitter <ExternalLink className="w-4 h-4" />
                  </a>
                </li>
                <li>
                  <a
                    href="#"
                    className="text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors flex items-center gap-2"
                  >
                    Instagram <ExternalLink className="w-4 h-4" />
                  </a>
                </li>
              </ul>
            </div>
          </div>
          <div className="border-t border-[var(--color-border)] pt-8 text-center text-[var(--color-text-secondary)]">
            <p>© 2025 FityQ. Todos os direitos reservados.</p>
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
