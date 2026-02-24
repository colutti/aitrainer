import { useEffect, useState } from 'react';

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

const SOFIA: TrainerInfo = {
  id: 'sofia',
  name: 'Dra. Sofia Pulse',
  avatar: '/assets/avatars/sofia.png',
  shortDescription: 'Saúde inteligente para mulheres modernas.',
  specialties: ['#saúdefeminina', '#hormônios', '#metabolismo'],
  catchphrase: 'Vamos hackear seu metabolismo com ciência e carinho.',
  accentColor: 'from-indigo-600 to-cyan-500',
};

const GYMBRO: TrainerInfo = {
  id: 'gymbro',
  name: "Breno 'The Bro' Silva",
  avatar: '/assets/avatars/gymbro.png',
  shortDescription: 'Seu parceiro de treino que sempre te bota pra cima!',
  specialties: ['#parceria', '#motivação', '#lifestyle'],
  catchphrase: 'Bora, monstro! Hoje é dia de EVOLUIR! 🔥',
  accentColor: 'from-cyan-500 to-indigo-600',
};

const CONVERSATIONS: Conversation[] = [
  {
    trainer: SOFIA,
    messages: [
      {
        role: 'user',
        text: 'Tenho 68kg, 32 anos, às vezes me sinto cansada apesar de dormir bem. Posso melhorar com nutrição?',
        delay: 500,
      },
      {
        role: 'trainer',
        text: 'Ótimo trazer isso! Cansaço crônico apesar do sono pode ter várias raízes — hormonal, nutricional, estilo de vida. Com 68kg, seu metabolismo base é um valor, mas como você come, quando treina, seu ciclo menstrual... tudo isso muda seu TDEE semanalmente. Primeira coisa que preciso entender: qual seu ciclo menstrual? Regular? Seu padrão de energia ao longo do mês é consistente ou muda muito?',
        delay: 4500,
      },
      {
        role: 'user',
        text: 'Meu ciclo é bem regular, me sinto mais cansada na primeira semana',
        delay: 8000,
      },
      {
        role: 'trainer',
        text: 'Perfeito! Essa queda de energia na primeira semana é textbook hormonal — estrogênio cai, ferro sai pelo sangramento. Tudo conectado. Aqui na plataforma, vamos registrar seu ciclo, seu sono, treino, alimentação. Com esses dados eu construo um TDEE adaptativo que entende suas flutuações reais. Ferro, magnésio, proteína — vão dançar junto com seus ciclos. Começa a fazer sentido agora?',
        delay: 12500,
      },
    ],
  },
  {
    trainer: GYMBRO,
    messages: [
      {
        role: 'user',
        text: 'Nunca malhei, tenho 82kg e quero ganhar músculo. Por onde começo?',
        delay: 500,
      },
      {
        role: 'trainer',
        text: 'Caramba! Bora sim monstro! 🔥 Primeira coisa: relaxa, você tá no lugar certo! Vamos começar coletando seus dados aqui pra eu montar algo estratégico pra você. Preciso saber: qual sua altura? Quanto você treina por semana no momento? E como tá sua alimentação — come bastante proteína ou come qualquer coisa mesmo?',
        delay: 4000,
      },
      {
        role: 'user',
        text: 'Tenho 1,78m, não treino nada no momento, e como bem desordenado',
        delay: 7500,
      },
      {
        role: 'trainer',
        text: 'Beleza! Com 82kg e 1,78m você tem potencial IMENSO pra ganhar massa! A nutrição desordenada? A gente vai arrumar isso junto. Mas antes de calcular seu plano exato, vamos registrar alguns dados seu aqui na plataforma — sua rotina atual, quantas horas você dorme, se tem alguma lesão. Só assim meu algoritmo vai entender SEU contexto real e criar um plano que funcione pra você de verdade. Vamo começar? Prometo que não é complicado!',
        delay: 10500,
      },
    ],
  },
];

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
  const [currentConvo, setCurrentConvo] = useState(0);
  const [visibleIndices, setVisibleIndices] = useState<Set<number>>(
    new Set()
  );

  const conversation: Conversation = CONVERSATIONS[currentConvo] ?? (CONVERSATIONS[0] as Conversation);

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
  }, [conversation]);

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
          <h2 className="text-4xl md:text-5xl font-bold text-white">
            Converse com Seu Treinador Agora
          </h2>
          <p className="text-lg text-zinc-400">
            Cada treinador tem personalidade, expertise e um jeito único de te guiar.
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
            Cada conversa mostra a IA se adaptando ao seu contexto. Seus dados alimentam inteligência cada vez melhor.
          </p>
        </div>
      </div>
    </section>
  );
};
