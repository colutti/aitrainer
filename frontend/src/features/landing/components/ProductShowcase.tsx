import { Button } from '@shared/components/ui/Button';
import { ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

export const ProductShowcase = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 border-t border-border bg-dark-bg">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="font-display text-3xl font-bold text-text-primary mb-4">
            {t('landing.showcase.title')}
          </h2>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto">
            {t('landing.showcase.description')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Card 1: Dashboard */}
          <div className="flex flex-col">
            <div className="flex-1 rounded-lg border border-border bg-light-bg p-6 shadow-sm">
              <div className="flex items-center gap-1.5 mb-6">
                <div className="w-2.5 h-2.5 rounded-full bg-border" />
                <div className="w-2.5 h-2.5 rounded-full bg-border" />
                <div className="w-2.5 h-2.5 rounded-full bg-border" />
              </div>

              <p className="text-xs text-text-muted mb-1">{t('landing.hero.daily_goal')}</p>
              <p className="font-display text-3xl font-bold text-text-primary mb-6">
                2.150 <span className="text-sm font-normal text-text-muted">kcal</span>
              </p>

              <div className="space-y-4 mb-6">
                {[
                  { name: t('landing.hero.macro_protein'), pct: 88, color: 'bg-primary' },
                  { name: t('landing.hero.macro_fat'), pct: 80, color: 'bg-primary/60' },
                  { name: t('landing.hero.macro_carbs'), pct: 78, color: 'bg-primary/30' },
                ].map((m) => (
                  <div key={m.name}>
                    <div className="flex justify-between text-[10px] font-semibold text-text-secondary mb-1.5 uppercase tracking-wider">
                      <span>{m.name}</span>
                      <span>{m.pct.toString()}%</span>
                    </div>
                    <div className="h-1.5 rounded-full bg-secondary">
                      <div className={`h-full rounded-full ${m.color}`} style={{ width: `${m.pct.toString()}%` }} />
                    </div>
                  </div>
                ))}
              </div>

              <div className="rounded border border-border bg-dark-bg p-3">
                <p className="text-[10px] text-text-muted mb-2 uppercase font-bold tracking-tight">{t('landing.showcase.weight_30d')}</p>
                <div className="h-8 w-full bg-primary/5 rounded border border-primary/10 flex items-end px-1 pb-1">
                  <svg className="w-full h-full" viewBox="0 0 100 20" preserveAspectRatio="none">
                    <path
                      d="M0,18 L10,15 L20,16 L30,12 L40,14 L50,8 L60,10 L70,5 L80,7 L90,2 L100,4"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="text-primary"
                    />
                  </svg>
                </div>
              </div>
            </div>
            <p className="text-center text-sm font-bold text-text-secondary mt-4 uppercase tracking-wide">{t('landing.showcase.dashboard_title')}</p>
          </div>

          {/* Card 2: Chat */}
          <div className="flex flex-col">
            <div className="flex-1 rounded-lg border border-border bg-light-bg p-6 shadow-sm">
              <div className="flex items-center gap-3 mb-6 pb-4 border-b border-border">
                <img
                  src="/assets/avatars/sofia.png"
                  alt="Sofia"
                  className="w-10 h-10 rounded object-cover border border-border"
                />
                <div>
                  <p className="font-bold text-sm text-text-primary">Dra. Sofia Pulse</p>
                  <p className="text-[10px] text-text-muted uppercase tracking-wider font-semibold">{t('landing.showcase.active_now')}</p>
                </div>
              </div>

              <div className="space-y-4">
                <div className="flex justify-end">
                  <div className="bg-primary text-white text-xs rounded-lg px-4 py-2.5 max-w-[85%]">
                    {t('landing.conversations.sofia.user_1')}
                  </div>
                </div>
                <div className="flex justify-start">
                  <div className="bg-secondary border border-border text-text-primary text-xs rounded-lg px-4 py-2.5 max-w-[90%] leading-relaxed">
                    {t('landing.conversations.sofia.trainer_1')}
                  </div>
                </div>
                <div className="flex justify-end">
                  <div className="bg-primary text-white text-xs rounded-lg px-4 py-2.5 max-w-[85%]">
                    {t('landing.conversations.sofia.user_2')}
                  </div>
                </div>
              </div>
            </div>
            <p className="text-center text-sm font-bold text-text-secondary mt-4 uppercase tracking-wide">{t('landing.showcase.chat_title')}</p>
          </div>

          {/* Card 3: TDEE Analytics */}
          <div className="flex flex-col">
            <div className="flex-1 rounded-lg border border-border bg-light-bg p-6 shadow-sm">
              <p className="text-xs text-text-muted mb-6 uppercase font-bold tracking-tight">{t('landing.showcase.meta_calorie_title')}</p>

              <div className="flex justify-center mb-8">
                <div className="relative w-32 h-32 flex flex-col items-center justify-center border-4 border-secondary rounded-full">
                  <div className="absolute inset-0 border-4 border-primary rounded-full border-t-transparent -rotate-45" />
                  <span className="text-2xl font-bold text-text-primary">87%</span>
                  <span className="text-[9px] text-text-muted uppercase font-bold tracking-widest">{t('landing.showcase.accuracy')}</span>
                </div>
              </div>

              <div className="text-center mb-8">
                <p className="font-display text-3xl font-bold text-text-primary">2.487 kcal</p>
                <p className="text-xs text-text-muted mt-1 uppercase tracking-wider">{t('landing.showcase.weekly_target_title')}</p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: t('landing.showcase.vs_previous'), value: '+87 kcal', color: 'text-primary' },
                  { label: t('landing.showcase.data_used'), value: t('landing.showcase.days_count', { count: 14 }), color: 'text-text-primary' },
                ].map((s) => (
                  <div key={s.label} className="rounded border border-border bg-dark-bg p-3 text-center">
                    <p className={`text-sm font-bold ${s.color}`}>{s.value}</p>
                    <p className="text-[9px] text-text-muted mt-1 uppercase font-bold tracking-tighter">{s.label}</p>
                  </div>
                ))}
              </div>
            </div>
            <p className="text-center text-sm font-bold text-text-secondary mt-4 uppercase tracking-wide">{t('landing.showcase.meta_title')}</p>
          </div>
        </div>

        <div className="mt-16 text-center">
          <Button
            onClick={() => { void navigate('/login'); }}
            variant="secondary"
            className="border-border bg-dark-card rounded-md inline-flex items-center gap-2"
          >
            {t('landing.cta_product')}
            <ChevronRight size={16} />
          </Button>
        </div>
      </div>
    </section>
  );
};
