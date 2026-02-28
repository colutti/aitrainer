import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

interface ChatMessage {
  role: 'user' | 'trainer';
  text: string;
  delay?: number;
}

interface TrainerInfo {
  id: string;
  name: string;
  avatar: string;
  shortDescription: string;
  specialties: string[];
  catchphrase: string;
  accentColor: string;
}

interface Conversation {
  trainer: TrainerInfo;
  messages: ChatMessage[];
}

const TypingIndicator = () => (
  <div className="flex gap-1.5 items-center py-2">
    {[0, 150, 300].map((delay) => (
      <div
        key={delay}
        className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"
        style={{ animationDelay: `${delay.toString()}ms` }}
      />
    ))}
  </div>
);

const ChatMessage = ({
  message,
  isVisible,
}: {
  message: ChatMessage;
  isVisible: boolean;
}) => {
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} transition-all duration-500 ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
      }`}
    >
      <div
        className={`max-w-xl rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? 'bg-indigo-600 text-white'
            : 'bg-zinc-800 text-zinc-100'
        }`}
      >
        {message.text}
      </div>
    </div>
  );
};

const CarouselIndicator = ({
  total,
  current,
}: {
  total: number;
  current: number;
}) => (
  <div className="flex gap-2 justify-center mt-8">
    {Array.from({ length: total }).map((_, i) => (
      <div
        key={i}
        className={`h-2 rounded-full transition-all duration-500 ${
          i === current
            ? 'bg-indigo-500 w-8'
            : 'bg-zinc-700 w-2'
        }`}
      />
    ))}
  </div>
);

export const ChatCarousel = () => {
  const { t } = useTranslation();
  const [currentConvo, setCurrentConvo] = useState(0);
  const [visibleIndices, setVisibleIndices] = useState<Set<number>>(
    new Set()
  );

  const CONVERSATIONS: Conversation[] = useMemo(() => [
    {
      trainer: {
        id: 'sofia',
        name: 'Dra. Sofia Pulse',
        avatar: '/assets/avatars/sofia.png',
        shortDescription: t('landing.trainers.profiles.sofia.tagline'),
        specialties: t('landing.trainers.profiles.sofia.specialties', { returnObjects: true }) as string[],
        catchphrase: t('landing.trainers.profiles.sofia.catchphrase'),
        accentColor: 'from-indigo-600 to-cyan-500',
      },
      messages: [
        {
          role: 'user',
          text: t('landing.conversations.sofia.user_1'),
          delay: 800,
        },
        {
          role: 'trainer',
          text: t('landing.conversations.sofia.trainer_1'),
          delay: 6000,
        },
        {
          role: 'user',
          text: t('landing.conversations.sofia.user_2'),
          delay: 11000,
        },
        {
          role: 'trainer',
          text: t('landing.conversations.sofia.trainer_2'),
          delay: 16000,
        },
      ],
    },
    {
      trainer: {
        id: 'gymbro',
        name: "Breno 'The Bro' Silva",
        avatar: '/assets/avatars/gymbro.png',
        shortDescription: t('landing.trainers.profiles.gymbro.tagline'),
        specialties: t('landing.trainers.profiles.gymbro.specialties', { returnObjects: true }) as string[],
        catchphrase: t('landing.trainers.profiles.gymbro.catchphrase'),
        accentColor: 'from-cyan-500 to-indigo-600',
      },
      messages: [
        {
          role: 'user',
          text: t('landing.conversations.gymbro.user_1'),
          delay: 800,
        },
        {
          role: 'trainer',
          text: t('landing.conversations.gymbro.trainer_1'),
          delay: 6500,
        },
        {
          role: 'user',
          text: t('landing.conversations.gymbro.user_2'),
          delay: 12000,
        },
        {
          role: 'trainer',
          text: t('landing.conversations.gymbro.trainer_2'),
          delay: 18000,
        },
      ],
    },
  ], [t]);

  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const conversation = (CONVERSATIONS[currentConvo] ?? CONVERSATIONS[0])!;

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setVisibleIndices(new Set());
    const messages = conversation.messages;
    const timeouts: NodeJS.Timeout[] = [];

    messages.forEach((msg, idx) => {
      const delay = msg.delay ?? idx * 2500;
      const timeout = setTimeout(() => {
        setVisibleIndices((prev) => new Set([...prev, idx]));
      }, delay);
      timeouts.push(timeout);
    });

    const lastMessageTime =
      Math.max(...messages.map((m) => m.delay ?? 0)) + 4000;
    const rotateTimeout = setTimeout(() => {
      setCurrentConvo((prev) => (prev + 1) % CONVERSATIONS.length);
    }, lastMessageTime);

    return () => {
      timeouts.forEach((timeout) => {
        clearTimeout(timeout);
      });
      clearTimeout(rotateTimeout);
    };
  }, [conversation, CONVERSATIONS.length]);

  return (
    <section className="relative py-20 px-6 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-indigo-500/5 to-transparent pointer-events-none" />

      <div className="relative z-10 max-w-5xl mx-auto">
        {/* Logo + Heading */}
        <div className="text-center mb-12 space-y-4">
          <div className="flex justify-center items-center gap-3 mb-4">
            <img
              src="/logo_icon.png"
              alt="FityQ"
              className="h-10 w-10"
            />
            <span className="text-white font-bold text-lg">FityQ</span>
          </div>
          <h2 className="font-display text-4xl md:text-5xl font-bold text-white">
            {t('landing.chat_carousel.title')}
          </h2>
          <p className="text-lg text-zinc-400">
            {t('landing.chat_carousel.subtitle')}
          </p>
        </div>

        {/* Chat container */}
        <div className="bg-gradient-to-b from-zinc-900/50 to-zinc-950/50 backdrop-blur rounded-2xl border border-zinc-800 overflow-hidden">
          {/* Trainer header with avatar */}
          <div
            className={`bg-gradient-to-r ${conversation.trainer.accentColor} p-6 flex gap-4 items-start`}
          >
            <img
              src={conversation.trainer.avatar}
              alt={conversation.trainer.name}
              className="h-20 w-20 rounded-lg object-cover shadow-lg"
            />
            <div className="flex-1">
              <h3 className="font-bold text-white text-xl">
                {conversation.trainer.name}
              </h3>
              <p className="text-white/90 text-sm italic mb-2">
                "{conversation.trainer.catchphrase}"
              </p>
              <div className="flex gap-2 flex-wrap">
                {conversation.trainer.specialties.map((spec) => (
                  <span
                    key={spec}
                    className="text-xs bg-white/20 text-white px-2 py-1 rounded-full"
                  >
                    {spec}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="p-8 space-y-4 min-h-96 flex flex-col justify-center">
            {conversation.messages.map((msg, idx) => (
              <ChatMessage
                key={idx}
                message={msg}
                isVisible={visibleIndices.has(idx)}
              />
            ))}

            {visibleIndices.size < conversation.messages.length && (
              <div className="flex justify-start">
                <div className="bg-zinc-800 rounded-2xl px-4">
                  <TypingIndicator />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Carousel indicator */}
        <CarouselIndicator
          total={CONVERSATIONS.length}
          current={currentConvo}
        />

        {/* CTA hint */}
        <div className="text-center mt-12">
          <p className="text-sm text-zinc-500">
            {t('landing.chat_carousel.cta_hint')}
          </p>
        </div>
      </div>
    </section>
  );
};

