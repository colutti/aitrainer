/**
 * ProductShowcase
 * Decorative section showing 3 stylized CSS-only mockups of the FityQ product.
 * All data is hardcoded/fake — no store imports, no API calls.
 */
export const ProductShowcase = (): React.ReactNode => {
  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="font-display text-4xl sm:text-5xl font-bold text-white mb-4">
            Veja o FityQ em Ação
          </h2>
          <p className="text-lg text-[#a1a1aa] max-w-2xl mx-auto">
            Dashboard inteligente, chat contextual e análise metabólica — tudo em um só lugar.
          </p>
        </div>

        {/* Cards — horizontal scroll on mobile, grid on desktop */}
        <div className="flex overflow-x-auto snap-x snap-mandatory gap-6 pb-4 -mx-4 px-4 md:mx-0 md:px-0 md:grid md:grid-cols-3 md:overflow-visible">

          {/* Card 1: Dashboard */}
          <div className="snap-center min-w-[280px] flex-shrink-0 md:min-w-0 flex flex-col">
            <div className="flex-1 rounded-2xl border border-white/10 bg-[rgba(18,18,20,0.9)] p-5 shadow-xl">
              {/* Mock header bar */}
              <div className="flex items-center gap-1.5 mb-4">
                <div className="w-2 h-2 rounded-full bg-red-500/60" />
                <div className="w-2 h-2 rounded-full bg-yellow-500/60" />
                <div className="w-2 h-2 rounded-full bg-green-500/60" />
              </div>

              <p className="text-xs text-[#a1a1aa] mb-1">Meta Diária</p>
              <p className="font-display text-2xl font-extrabold text-white mb-4">
                2.150 <span className="text-sm font-normal text-[#a1a1aa]">kcal</span>
              </p>

              {/* Macro bars */}
              <div className="space-y-2.5 mb-4">
                {[
                  { name: 'Proteína', pct: 88, color: 'bg-emerald-500' },
                  { name: 'Gordura', pct: 80, color: 'bg-yellow-500' },
                  { name: 'Carbo', pct: 78, color: 'bg-blue-500' },
                ].map((m) => (
                  <div key={m.name}>
                    <div className="flex justify-between text-[10px] text-[#a1a1aa] mb-1">
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
              <div className="rounded-lg bg-white/[0.03] p-2.5">
                <p className="text-[10px] text-[#a1a1aa] mb-1.5">Peso (30 dias)</p>
                <svg width="100%" height="32" viewBox="0 0 160 32" preserveAspectRatio="none">
                  <polyline
                    points="0,26 25,22 50,24 75,16 100,12 130,8 160,4"
                    stroke="url(#pg1)" strokeWidth="1.5" strokeLinecap="round" fill="none"
                  />
                  <defs>
                    <linearGradient id="pg1" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#6366f1" />
                      <stop offset="100%" stopColor="#22d3ee" />
                    </linearGradient>
                  </defs>
                </svg>
              </div>
            </div>
            <p className="text-center text-sm font-medium text-[#a1a1aa] mt-3">Dashboard Inteligente</p>
          </div>

          {/* Card 2: Chat */}
          <div className="snap-center min-w-[280px] flex-shrink-0 md:min-w-0 flex flex-col">
            <div className="flex-1 rounded-2xl border border-white/10 bg-[rgba(18,18,20,0.9)] p-5 shadow-xl">
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
                  <p className="text-[10px] text-[#a1a1aa]">#força #hipertrofia #dados</p>
                </div>
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
              </div>

              {/* Messages */}
              <div className="space-y-3">
                <div className="flex justify-end">
                  <div className="bg-indigo-600/80 text-white text-xs rounded-xl rounded-tr-sm px-3 py-2 max-w-[75%]">
                    Fiz agachamento ontem, senti muito a panturrilha
                  </div>
                </div>
                <div className="flex justify-start">
                  <div className="bg-white/5 text-[#fafafa] text-xs rounded-xl rounded-tl-sm px-3 py-2 max-w-[80%] leading-relaxed">
                    Sentiu a panturrilha puxando? Seu tornozelo precisa de mais mobilidade. Antes da próxima série, tenta 10 rotações lentas em cada pé — depois me conta.
                  </div>
                </div>
                <div className="flex justify-end">
                  <div className="bg-indigo-600/80 text-white text-xs rounded-xl rounded-tr-sm px-3 py-2 max-w-[75%]">
                    Qual exercício você recomenda?
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
            <p className="text-center text-sm font-medium text-[#a1a1aa] mt-3">Chat com IA</p>
          </div>

          {/* Card 3: TDEE Analytics */}
          <div className="snap-center min-w-[280px] flex-shrink-0 md:min-w-0 flex flex-col">
            <div className="flex-1 rounded-2xl border border-white/10 bg-[rgba(18,18,20,0.9)] p-5 shadow-xl">
              <p className="text-xs text-[#a1a1aa] mb-4">Meta Calórica Inteligente</p>

              {/* Large ring */}
              <div className="flex justify-center mb-4">
                <div className="relative w-28 h-28">
                  <svg viewBox="0 0 112 112" className="w-28 h-28 -rotate-90">
                    <circle cx="56" cy="56" r="46" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
                    <circle
                      cx="56" cy="56" r="46"
                      fill="none"
                      stroke="url(#tdeeGrad)"
                      strokeWidth="8"
                      strokeLinecap="round"
                      strokeDasharray={`${(0.87 * 2 * Math.PI * 46).toString()} ${(2 * Math.PI * 46).toString()}`}
                    />
                    <defs>
                      <linearGradient id="tdeeGrad" x1="0" y1="0" x2="1" y2="0">
                        <stop offset="0%" stopColor="#6366f1" />
                        <stop offset="100%" stopColor="#22d3ee" />
                      </linearGradient>
                    </defs>
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="font-display text-xl font-extrabold text-white">87%</span>
                    <span className="text-[9px] text-[#a1a1aa]">precisão</span>
                  </div>
                </div>
              </div>

              <div className="text-center mb-4">
                <p className="font-display text-2xl font-extrabold text-white">2.487 kcal</p>
                <p className="text-xs text-[#a1a1aa] mt-0.5">Sua meta desta semana</p>
              </div>

              {/* Confidence badge */}
              <div className="flex justify-center mb-4">
                <span className="text-xs font-semibold bg-emerald-500/20 text-emerald-400 px-3 py-1 rounded-full border border-emerald-500/30">
                  Confiança Alta
                </span>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-2">
                {[
                  { label: 'Vs. semana anterior', value: '+87 kcal', color: 'text-orange-400' },
                  { label: 'Dados usados', value: '14 dias', color: 'text-cyan-400' },
                ].map((s) => (
                  <div key={s.label} className="rounded-lg bg-white/[0.03] p-2.5 text-center">
                    <p className={`text-sm font-bold font-display ${s.color}`}>{s.value}</p>
                    <p className="text-[10px] text-[#a1a1aa] mt-0.5">{s.label}</p>
                  </div>
                ))}
              </div>
            </div>
            <p className="text-center text-sm font-medium text-[#a1a1aa] mt-3">Meta Inteligente</p>
          </div>

        </div>

        {/* Mobile scroll hint */}
        <p className="text-center text-xs text-[#a1a1aa] mt-2 md:hidden">
          Deslize para ver mais →
        </p>
      </div>
    </section>
  );
};
