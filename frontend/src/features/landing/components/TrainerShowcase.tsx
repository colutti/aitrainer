import { Button } from '@shared/components/ui/Button';
import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';

interface TrainerCard {
  id: string;
  name: string;
  avatar: string;
  forWho: string;
  style: string;
  bestFor: string;
  example: string;
}

export const TrainerShowcase = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [selectedId, setSelectedId] = useState<string>('gymbro');

  const trainers: TrainerCard[] = [
    {
      id: 'atlas',
      name: 'Atlas Prime',
      avatar: '/assets/avatars/atlas.png',
      forWho: t('landing.trainers.profiles.atlas.for_who'),
      style: t('landing.trainers.profiles.atlas.style'),
      bestFor: t('landing.trainers.profiles.atlas.best_for'),
      example: t('landing.trainers.profiles.atlas.example'),
    },
    {
      id: 'luna',
      name: 'Luna Stardust',
      avatar: '/assets/avatars/luna.png',
      forWho: t('landing.trainers.profiles.luna.for_who'),
      style: t('landing.trainers.profiles.luna.style'),
      bestFor: t('landing.trainers.profiles.luna.best_for'),
      example: t('landing.trainers.profiles.luna.example'),
    },
    {
      id: 'sofia',
      name: 'Dra. Sofia Pulse',
      avatar: '/assets/avatars/sofia.png',
      forWho: t('landing.trainers.profiles.sofia.for_who'),
      style: t('landing.trainers.profiles.sofia.style'),
      bestFor: t('landing.trainers.profiles.sofia.best_for'),
      example: t('landing.trainers.profiles.sofia.example'),
    },
    {
      id: 'sargento',
      name: 'Major Steel',
      avatar: '/assets/avatars/sargento.png',
      forWho: t('landing.trainers.profiles.sargento.for_who'),
      style: t('landing.trainers.profiles.sargento.style'),
      bestFor: t('landing.trainers.profiles.sargento.best_for'),
      example: t('landing.trainers.profiles.sargento.example'),
    },
    {
      id: 'gymbro',
      name: "Breno 'The Bro' Silva",
      avatar: '/assets/avatars/gymbro.png',
      forWho: t('landing.trainers.profiles.gymbro.for_who'),
      style: t('landing.trainers.profiles.gymbro.style'),
      bestFor: t('landing.trainers.profiles.gymbro.best_for'),
      example: t('landing.trainers.profiles.gymbro.example'),
    },
  ];

  const selectedTrainer = trainers.find((trainer) => trainer.id === selectedId) ?? trainers[0];

  if (!selectedTrainer) {
    return null;
  }

  return (
    <section id="treinadores" className="py-20 px-4 sm:px-6 lg:px-8 bg-dark-bg border-t border-border">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="font-display text-3xl font-bold text-text-primary mb-4">
            {t('landing.trainers.title')}
          </h2>
          <p className="text-lg text-text-secondary max-w-3xl mx-auto">
            {t('landing.trainers.description')}
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">
          {trainers.map((trainer) => (
            <Button
              key={trainer.id}
              type="button"
              variant="ghost"
              onClick={() => { setSelectedId(trainer.id); }}
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
              <h3 className="font-bold text-text-primary mb-1">{trainer.name}</h3>
              <p className="text-xs text-text-secondary line-clamp-3">{trainer.forWho}</p>
            </Button>
          ))}
        </div>

        <div className="mt-8 p-6 sm:p-8 rounded-2xl border border-border bg-light-bg/95 shadow-[0_18px_45px_rgba(0,0,0,0.25)]">
          <div className="flex flex-col sm:flex-row gap-6">
            <img
              src={selectedTrainer.avatar}
              alt={selectedTrainer.name}
              className="w-24 h-24 rounded-xl object-cover border-2 border-primary/40 shrink-0"
            />
            <div className="flex-1">
              <h3 className="text-2xl font-bold text-text-primary">{selectedTrainer.name}</h3>
              <p className="mt-2 text-sm text-primary font-semibold">{selectedTrainer.style}</p>
              <p className="mt-4 text-sm text-text-secondary">{selectedTrainer.forWho}</p>
              <p className="mt-3 text-sm text-text-secondary">{selectedTrainer.bestFor}</p>
              <p className="mt-4 text-base italic text-text-secondary">"{selectedTrainer.example}"</p>
              <Button
                onClick={() => { void navigate('/login?mode=register'); }}
                variant="primary"
                size="sm"
                className="rounded-md mt-6"
              >
                {t('landing.trainers.cta')}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
