import { useEffect, useRef, useState } from 'react';

// Type definitions
interface ChatMessage {
  role: 'user' | 'trainer';
  text: string;
  isTyping?: boolean;
}

interface ChatWindowProps {
  trainerName: string;
  trainerColor: string;
  messages: ChatMessage[];
}

// Typing indicator animation
const TypingIndicator = () => (
  <div className="flex gap-1.5 items-center py-2">
    <div
      className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"
      style={{ animationDelay: '0ms' }}
    />
    <div
      className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"
      style={{ animationDelay: '150ms' }}
    />
    <div
      className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce"
      style={{ animationDelay: '300ms' }}
    />
  </div>
);

// Chat bubble component
const ChatBubble = ({
  message,
  isUser,
}: {
  message: ChatMessage;
  isUser: boolean;
}) => {
  if (message.isTyping) {
    return (
      <div
        className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}
      >
        <div className="bg-zinc-800 rounded-2xl px-3 py-2 max-w-xs">
          <TypingIndicator />
        </div>
      </div>
    );
  }

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-fade-in`}
    >
      <div
        className={`rounded-2xl px-4 py-3 max-w-xs text-sm leading-relaxed ${
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

// iPhone frame with chat
const ChatWindow = ({
  trainerName,
  trainerColor,
  messages,
}: ChatWindowProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex flex-col items-center w-full max-w-sm mx-auto">
      {/* iPhone Frame */}
      <div className="relative w-full aspect-[9/19.5] rounded-[40px] border-8 border-black bg-black shadow-2xl overflow-hidden">
        {/* Notch */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-40 h-7 bg-black rounded-b-3xl z-20 flex items-center justify-center gap-1">
          <div className="w-1.5 h-1.5 bg-zinc-600 rounded-full" />
          <div className="w-1.5 h-1.5 bg-zinc-600 rounded-full" />
        </div>

        {/* Status bar */}
        <div className="bg-zinc-950 px-6 pt-3 pb-2 flex justify-between items-center text-xs text-white font-semibold">
          <span>9:41</span>
          <div className="flex gap-1">
            <div className="w-4 h-3 border border-white rounded-sm" />
            <div className="w-1 h-3 bg-white rounded-r" />
          </div>
        </div>

        {/* Chat header */}
        <div className={`bg-gradient-to-r ${trainerColor} px-4 py-3`}>
          <p className="font-semibold text-white text-sm">{trainerName}</p>
          <p className="text-xs text-white/70">Online</p>
        </div>

        {/* Messages area */}
        <div
          ref={scrollRef}
          className="flex-1 overflow-y-auto bg-zinc-950 px-4 py-4 space-y-4 h-96 flex flex-col"
        >
          {messages.map((msg, idx) => (
            <ChatBubble
              key={idx}
              message={msg}
              isUser={msg.role === 'user'}
            />
          ))}
        </div>

        {/* Input area */}
        <div className="bg-zinc-900 px-4 py-3 border-t border-zinc-800 flex gap-2">
          <input
            type="text"
            placeholder="Mensagem..."
            className="flex-1 bg-zinc-800 rounded-full px-4 py-2 text-xs text-white placeholder-zinc-500 outline-none"
            disabled
          />
          <button className="text-indigo-500 font-bold text-lg">⬆</button>
        </div>
      </div>
    </div>
  );
};

// Main showcase component
export const ChatShowcase = () => {
  const [lunaMessages, setLunaMessages] = useState<ChatMessage[]>([
    {
      role: 'user',
      text: 'Tenho 70kg, quero ganhar massa com deficit calórico. Como funciona?',
    },
    { role: 'trainer', text: '', isTyping: true },
  ]);

  const [atlasMessages, setAtlasMessages] = useState<ChatMessage[]>([
    { role: 'user', text: 'Sou iniciante. Como estruturo minha primeira semana?' },
    { role: 'trainer', text: '', isTyping: true },
  ]);

  // Simulate trainer responses after a delay
  useEffect(() => {
    const lunaTimer = setTimeout(() => {
      setLunaMessages([
        {
          role: 'user',
          text: 'Tenho 70kg, quero ganhar massa com deficit calórico. Como funciona?',
        },
        {
          role: 'trainer',
          text: 'Excelente meta! Com 70kg, seu TDEE é ~1950 kcal. Para ganho de massa em deficit: 1700 kcal/dia. Proteína: 140g, Carbos: 180g, Gordura: 56g. Isso mantém o músculo enquanto reduz gordura. Você já faz musculação?',
        },
      ]);
    }, 2500);

    return () => {
      clearTimeout(lunaTimer);
    };
  }, []);

  useEffect(() => {
    const atlasTimer = setTimeout(() => {
      setAtlasMessages([
        {
          role: 'user',
          text: 'Sou iniciante. Como estruturo minha primeira semana?',
        },
        {
          role: 'trainer',
          text: 'Pega firme! Recomendo 3x/semana: Seg (Peito+Tríceps), Qua (Costas+Bíceps), Sex (Perna+Ombro). 4-5 exercícios por grupo, 3×8-10 reps, repouso 60-90s. Comece leve, foco em técnica. Qual seu objetivo?',
        },
      ]);
    }, 2500);

    return () => {
      clearTimeout(atlasTimer);
    };
  }, []);

  return (
    <section className="relative py-20 px-6 overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-indigo-500/5 to-transparent pointer-events-none" />

      <div className="relative z-10 max-w-7xl mx-auto">
        {/* Section heading */}
        <div className="text-center mb-16 space-y-4">
          <h2 className="text-4xl md:text-5xl font-bold text-white">
            Converse com Seu Treinador Agora
          </h2>
          <p className="text-lg text-zinc-300 max-w-2xl mx-auto">
            Veja como Luna cuida da sua nutrição e Atlas estrutura seu treino.
            Tudo personalizados ao seu contexto.
          </p>
        </div>

        {/* Chat windows grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
          {/* Luna chat */}
          <div className="flex flex-col items-center gap-4">
            <ChatWindow
              trainerName="Luna"
              trainerColor="from-cyan-600 to-blue-600"
              messages={lunaMessages}
            />
            <div className="text-center space-y-2">
              <h3 className="font-semibold text-white text-lg">Luna</h3>
              <p className="text-sm text-zinc-400">
                Especialista em nutrição & TDEE adaptativo
              </p>
            </div>
          </div>

          {/* Atlas chat */}
          <div className="flex flex-col items-center gap-4">
            <ChatWindow
              trainerName="Atlas"
              trainerColor="from-indigo-600 to-purple-600"
              messages={atlasMessages}
            />
            <div className="text-center space-y-2">
              <h3 className="font-semibold text-white text-lg">Atlas</h3>
              <p className="text-sm text-zinc-400">
                Especialista em treino e força
              </p>
            </div>
          </div>
        </div>

        {/* CTA hint */}
        <div className="text-center mt-12">
          <p className="text-sm text-zinc-400">
            Escolha entre 5 treinadores. Cada um com uma personalidade única.
            Todos disponíveis 24/7.
          </p>
        </div>
      </div>
    </section>
  );
};
