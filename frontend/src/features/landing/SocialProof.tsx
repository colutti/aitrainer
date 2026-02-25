/**
 * SocialProof
 * Stats bar with trust indicators for the landing page.
 * TODO: Replace placeholder metrics with real analytics data.
 */
export const SocialProof = (): React.ReactNode => {
  const stats = [
    /* TODO: Replace with real metrics */
    { value: '500+', label: 'Usuários ativos' },
    { value: '50k+', label: 'Mensagens trocadas' },
    { value: '5', label: 'Treinadores únicos' },
    { value: '24/7', label: 'Sempre disponível' },
  ];

  return (
    <section className="py-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-5xl mx-auto">
        <div className="rounded-2xl border border-white/8 bg-[rgba(18,18,20,0.6)] backdrop-blur-sm px-8 py-10">
          <p className="text-center text-sm text-[#a1a1aa] mb-8 font-medium tracking-wide uppercase">
            Centenas de pessoas já confiam no FityQ
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, i) => (
              <div key={i} className="text-center">
                <p className="font-display text-3xl sm:text-4xl font-extrabold bg-gradient-to-r from-[#6366f1] to-[#22d3ee] bg-clip-text text-transparent mb-1">
                  {stat.value}
                </p>
                <p className="text-sm text-[#a1a1aa]">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
