import { Button } from '@shared/components/ui/Button';
import { ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';


/**
 * ProductShowcase
 * Decorative section showing 3 stylized CSS-only mockups of the FityQ product.
 * All data is hardcoded/fake — no store imports, no API calls.
 */
export const ProductShowcase = (): React.ReactNode => {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <section className="py-12 md:py-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="font-display text-4xl sm:text-5xl font-bold text-white mb-4">
            {t('landing.showcase.title')}
          </h2>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto">
            {t('landing.showcase.description')}
          </p>
        </div>

        {/* Cards — Stacked on mobile, grid on desktop */}
        <div className="flex flex-col gap-8 md:grid md:grid-cols-3 md:gap-6">

          {/* Card 1: Dashboard */}
          <div className="flex flex-col h-full">
            <div className="flex-1 rounded-2xl border border-white/10 bg-secondary/90 p-5 shadow-xl">
              {/* Mock header bar */}
              <div className="flex items-center gap-1.5 mb-4">
                <div className="w-2 h-2 rounded-full bg-red-500/60" />
                <div className="w-2 h-2 rounded-full bg-yellow-500/60" />
                <div className="w-2 h-2 rounded-full bg-green-500/60" />
              </div>

              <p className="text-xs text-text-secondary mb-1">{t('landing.hero.daily_goal')}</p>
              <p className="font-display text-2xl font-extrabold text-white mb-4">
                2.150 <span className="text-sm font-normal text-text-secondary">kcal</span>
              </p>

              {/* Macro bars */}
              <div className="space-y-2.5 mb-4">
                {[
                  { name: t('landing.hero.macro_protein'), pct: 88, color: 'bg-emerald-500' },
                  { name: t('landing.hero.macro_fat'), pct: 80, color: 'bg-yellow-500' },
                  { name: t('landing.hero.macro_carbs'), pct: 78, color: 'bg-blue-500' },
                ].map((m) => (
                  <div key={m.name}>
                    <div className="flex justify-between text-[10px] text-text-secondary mb-1">
                      <span>{m.name}</span>
                      <span>{m.pct}%</span>
                    </div>
                    <div className="h-1 rounded-full bg-white/5">
                      <div className={`h-full rounded-full ${m.color} opacity-70`} style={{ width: `${m.pct.toString()}%` }} />
                    </div>
                  </div>
                ))}
              </div>

              {/* Mini chart */}
              <div className="rounded-lg bg-white/3 p-2.5">
                <p className="text-[10px] text-text-secondary mb-1.5">{t('landing.showcase.weight_30d')}</p>
                <svg width="100%" height="32" viewBox="0 0 160 32" preserveAspectRatio="none">
                  <polyline
                    points="0,26 25,22 50,24 75,16 100,12 130,8 160,4"
                    stroke="url(#pg1Showcase)" strokeWidth="1.5" strokeLinecap="round" fill="none"
                  />
                  <defs>
                    <linearGradient id="pg1Showcase" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="var(--color-primary)" />
                      <stop offset="100%" stopColor="var(--color-accent)" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
            </div>
            <p className="text-center text-sm font-medium text-text-secondary mt-3">{t('landing.showcase.dashboard_title')}</p>
          </div>

          {/* Card 2: Chat */}
          <div className="flex flex-col h-full">
            <div className="flex-1 rounded-2xl border border-white/10 bg-secondary/90 p-5 shadow-xl">
              {/* Trainer header */}
              <div className="flex items-center gap-2.5 mb-4 pb-3 border-b border-white/5">
                <img
                  src="/assets/avatars/atlas.png"
                  alt="Atlas"
                  className="w-8 h-8 rounded-lg object-cover"
                  loading="lazy"
                  width="32"
                  height="32"
                />
                <div>
                  <p className="font-display text-sm font-bold text-white">Atlas Prime</p>
                  <p className="text-[10px] text-text-secondary">#força #hipertrofia #dados</p>
                </div>
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              </div>

              {/* Messages */}
              <div className="space-y-3">
                <div className="flex justify-end">
                  <div className="bg-primary/80 text-white text-xs rounded-xl rounded-tr-sm px-3 py-2 max-w-[75%]">
                    {t('landing.conversations.sofia.user_1')}
                  </div>
                </div>
                <div className="flex justify-start">
                  <div className="bg-white/5 text-text-primary text-xs rounded-xl rounded-tl-sm px-3 py-2 max-w-[80%] leading-relaxed">
                    {t('landing.conversations.sofia.trainer_1')}
                  </div>
                </div>
                <div className="flex justify-end">
                  <div className="bg-primary/80 text-white text-xs rounded-xl rounded-tr-sm px-3 py-2 max-w-[75%]">
                    {t('landing.conversations.sofia.user_2')}
                  </div>
                </div>
                {/* Typing indicator */}
                <div className="flex justify-start">
                  <div className="bg-white/5 rounded-xl rounded-tl-sm px-3 py-2.5">
                    <div className="flex gap-1 items-center">
                      {[0, 150, 300].map((delay) => (
                        <div
                          key={delay}
                          className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce"
                          style={{ animationDelay: `${delay.toString()}ms` }}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <p className="text-center text-sm font-medium text-text-secondary mt-3">{t('landing.showcase.chat_title')}</p>
          </div>

          {/* Card 3: TDEE Analytics */}
          <div className="flex flex-col h-full">
            <div className="flex-1 rounded-2xl border border-white/10 bg-secondary/90 p-5 shadow-xl">
              <p className="text-xs text-text-secondary mb-4">{t('landing.showcase.meta_calorie_title')}</p>

              {/* Large ring */}
              <div className="flex justify-center mb-4">
                <div className="relative w-28 h-28">
                  <svg viewBox="0 0 112 112" className="w-28 h-28 -rotate-90">
                    <circle cx="56" cy="56" r="46" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
                    <circle
                      cx="56" cy="56" r="46"
                      fill="none"
                      stroke="url(#tdeeGradShowcase)"
                      strokeWidth="8"
                      strokeLinecap="round"
                      strokeDasharray={`${(0.87 * 2 * Math.PI * 46).toString()} ${(2 * Math.PI * 46).toString()}`}
                    />
                    <defs>
                      <linearGradient id="tdeeGradShowcase" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="var(--color-primary)" />
                        <stop offset="100%" stopColor="var(--color-accent)" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="font-display text-xl font-extrabold text-white">87%</span>
                    <span className="text-[9px] text-text-secondary">{t('landing.showcase.accuracy')}</span>
                  </div>
                </div>
              </div>

              <div className="text-center mb-4">
                <p className="font-display text-2xl font-extrabold text-white">2.487 kcal</p>
                <p className="text-xs text-text-secondary mt-0.5">{t('landing.showcase.weekly_target_title')}</p>
              </div>

              {/* Confidence badge */}
              <div className="flex justify-center mb-4">
                <span className="text-xs font-semibold bg-emerald-500/20 text-emerald-400 px-3 py-1 rounded-full border border-emerald-500/30">
                  {t('landing.showcase.high_confidence')}
                </span>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-2">
                {[
                  { label: t('landing.showcase.vs_previous'), value: '+87 kcal', color: 'text-orange-400' },
                  { label: t('landing.showcase.data_used'), value: t('landing.showcase.days_count', { count: 14 }), color: 'text-cyan-400' },
                ].map((s) => (
                  <div key={s.label} className="rounded-lg bg-white/3 p-2.5 text-center">
                    <p className={`text-sm font-bold font-display ${s.color}`}>{s.value}</p>
                    <p className="text-[10px] text-text-secondary mt-0.5">{s.label}</p>
                  </div>
                ))}
              </div>
            </div>
            <p className="text-center text-sm font-medium text-text-secondary mt-3">{t('landing.showcase.meta_title')}</p>
          </div>

        </div>

        {/* CTA Button */}
        <div className="mt-16 flex justify-center">
          <Button
            onClick={() => { void navigate('/login'); }}
            variant="secondary"
            size="lg"
            className="group"
          >
            {t('landing.cta_product')}
            <ChevronRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
          </Button>
        </div>
      </div>
    </section>
  );
};
