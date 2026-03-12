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
            <button
              key={trainer.id}
              onClick={() => { setSelectedId(selectedId === trainer.id ? null : trainer.id); }}
              className={`flex flex-col p-6 rounded-lg border transition-all text-left ${
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
            </button>
          ))}
        </div>

        {selectedTrainer && (
          <div className="mt-8 p-8 rounded-lg border border-border bg-light-bg flex flex-col md:flex-row gap-8 items-start animate-fade-in">
            <img
              src={selectedTrainer.avatar}
              alt={selectedTrainer.name}
              className="w-24 h-24 rounded object-cover border border-border"
            />
            <div className="flex-1">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
                <div>
                  <h3 className="text-2xl font-bold text-text-primary">
                    {selectedTrainer.name}
                  </h3>
                  <p className="text-sm text-primary font-medium">
                    {selectedTrainer.style}
                  </p>
                </div>
                <Button
                  onClick={() => { void navigate('/login'); }}
                  variant="primary"
                  size="sm"
                  className="rounded-md"
                >
                  <MessageCircle size={16} className="mr-2" />
                  {t('landing.trainers.talk_with', { name: selectedTrainer.name.split(' ')[0] })}
                </Button>
              </div>
              
              <p className="text-lg italic text-text-secondary mb-6 leading-relaxed">
                "{selectedTrainer.catchphrase}"
              </p>
              
              <div className="flex flex-wrap gap-2">
                {selectedTrainer.specialties.map((spec) => (
                  <span
                    key={spec}
                    className="px-2.5 py-1 rounded bg-secondary border border-border text-xs text-text-secondary"
                  >
                    {spec}
                  </span>
                ))}
              </div>
            </div>
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
