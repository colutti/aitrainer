import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { ChatContextPanel } from './ChatContextPanel';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, options?: Record<string, unknown>) => {
      if (key === 'chat.context.trainer_label') return 'Treinador';
      if (key === 'chat.context.message_count') {
        const count = typeof options?.count === 'number' ? options.count : 0;
        return `${count} mensagens nesta conversa`;
      }
      if (key === 'chat.context.responding_now') return 'Respondendo agora';
      if (key === 'chat.context.default_trainer_id') return 'treinador-padrao';
      if (key === 'chat.debug.title') return 'Depuração da última resposta';
      if (key === 'chat.debug.subtitle') return 'Visível apenas em desenvolvimento. Mostra a ordem, o tempo e a saída de cada nó.';
      if (key === 'chat.debug.status.completed') return 'Concluído';
      if (key === 'chat.debug.status.pending') return 'Pendente';
      if (key === 'chat.debug.status.not_called') return 'Não chamado';
      if (key === 'chat.debug.no_output') return 'Sem saída registrada';
      if (key === 'chat.debug.no_data') return 'Nenhum trace disponível';
      if (key === 'chat.debug.nodes_title') return 'Nós executados';
      if (key === 'chat.debug.identifiers') return 'Identificadores';
      if (key === 'chat.debug.tools') return 'Ferramentas';
      if (key === 'chat.debug.none') return 'Nenhuma';
      if (key === 'chat.debug.intent') return 'Intenção';
      if (key === 'chat.debug.duration_total') return 'Tempo total';
      if (key === 'chat.debug.security') return 'Segurança';
      if (key === 'chat.debug.revision') return 'Precisa revisão';
      if (key === 'common.yes') return 'Sim';
      if (key === 'common.no') return 'Não';
      return key;
    },
  }),
}));

describe('ChatContextPanel', () => {
  const baseProps = {
    trainerName: "Breno 'The Bro' Silva",
    trainerId: 'gymbro',
    isStreaming: false,
    messageCount: 26,
    showDebugPanel: true,
  };

  it('does not render trainer section texts', () => {
    render(<ChatContextPanel {...baseProps} />);
    expect(screen.queryByText('Treinador')).not.toBeInTheDocument();
    expect(screen.queryByText(/Breno/)).not.toBeInTheDocument();
    expect(screen.queryByText(/26 mensagens nesta conversa/)).not.toBeInTheDocument();
    expect(screen.queryByText('gymbro')).not.toBeInTheDocument();
  });

  it('does not render debug subtitle', () => {
    render(<ChatContextPanel {...baseProps} />);
    expect(
      screen.queryByText(/Visível apenas em desenvolvimento/),
    ).not.toBeInTheDocument();
  });

  it('renders nodes in execution order with correct statuses', () => {
    const debugTrace = {
      user_email: 'a@b.com',
      request_id: 'r1',
      conversation_id: 'c1',
      turn_id: 't1',
      channel: 'app',
      status: 'success',
      duration_ms: 1200,
      intent: 'general',
      security_status: 'safe',
      plan_needs_revision: false,
      tools_called: ['search_memory'],
      persistence_actions: [],
      final_response: 'ok',
      technical_response: 'ok',
      started_at: '2026-05-02T10:00:00',
      ended_at: '2026-05-02T10:00:05',
      node_outputs: {},
      nodes: [
        { node_name: 'session_context', status: 'completed', started_at: '2026-05-02T10:00:00', duration_ms: 100, output_preview: 'hydrated' },
        { node_name: 'prompt_security', status: 'completed', started_at: '2026-05-02T10:00:01', duration_ms: 50, output_preview: 'safe' },
        { node_name: 'intent_router', status: 'completed', started_at: '2026-05-02T10:00:02', duration_ms: 80, output_preview: 'general' },
        { node_name: 'training_specialist', status: 'pending', started_at: null, duration_ms: null, output_preview: '' },
      ],
    };
    render(<ChatContextPanel {...baseProps} debugTrace={debugTrace} />);

    expect(screen.getByText('session_context')).toBeInTheDocument();
    expect(screen.getByText('prompt_security')).toBeInTheDocument();
    expect(screen.getByText('intent_router')).toBeInTheDocument();
    expect(screen.getByText('training_specialist')).toBeInTheDocument();

    expect(screen.getAllByText('Concluído').length).toBeGreaterThanOrEqual(3);
    expect(screen.getByText('Não chamado')).toBeInTheDocument();
  });

  it('renders tool labels per node', () => {
    const debugTrace = {
      user_email: 'a@b.com',
      request_id: 'r1',
      conversation_id: 'c1',
      turn_id: 't1',
      channel: 'app',
      status: 'success',
      duration_ms: 1200,
      intent: 'general',
      security_status: 'safe',
      plan_needs_revision: false,
      tools_called: ['search_memory'],
      persistence_actions: [],
      final_response: 'ok',
      technical_response: 'ok',
      started_at: '2026-05-02T10:00:00',
      ended_at: '2026-05-02T10:00:05',
      node_outputs: {},
      nodes: [
        { node_name: 'memory_hub', status: 'completed', started_at: '2026-05-02T10:00:00', duration_ms: 200, output_preview: 'saved', tools_called: ['save_memory', 'update_memory'] },
      ],
    };
    render(<ChatContextPanel {...baseProps} debugTrace={debugTrace} />);

    expect(screen.getByText('save_memory')).toBeInTheDocument();
    expect(screen.getByText('update_memory')).toBeInTheDocument();
  });
});
