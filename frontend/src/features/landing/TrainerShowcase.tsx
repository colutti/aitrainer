import { Button } from '@shared/components/ui/Button';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface TrainerData {
  id: string;
  name: string;
  avatar: string;
  tagline: string;
  catchphrase: string;
  specialties: string[];
  style: string;
  gradient: string;
  borderHover: string;
}

const TRAINERS: TrainerData[] = [
  {
    id: 'atlas',
    name: 'Atlas Prime',
    avatar: '/assets/avatars/atlas.png',
    tagline: 'A eficiência é a única métrica que importa.',
    catchphrase: 'Seus músculos são máquinas biológicas. Vamos otimizá-las.',
    specialties: ['#biomecânica', '#dados', '#hipertrofia'],
    style: 'Científico & Precisionista',
    gradient: 'from-sky-600 to-slate-700',
    borderHover: 'hover:border-sky-500/60',
  },
  {
    id: 'luna',
    name: 'Luna Stardust',
    avatar: '/assets/avatars/luna.png',
    tagline: 'Seu corpo é um templo estelar.',
    catchphrase: 'Respire o universo, expire as tensões.',
    specialties: ['#yoga', '#mindfulness', '#fluxo'],
    style: 'Holística & Telúrica',
    gradient: 'from-indigo-500 to-purple-600',
    borderHover: 'hover:border-indigo-400/60',
  },
  {
    id: 'sofia',
    name: 'Dra. Sofia Pulse',
    avatar: '/assets/avatars/sofia.png',
    tagline: 'Saúde inteligente para mulheres modernas.',
    catchphrase: 'Vamos hackear seu metabolismo com ciência e carinho.',
    specialties: ['#saúdefeminina', '#hormônios', '#metabolismo'],
    style: 'Especialista Empática',
    gradient: 'from-blue-500 to-cyan-600',
    borderHover: 'hover:border-blue-400/60',
  },
  {
    id: 'sargento',
    name: 'Major Steel',
    avatar: '/assets/avatars/sargento.png',
    tagline: 'A dor é a fraqueza saindo do corpo!',
    catchphrase: 'Sem desculpas, recruta. VAMOS EMBORA!',
    specialties: ['#disciplina', '#força', '#semdesculpas'],
    style: 'Bootcamp Militar',
    gradient: 'from-emerald-600 to-teal-800',
    borderHover: 'hover:border-emerald-500/60',
  },
  {
    id: 'gymbro',
    name: "Breno 'The Bro' Silva",
    avatar: '/assets/avatars/gymbro.png',
    tagline: 'Seu parceiro de treino que sempre te bota pra cima!',
    catchphrase: 'Bora, monstro! Hoje é dia de EVOLUIR! 🔥',
    specialties: ['#parceria', '#motivação', '#lifestyle'],
    style: 'Parceiro do Ginásio',
    gradient: 'from-violet-600 to-purple-800',
    borderHover: 'hover:border-violet-500/60',
  },
];

