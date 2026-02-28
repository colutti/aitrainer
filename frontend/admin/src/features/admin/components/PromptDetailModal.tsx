import { Copy, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

import { Button } from '../../../../../src/shared/components/ui/Button';
import { useNotificationStore } from '../../../../../src/shared/hooks/useNotification';
import type { PromptLog } from '../../../../../src/shared/types/admin';

interface PromptDetailModalProps {
  selectedPrompt: PromptLog | null;
  onClose: () => void;
}

interface XmlSection {
  tag: string;
  content: string;
}

interface MsgMetadata {
  data?: string;
  hora?: string;
}

// Parse XML tags from prompt string
function parsePromptSections(prompt: string): XmlSection[] {
  const sections: XmlSection[] = [];
  const regex = /<(\w+)>([\s\S]*?)<\/\1>/g;
  let match;
  while ((match = regex.exec(prompt)) !== null) {
    const tag = match[1] ?? '';
    const content = (match[2] ?? '').trim();
    if (tag) sections.push({ tag, content });
  }
  return sections;
}

// Extract <msg> tag metadata from message content
function parseMsgAttributes(content: string): { attributes: MsgMetadata; text: string } {
  const msgRegex = /<msg(?:\s+data="([^"]*)")?(?:\s+hora="([^"]*)")?>(.*?)<\/msg>/;
  const match = msgRegex.exec(content);
  if (match) {
    return {
      attributes: { data: match[1], hora: match[2] },
      text: match[3] ?? '',
    };
  }
  return { attributes: {}, text: content };
}

// Color mapping for XML tag sections
const TAG_COLORS: Record<string, { bg: string; text: string; emoji: string }> = {
  identidade: { bg: 'bg-purple-500/10', text: 'text-purple-400', emoji: '🟣' },
  escopo: { bg: 'bg-blue-500/10', text: 'text-blue-400', emoji: '🔵' },
  formato: { bg: 'bg-cyan-500/10', text: 'text-cyan-400', emoji: '🔷' },
  contexto: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', emoji: '🟡' },
  aluno: { bg: 'bg-green-500/10', text: 'text-green-400', emoji: '🟢' },
  historico: { bg: 'bg-orange-500/10', text: 'text-orange-400', emoji: '🟠' },
};

export function PromptDetailModal({ selectedPrompt, onClose }: PromptDetailModalProps) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    system: true,
    history: false,
    tools: false,
    identidade: true,
    escopo: true,
    formato: true,
    contexto: true,
    aluno: true,
    historico: false,
  });
  const notify = useNotificationStore();

  if (!selectedPrompt) return null;

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      notify.success('Copiado para a área de transferência!');
    } catch {
      notify.error('Erro ao copiar.');
    }
  };

  const hasMessages = !!(selectedPrompt.prompt?.messages && selectedPrompt.prompt.messages.length > 0);
  const hasTools = !!(selectedPrompt.prompt?.tools && selectedPrompt.prompt.tools.length > 0);
  const promptStr = selectedPrompt.prompt?.prompt ?? '';
  const durationSec = (selectedPrompt.duration_ms / 1000).toFixed(2);

  // Parse XML sections from prompt
  const xmlSections = parsePromptSections(promptStr);
  const hasXmlSections = xmlSections.length > 0;

  return (
    <div
      className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-[100] p-4 animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="bg-dark-card border border-border p-6 rounded-xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl"
        onClick={(e) => { e.stopPropagation(); }}
      >
        {/* Header */}
        <div className="flex justify-between items-center mb-4 shrink-0">
          <div>
            <h2 className="text-2xl font-bold text-text-primary">Detalhes do Prompt</h2>
            <div className="flex gap-4 mt-2 text-xs text-text-secondary flex-wrap">
              <span className="px-2 py-1 bg-blue-500/10 text-blue-400 rounded font-mono">
                {selectedPrompt.model}
              </span>
              <span className="px-2 py-1 bg-green-500/10 text-green-400 rounded">
                {selectedPrompt.tokens_input} → {selectedPrompt.tokens_output} tokens
              </span>
              <span className="px-2 py-1 bg-purple-500/10 text-purple-400 rounded">
                {durationSec}s
              </span>
              <span
                className={`px-2 py-1 rounded ${
                  selectedPrompt.status === 'success'
                    ? 'bg-green-500/10 text-green-400'
                    : 'bg-red-500/10 text-red-400'
                }`}
              >
                {selectedPrompt.status === 'success' ? '✓ Success' : '✗ Error'}
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              className="gap-2"
              onClick={() => { void copyToClipboard(JSON.stringify(selectedPrompt, null, 2)); }}
            >
              <Copy size={16} /> JSON
            </Button>
            <Button variant="ghost" size="sm" onClick={onClose}>
              Fechar
            </Button>
          </div>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto space-y-3 min-h-0">
          {/* Prompt / System Section */}
          {hasXmlSections ? (
            // Render individual XML sections with colors
            <>
              {xmlSections.map((section) => {
                const colors = TAG_COLORS[section.tag] ?? {
                  bg: 'bg-gray-500/10',
                  text: 'text-gray-400',
                  emoji: '⚪',
                };
                const isExpanded = expandedSections[section.tag] ?? true;

                return (
                  <div key={section.tag} className={`${colors.bg} rounded-lg border border-white/5 overflow-hidden`}>
                    <button
                      onClick={() => { toggleSection(section.tag); }}
                      className="w-full flex items-center justify-between p-3 hover:bg-white/5 transition-colors"
                    >
                      <h3 className={`font-semibold ${colors.text} text-sm`}>
                        {colors.emoji} {section.tag.charAt(0).toUpperCase() + section.tag.slice(1)}
                      </h3>
                      {isExpanded ? (
                        <ChevronUp size={16} className={colors.text} />
                      ) : (
                        <ChevronDown size={16} className={colors.text} />
                      )}
                    </button>
                    {isExpanded && (
                      <div className="border-t border-white/5 p-4 max-h-[300px] overflow-y-auto">
                        <div className="prose prose-invert prose-sm max-w-none text-zinc-300">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {section.content}
                          </ReactMarkdown>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </>
          ) : (
            // Fallback: render raw prompt as markdown
            <div className={`bg-black/40 rounded-lg border border-white/5 overflow-hidden ${!hasMessages ? 'p-4' : ''}`}>
              {hasMessages ? (
                <>
                  <button
                    onClick={() => { toggleSection('system'); }}
                    className="w-full flex items-center justify-between p-3 hover:bg-white/5 transition-colors"
                  >
                    <h3 className="font-semibold text-text-primary text-sm">System Prompt</h3>
                    {expandedSections.system ? (
                      <ChevronUp size={16} className="text-text-secondary" />
                    ) : (
                      <ChevronDown size={16} className="text-text-secondary" />
                    )}
                  </button>
                  {expandedSections.system && (
                    <div className="border-t border-white/5 p-4 max-h-[300px] overflow-y-auto">
                      <div className="prose prose-invert prose-sm max-w-none text-zinc-300">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {promptStr}
                        </ReactMarkdown>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="prose prose-invert prose-sm max-w-none text-zinc-300 overflow-x-hidden">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {promptStr}
                  </ReactMarkdown>
                </div>
              )}
            </div>
          )}

          {/* Chat History Section */}
          {hasMessages && (
                <div className="bg-black/40 rounded-lg border border-white/5 overflow-hidden">
                  <button
                    onClick={() => { toggleSection('history'); }}
                    className="w-full flex items-center justify-between p-3 hover:bg-white/5 transition-colors"
                  >
                    <h3 className="font-semibold text-text-primary text-sm">
                      Chat History ({selectedPrompt.prompt?.messages?.length ?? 0} mensagens)
                    </h3>
                    {expandedSections.history ? (
                      <ChevronUp size={16} className="text-text-secondary" />
                    ) : (
                      <ChevronDown size={16} className="text-text-secondary" />
                    )}
                  </button>
                  {expandedSections.history && (
                    <div className="border-t border-white/5 p-4 max-h-[400px] overflow-y-auto space-y-2">
                      {selectedPrompt.prompt?.messages?.map((msg, idx) => {
                        const { attributes, text } = parseMsgAttributes(msg.content);
                        return (
                          <div key={idx} className="flex gap-3">
                            <span className="text-[10px] font-bold px-2 py-1 rounded bg-zinc-800 text-zinc-400 flex-shrink-0 h-fit">
                              {msg.role === 'human' ? 'User' : msg.role === 'ai' ? 'AI' : 'System'}
                            </span>
                            {!!(attributes.data ?? attributes.hora) && (
                              <div className="flex gap-1 flex-shrink-0">
                                {attributes.data && (
                                  <span className="text-[10px] px-1 py-0.5 rounded bg-blue-900/40 text-blue-300">
                                    {attributes.data}
                                  </span>
                                )}
                                {attributes.hora && (
                                  <span className="text-[10px] px-1 py-0.5 rounded bg-purple-900/40 text-purple-300">
                                    {attributes.hora}
                                  </span>
                                )}
                              </div>
                            )}
                            <p className="text-xs text-zinc-300 flex-1 break-words">
                              {text}
                            </p>
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}

              {/* Tools Section */}
              {hasTools && (
                <div className="bg-black/40 rounded-lg border border-white/5 overflow-hidden">
                  <button
                    onClick={() => { toggleSection('tools'); }}
                    className="w-full flex items-center justify-between p-3 hover:bg-white/5 transition-colors"
                  >
                    <h3 className="font-semibold text-text-primary text-sm">
                      Tools ({selectedPrompt.prompt?.tools?.length ?? 0})
                    </h3>
                    {expandedSections.tools ? (
                      <ChevronUp size={16} className="text-text-secondary" />
                    ) : (
                      <ChevronDown size={16} className="text-text-secondary" />
                    )}
                  </button>
                  {expandedSections.tools && (
                    <div className="border-t border-white/5 p-4 flex flex-wrap gap-2">
                      {selectedPrompt.prompt?.tools?.map((tool) => (
                        <span
                          key={tool}
                          className="px-2 py-1 bg-orange-500/10 text-orange-400 text-xs rounded font-mono"
                        >
                          {tool}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}
        </div>
      </div>
    </div>
  );
}
