import { useEffect, useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';

interface ChatMessageData {
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
}

interface Conversation {
  trainer: TrainerInfo;
  messages: ChatMessageData[];
}

const TypingIndicator = () => (
  <div className="flex gap-1 items-center py-2 px-1">
    {[0, 150, 300].map((delay) => (
      <div
        key={delay}
        className="w-1.5 h-1.5 bg-text-muted/50 rounded-full animate-bounce"
        style={{ animationDelay: `${delay.toString()}ms` }}
      />
    ))}
  </div>
);

const ChatMessage = ({
  message,
  isVisible,
}: {
  message: ChatMessageData;
  isVisible: boolean;
}) => {
  const isUser = message.role === 'user';

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} transition-all duration-300 ${
        isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-2'
      }`}
    >
      <div
        className={`max-w-[85%] sm:max-w-lg rounded-lg px-4 py-2.5 text-sm leading-relaxed ${
          isUser
            ? 'bg-primary text-white'
            : 'bg-secondary border border-border text-text-primary'
        }`}
      >
        {message.text}
      </div>
    </div>
  );
};

export const ChatCarousel = () => {
  const { t } = useTranslation();
  const [currentConvo, setCurrentConvo] = useState(0);
  const [visibleIndices, setVisibleIndices] = useState<Set<number>>(new Set());

  const CONVERSATIONS: Conversation[] = useMemo(() => [
    {
      trainer: {
        id: 'sofia',
        name: 'Dra. Sofia Pulse',
        avatar: '/assets/avatars/sofia.png',
        shortDescription: t('landing.trainers.profiles.sofia.tagline'),
        specialties: t('landing.trainers.profiles.sofia.specialties', { returnObjects: true }) as string[],
        catchphrase: t('landing.trainers.profiles.sofia.catchphrase'),
      },
      messages: [
        { role: 'user', text: t('landing.conversations.sofia.user_1'), delay: 800 },
        { role: 'trainer', text: t('landing.conversations.sofia.trainer_1'), delay: 5000 },
        { role: 'user', text: t('landing.conversations.sofia.user_2'), delay: 10000 },
        { role: 'trainer', text: t('landing.conversations.sofia.trainer_2'), delay: 14000 },
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
      },
      messages: [
        { role: 'user', text: t('landing.conversations.gymbro.user_1'), delay: 800 },
        { role: 'trainer', text: t('landing.conversations.gymbro.trainer_1'), delay: 5000 },
        { role: 'user', text: t('landing.conversations.gymbro.user_2'), delay: 10000 },
        { role: 'trainer', text: t('landing.conversations.gymbro.trainer_2'), delay: 14000 },
      ],
    },
  ], [t]);

  // Guaranteed at least one conversation exists
  const conversation = CONVERSATIONS[currentConvo] ?? CONVERSATIONS[0];

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setVisibleIndices(new Set());
    const messages = conversation ? conversation.messages : [];
    const timeouts: NodeJS.Timeout[] = [];

    messages.forEach((msg, idx) => {
      const delay = msg.delay ?? idx * 2500;
      const timeout = setTimeout(() => {
        setVisibleIndices((prev) => new Set([...prev, idx]));
      }, delay);
      timeouts.push(timeout);
    });

    const lastMessageTime = Math.max(...messages.map((m) => m.delay ?? 0)) + 4000;
    const rotateTimeout = setTimeout(() => {
      setCurrentConvo((prev) => (prev + 1) % CONVERSATIONS.length);
    }, lastMessageTime);

    return () => {
      timeouts.forEach(clearTimeout);
      clearTimeout(rotateTimeout);
    };
  }, [conversation, CONVERSATIONS.length]);

  if (!conversation) return null;

  return (
    <section className="py-20 px-4 sm:px-6 lg:px-8 border-t border-border">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-12">
          <h2 className="font-display text-3xl font-bold text-text-primary mb-4">
            {t('landing.chat_carousel.title')}
          </h2>
          <p className="text-lg text-text-secondary">
            {t('landing.chat_carousel.subtitle')}
          </p>
        </div>

        <div className="rounded-lg border border-border bg-dark-bg overflow-hidden shadow-sm">
          {/* Trainer Info Header */}
          <div className="p-6 border-b border-border bg-light-bg flex items-center gap-4">
            <img
              src={conversation.trainer.avatar}
              alt={conversation.trainer.name}
              className="w-12 h-12 rounded-md object-cover border border-border"
            />
            <div>
              <h3 className="font-bold text-text-primary text-base">
                {conversation.trainer.name}
              </h3>
              <p className="text-xs text-text-muted italic">
                {conversation.trainer.catchphrase}
              </p>
            </div>
          </div>

          {/* Chat Window */}
          <div className="p-6 h-[450px] flex flex-col justify-end gap-4 bg-dark-bg/50">
            {conversation.messages.map((msg, idx) => (
              <ChatMessage
                key={`${currentConvo.toString()}-${idx.toString()}`}
                message={msg}
                isVisible={visibleIndices.has(idx)}
              />
            ))}

            {visibleIndices.size < conversation.messages.length && (
              <div className="flex justify-start">
                <div className="bg-secondary rounded-lg border border-border">
                  <TypingIndicator />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Indicators */}
        <div className="flex justify-center gap-2 mt-8">
          {CONVERSATIONS.map((_, i) => (
            <button
              key={i.toString()}
              onClick={() => { setCurrentConvo(i); }}
              className={`h-1.5 rounded-full transition-all ${
                i === currentConvo ? 'bg-primary w-6' : 'bg-border w-1.5'
              }`}
            />
          ))}
        </div>
      </div>
    </section>
  );
};