export const TrainerShowcase = (): React.ReactNode => {
  const navigate = useNavigate();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const selectedTrainer = TRAINERS.find((t) => t.id === selectedId) ?? null;

  return (
    <section id="treinadores" className="py-24 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="font-display text-4xl sm:text-5xl font-bold text-white mb-4">
            Conheça Seus Treinadores
          </h2>
          <p className="text-lg text-[#a1a1aa] max-w-2xl mx-auto">
            5 personalidades únicas, cada uma com estilo, expertise e abordagem própria. Escolha quem combina com você.
          </p>
        </div>

        {/* Desktop grid + Mobile scroll */}
        <div className="flex overflow-x-auto snap-x snap-mandatory gap-4 pb-4 md:grid md:grid-cols-3 md:overflow-visible lg:grid-cols-5 -mx-4 px-4 md:mx-0 md:px-0">
          {TRAINERS.map((trainer) => {
            const isSelected = selectedId === trainer.id;
            return (
              <button
                key={trainer.id}
                onClick={() => { setSelectedId(isSelected ? null : trainer.id); }}
                className={`group relative snap-center min-w-[240px] md:min-w-0 flex-shrink-0 text-left p-5 rounded-2xl border transition-all duration-300 cursor-pointer ${
                  isSelected
                    ? `border-transparent bg-gradient-to-br ${trainer.gradient} opacity-100 scale-[1.02]`
                    : `border-white/10 bg-[rgba(18,18,20,0.8)] ${trainer.borderHover} hover:scale-[1.03]`
                }`}
              >
                {/* Avatar with gradient border */}
                <div
                  className={`w-16 h-16 rounded-xl mb-3 p-0.5 bg-gradient-to-br ${trainer.gradient}`}
                >
                  <img
                    src={trainer.avatar}
                    alt={trainer.name}
                    className="w-full h-full rounded-[10px] object-cover"
                    loading="lazy"
                    width="64"
                    height="64"
                  />
                </div>

                <h3 className="font-display font-bold text-white text-base mb-1 leading-tight">
                  {trainer.name}
                </h3>
                <p className={`text-xs mb-3 leading-snug ${isSelected ? 'text-white/80' : 'text-[#a1a1aa]'}`}>
                  {trainer.tagline}
                </p>

                {/* Specialties */}
                <div className="flex flex-wrap gap-1 mb-3">
                  {trainer.specialties.map((spec) => (
                    <span
                      key={spec}
                      className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
                        isSelected
                          ? 'bg-white/20 text-white'
                          : 'bg-white/5 text-[#a1a1aa]'
                      }`}
                    >
                      {spec}
                    </span>
                  ))}
                </div>

                {/* Catchphrase — visible on hover */}
                <p
                  className={`text-xs italic leading-snug transition-all duration-300 ${
                    isSelected
                      ? 'text-white/90 opacity-100'
                      : 'text-[#a1a1aa] opacity-0 group-hover:opacity-100'
                  }`}
                >
                  "{trainer.catchphrase}"
                </p>
              </button>
            );
          })}
        </div>

        {/* Mobile scroll hint */}
        <p className="text-center text-xs text-[#a1a1aa] mt-2 md:hidden">
          Deslize para ver mais treinadores →
        </p>

        {/* Expanded detail panel */}
        {selectedTrainer !== null && (
          <div className="mt-6 rounded-2xl border border-white/10 bg-[rgba(18,18,20,0.9)] p-6 sm:p-8 transition-all duration-500">
            <div className="flex flex-col sm:flex-row gap-6 items-start">
              <div
                className={`shrink-0 w-20 h-20 rounded-xl p-0.5 bg-gradient-to-br ${selectedTrainer.gradient}`}
              >
                <img
                  src={selectedTrainer.avatar}
                  alt={selectedTrainer.name}
                  className="w-full h-full rounded-[10px] object-cover"
                  width="80"
                  height="80"
                />
              </div>
              <div className="flex-1">
                <div className="flex items-start justify-between gap-4 flex-wrap">
                  <div>
                    <h3 className="font-display text-2xl font-bold text-white mb-1">
                      {selectedTrainer.name}
                    </h3>
                    <p className="text-sm text-[#a1a1aa] mb-1">
                      {selectedTrainer.style}
                    </p>
                    <p className="text-base italic text-[#fafafa]/80 mb-4">
                      "{selectedTrainer.catchphrase}"
                    </p>
                  </div>
                  <Button
                    onClick={() => { void navigate('/login'); }}
                    variant="primary"
                    size="sm"
                  >
                    Conversar com {selectedTrainer.name.split(' ')[0]}
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {selectedTrainer.specialties.map((spec) => (
                    <span
                      key={spec}
                      className="text-xs bg-white/10 text-[#fafafa]/80 px-2.5 py-1 rounded-full"
                    >
                      {spec}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};
