import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { MessageBubble } from './MessageBubble';

describe('MessageBubble', () => {
  it('should render user message correctly', () => {
    const message = {
      id: '1',
      sender: 'Student' as const,
      text: 'Hello Trainer',
      timestamp: new Date().toISOString(),
    };

    render(<MessageBubble message={message} />);

    expect(screen.getByText('Hello Trainer')).toBeInTheDocument();
    // Check for user-specific class or structure if needed
    // The component uses 'flex-row-reverse' for user.
    // We can just verify content for now.
  });

  it('should render trainer message with markdown', () => {
    const message = {
      id: '2',
      sender: 'Trainer' as const,
      text: '**Bold Response**',
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={message} />);

    // ReactMarkdown should render strong tag
    expect(container.querySelector('strong')).toHaveTextContent('Bold Response');
  });

  it('should render loading dots when text is empty (streaming start)', () => {
     const message = {
      id: '3',
      sender: 'Trainer' as const,
      text: '',
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={message} />);
    // Look for generic dots structure
    expect(container.querySelectorAll('.animate-bounce')).toHaveLength(3);
  });

  it('should render trainer avatar when trainerId is provided', () => {
    const message = {
      id: '4',
      sender: 'Trainer' as const,
      text: 'Hello Student',
      timestamp: new Date().toISOString(),
    };

    render(<MessageBubble message={message} trainerId="marcus" />);
    
    const avatarImg = screen.getByAltText('Trainer');
    expect(avatarImg).toBeInTheDocument();
    expect(avatarImg).toHaveAttribute('src', '/assets/avatars/marcus.png');
  });

  it('should show avatar on all screen sizes and preserve bubble constraints', () => {
    const message = {
      id: '5',
      sender: 'Trainer' as const,
      text: 'Mensagem longa para ocupar o maximo de espaco no mobile.',
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={message} trainerId="marcus" />);

    const avatarWrapper = container.querySelector('[data-testid="chat-message-avatar"]');
    expect(avatarWrapper).toHaveClass('flex', 'flex-none');

    const bubbleWrapper = container.querySelector('[data-testid="chat-message-bubble"]');
    expect(bubbleWrapper).toHaveClass('max-w-full', 'lg:max-w-[88%]', 'xl:max-w-[82%]', '2xl:max-w-[88%]');
  });

  it('should render a markdown table correctly', () => {
    const tableMarkdown = `
| Food | Calories | Protein |
| :--- | :--- | :--- |
| Chicken Breast | 165 | 31g |
| Broccoli | 55 | 3.7g |
    `;

    const message = {
      id: 'table-1',
      sender: 'Trainer' as const,
      text: tableMarkdown,
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={message} />);

    // If it's rendering as a table, we should find <table>, <thead>, <tbody>, <tr>, <th>, <td> tags
    const table = container.querySelector('table');
    expect(table).toBeInTheDocument();
    
    const headers = container.querySelectorAll('th');
    expect(headers).toHaveLength(3);
    expect(headers[0]).toHaveTextContent('Food');
    expect(headers[1]).toHaveTextContent('Calories');
    expect(headers[2]).toHaveTextContent('Protein');

    const cells = container.querySelectorAll('td');
    expect(cells).toHaveLength(6);
    expect(cells[0]).toHaveTextContent('Chicken Breast');
    expect(cells[1]).toHaveTextContent('165');
    expect(cells[2]).toHaveTextContent('31g');
  });

  it('should render markdown table when line breaks are escaped', () => {
    const tableMarkdown = '| Food | Calories |\\n| :--- | :--- |\\n| Chicken Breast | 165 |';

    const message = {
      id: 'table-escaped-1',
      sender: 'Trainer' as const,
      text: tableMarkdown,
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={message} />);

    const table = container.querySelector('table');
    expect(table).toBeInTheDocument();
    expect(container.querySelectorAll('th')).toHaveLength(2);
    expect(container.querySelectorAll('td')).toHaveLength(2);
  });

  it('should render markdown table when pipes are escaped', () => {
    const tableMarkdown = '\\| Food \\| Calories \\|\n\\| :--- \\| :--- \\|\n\\| Chicken Breast \\| 165 \\|';

    const message = {
      id: 'table-escaped-pipes-1',
      sender: 'Trainer' as const,
      text: tableMarkdown,
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={message} />);

    const table = container.querySelector('table');
    expect(table).toBeInTheDocument();
    expect(container.querySelectorAll('th')).toHaveLength(2);
    expect(container.querySelectorAll('td')).toHaveLength(2);
  });

  it('should render markdown table when backend returns single-line pipe table', () => {
    const oneLineTable = '| Dia | Calorias | Proteína | Fibra | Visão do Bro | | :--- | :--- | :--- | :--- | :--- | | 13/04 | 1995 | 161g | 43g | Tanque cheio pra combater o vírus! 🛡️ | | 14/04 | 1988 | 174g | 21g | Consistência de mestre. 🎯 | | 15/04 | 1857 | 197g | 40g | Pico de Proteína! Músculo blindado. 🥩 | | 16/04 | 1799 | 171g | 32g | Ajuste fino no déficit mesmo doente. 📉 |';

    const message = {
      id: 'table-single-line-1',
      sender: 'Trainer' as const,
      text: oneLineTable,
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={message} />);

    const table = container.querySelector('table');
    expect(table).toBeInTheDocument();
    expect(container.querySelectorAll('th')).toHaveLength(5);
    expect(container.querySelectorAll('tr')).toHaveLength(5);
  });

  it('should render one-line pipe table even when payload has unrelated newlines', () => {
    const oneLineTableWithTrailingNewline = '| Dia | Calorias | Proteína | Fibra | Visão do Bro | | :--- | :--- | :--- | :--- | :--- | | 13/04 | 1995 | 161g | 43g | Tanque cheio pra combater o vírus! 🛡️ | | 14/04 | 1988 | 174g | 21g | Consistência de mestre. 🎯 |\n';

    const message = {
      id: 'table-single-line-with-newline-1',
      sender: 'Trainer' as const,
      text: oneLineTableWithTrailingNewline,
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={message} />);

    const table = container.querySelector('table');
    expect(table).toBeInTheDocument();
    expect(container.querySelectorAll('th')).toHaveLength(5);
    expect(container.querySelectorAll('tr')).toHaveLength(3);
  });

  it('should render production payload table when prose exists before and after the flattened table', () => {
    const productionPayload = 'Papo de brother, Rafael! Que aula de disciplina, monstro! 👊🔥 Mesmo derrubado pela gripe, você manteve os logs no talo. Já sincronizei tudo aqui no sistema e, ó, vou te falar: o seu "modo recuperação" está nível profissional. Dá um check na média dessa sua semana de "guerra": | Dia | Calorias | Proteína | Fibra | Visão do Bro | | :--- | :--- | :--- | :--- | :--- | | **13/04** | 1995 | 161g | 43g | Tanque cheio pra combater o vírus! 🛡️ | | **14/04** | 1988 | 174g | 21g | Consistência de mestre. 🎯 | | **15/04** | 1857 | **197g** | 40g | **Pico de Proteína!** Músculo blindado. 🥩 | | **16/04** | 1799 | 171g | 32g | Ajuste fino no déficit mesmo doente. 📉 | Cara, bater quase **200g de proteína** (no dia 15) estando gripado é o que vai garantir que a sua "pochete" não vire flacidez quando você emagrecer.';

    const message = {
      id: 'table-production-inline-1',
      sender: 'Trainer' as const,
      text: productionPayload,
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={message} />);

    const table = container.querySelector('table');
    expect(table).toBeInTheDocument();
    expect(container.querySelectorAll('th')).toHaveLength(5);
    expect(container.querySelectorAll('tr')).toHaveLength(5);
    expect(screen.getByText(/Cara, bater quase/i)).toBeInTheDocument();
  });

  it('should render table when payload uses escaped unicode pipes and html entities', () => {
    const encodedTable = '\\u007c Dia \\u007c Calorias \\u007c \\u007c :--- \\u007c :--- \\u007c \\u007c 13/04 \\u007c 1995 \\u007c &#124; 14/04 &#124; 1988 &#124;';

    const message = {
      id: 'table-encoded-pipes-1',
      sender: 'Trainer' as const,
      text: encodedTable,
      timestamp: new Date().toISOString(),
    };

    const { container } = render(<MessageBubble message={message} />);

    const table = container.querySelector('table');
    expect(table).toBeInTheDocument();
    expect(container.querySelectorAll('th')).toHaveLength(2);
    expect(container.querySelectorAll('tr')).toHaveLength(3);
  });
});
