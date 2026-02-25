/**
 * HeroProductPreview
 * Decorative component for the landing page hero section.
 * Renders a stylized mock of the FityQ dashboard — purely visual,
 * no real data, no store imports.
 */
export const HeroProductPreview = (): React.ReactNode => {
  return (
    <div className="relative animate-float">
      {/* Glow behind card */}
      <div className="absolute inset-0 bg-gradient-to-br from-[#6366f1]/20 to-[#22d3ee]/10 rounded-3xl blur-2xl scale-110 pointer-events-none" />

      {/* Main dashboard card */}
      <div className="relative rounded-2xl border border-white/10 bg-[rgba(18,18,20,0.95)] p-6 shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-xs text-[#a1a1aa] mb-0.5">Meta Diária</p>
            <p className="text-3xl font-display font-extrabold text-white">2.150 <span className="text-base font-normal text-[#a1a1aa]">kcal</span></p>
          </div>
          {/* Consistency ring */}
          <div className="relative w-16 h-16">
            <svg viewBox="0 0 64 64" className="w-16 h-16 -rotate-90">
              <circle cx="32" cy="32" r="26" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="6" />
              <circle
                cx="32" cy="32" r="26"
                fill="none"
                stroke="url(#ringGrad)"
                strokeWidth="6"
                strokeLinecap="round"
                strokeDasharray={`${(0.87 * 2 * Math.PI * 26).toString()} ${(2 * Math.PI * 26).toString()}`}
              />
              <defs>
                <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#6366f1" />
                  <stop offset="100%" stopColor="#22d3ee" />
                </linearGradient>
              </defs>
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="font-display text-sm font-bold text-white">87%</span>
            </div>
          </div>
        </div>

        {/* Macro bars */}
        <div className="space-y-3 mb-6">
          {[
            { name: 'Proteína', current: 145, target: 165, color: 'bg-emerald-500', pct: 88 },
            { name: 'Gordura', current: 58, target: 72, color: 'bg-yellow-500', pct: 80 },
            { name: 'Carboidrato', current: 180, target: 230, color: 'bg-blue-500', pct: 78 },
          ].map((macro) => (
            <div key={macro.name}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-[#a1a1aa]">{macro.name}</span>
                <span className="text-white font-medium">{macro.current}g <span className="text-[#a1a1aa]">/ {macro.target}g</span></span>
              </div>
              <div className="h-1.5 rounded-full bg-white/5">
                <div
                  className={`h-full rounded-full ${macro.color} opacity-80`}
                  style={{ width: `${macro.pct.toString()}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Mini weight trend chart */}
        <div className="rounded-xl bg-white/[0.03] border border-white/5 p-3">
          <p className="text-xs text-[#a1a1aa] mb-2">Tendência de peso</p>
          <svg width="100%" height="40" viewBox="0 0 200 40" preserveAspectRatio="none">
            <polyline
              points="0,32 30,28 60,30 90,22 120,18 150,14 180,10 200,8"
              stroke="url(#weightGrad)"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
              opacity="0.8"
            />
            <defs>
              <linearGradient id="weightGrad" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#6366f1" />
                <stop offset="100%" stopColor="#22d3ee" />
              </linearGradient>
            </defs>
          </svg>
        </div>
      </div>

      {/* Floating chat bubble */}
      <div className="absolute -bottom-6 -left-6 max-w-[200px] rounded-xl border border-white/10 bg-[rgba(18,18,20,0.98)] p-3 shadow-lg">
        <div className="flex items-center gap-2 mb-2">
          <img
            src="/assets/avatars/sofia.png"
            alt="Sofia"
            className="w-6 h-6 rounded-full object-cover"
            loading="lazy"
            width="24"
            height="24"
          />
          <span className="text-xs font-semibold text-white">Dra. Sofia</span>
        </div>
        <p className="text-xs text-[#a1a1aa] leading-relaxed">
          Seu TDEE adaptou bem essa semana! 🎯
        </p>
      </div>
    </div>
  );
};
