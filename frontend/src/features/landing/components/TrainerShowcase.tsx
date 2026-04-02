import { Button } from '@shared/components/ui/Button';
import { ChevronRight, MessageCircle } from 'lucide-react';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

export const TrainerShowcase = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const TRAINERS = [
    {
      id: 'atlas',
      name: 'Atlas Prime',
      avatar: '/assets/avatars/atlas.png',
      tagline: t('landing.trainers.profiles.atlas.tagline'),
      catchphrase: t('landing.trainers.profiles.atlas.catchphrase'),
      specialties: t('landing.trainers.profiles.atlas.specialties', { returnObjects: true }) as string[],
      style: t('landing.trainers.profiles.atlas.style'),
    },
    {
      id: 'luna',
      name: 'Luna Stardust',
      avatar: '/assets/avatars/luna.png',
      tagline: t('landing.trainers.profiles.luna.tagline'),
      catchphrase: t('landing.trainers.profiles.luna.catchphrase'),
      specialties: t('landing.trainers.profiles.luna.specialties', { returnObjects: true }) as string[],
      style: t('landing.trainers.profiles.luna.style'),
    },
    {
      id: 'sofia',
      name: 'Dra. Sofia Pulse',
      avatar: '/assets/avatars/sofia.png',
      tagline: t('landing.trainers.profiles.sofia.tagline'),
      catchphrase: t('landing.trainers.profiles.sofia.catchphrase'),
      specialties: t('landing.trainers.profiles.sofia.specialties', { returnObjects: true }) as string[],
      style: t('landing.trainers.profiles.sofia.style'),
    },
    {
      id: 'sargento',
      name: 'Major Steel',
      avatar: '/assets/avatars/sargento.png',
      tagline: t('landing.trainers.profiles.sargento.tagline'),
      catchphrase: t('landing.trainers.profiles.sargento.catchphrase'),
      specialties: t('landing.trainers.profiles.sargento.specialties', { returnObjects: true }) as string[],
      style: t('landing.trainers.profiles.sargento.style'),
    },
    {
      id: 'gymbro',
      name: "Breno 'The Bro' Silva",
      avatar: '/assets/avatars/gymbro.png',
      tagline: t('landing.trainers.profiles.gymbro.tagline'),
      catchphrase: t('landing.trainers.profiles.gymbro.catchphrase'),
      specialties: t('landing.trainers.profiles.gymbro.specialties', { returnObjects: true }) as string[],
      style: t('landing.trainers.profiles.gymbro.style'),
    },
  ];

  const selectedTrainer = TRAINERS.find((t) => t.id === selectedId) ?? null;

  return (
    <section id="treinadores" className="py-20 px-4 sm:px-6 lg:px-8 bg-dark-bg border-t border-border">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="font-display text-3xl font-bold text-text-primary mb-4">
            {t('landing.trainers.title')}
          </h2>
          <p className="text-lg text-text-secondary max-w-2xl mx-auto">
            {t('landing.trainers.description')}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">
          {TRAINERS.map((trainer) => (
            <Button
              key={trainer.id}
              type="button"
              variant="ghost"
              onClick={() => { setSelectedId(selectedId === trainer.id ? null : trainer.id); }}
              className={`h-auto min-h-44 w-full items-start flex-col p-6 rounded-lg border transition-all text-left ${
                selectedId === trainer.id
                  ? 'bg-secondary border-primary'
                  : 'bg-dark-bg border-border hover:border-text-muted'
              }`}
            >
              <img
                src={trainer.avatar}
                alt={trainer.name}
                className="w-16 h-16 rounded mb-4 object-cover border border-border"
              />
              <h3 className="font-bold text-text-primary mb-1">
                {trainer.name}
              </h3>
              <p className="text-xs text-text-secondary line-clamp-2">
                {trainer.tagline}
              </p>
            </Button>
          ))}
        </div>

        {selectedTrainer && (
          <div className="mt-8 p-6 sm:p-10 rounded-2xl border border-border bg-light-bg/95 shadow-[0_18px_45px_rgba(0,0,0,0.25)] flex flex-col items-center text-center gap-6 animate-fade-in">
            <img
              src={selectedTrainer.avatar}
              alt={selectedTrainer.name}
              className="w-28 h-28 sm:w-32 sm:h-32 rounded-xl object-cover border-2 border-primary/40 shadow-[0_10px_28px_rgba(20,184,166,0.2)] shrink-0"
            />

            <div>
              <h3 className="text-2xl sm:text-3xl font-bold text-text-primary">
                {selectedTrainer.name}
              </h3>
              <p className="mt-2 text-sm sm:text-base text-primary font-semibold tracking-wide">
                {selectedTrainer.style}
              </p>
            </div>

            <p className="max-w-2xl text-base sm:text-lg italic text-text-secondary leading-relaxed">
              "{selectedTrainer.catchphrase}"
            </p>

            <div className="flex flex-wrap justify-center gap-2 sm:gap-3">
              {selectedTrainer.specialties.map((spec) => (
                <span
                  key={spec}
                  className="px-3 py-1 rounded-full bg-secondary border border-border text-xs sm:text-sm text-text-secondary"
                >
                  {spec}
                </span>
              ))}
            </div>

            <Button
              onClick={() => { void navigate('/login'); }}
              variant="primary"
              size="sm"
              className="rounded-md w-full sm:w-auto"
            >
              <MessageCircle size={16} className="mr-2" />
              {t('landing.trainers.talk_with', { name: selectedTrainer.name.split(' ')[0] })}
            </Button>
          </div>
        )}

        <div className="mt-16 text-center">
          <Button
            onClick={() => { void navigate('/login'); }}
            variant="secondary"
            className="border-border bg-dark-card rounded-md inline-flex items-center gap-2"
          >
            {t('landing.cta_trainers')}
            <ChevronRight size={16} />
          </Button>
        </div>
      </div>
    </section>
  );
};
