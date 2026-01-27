export interface Message {
  id: number;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
}

export class MessageFactory {
  static create(overrides?: Partial<Message>): Message {
    return {
      id: Date.now(),
      text: 'Test message',
      sender: 'user',
      timestamp: new Date(),
      ...overrides
    };
  }

  static createAI(text: string): Message {
    return this.create({ sender: 'ai', text });
  }

  static createUser(text: string): Message {
    return this.create({ sender: 'user', text });
  }

  static createList(count: number, sender: 'user' | 'ai' = 'user'): Message[] {
    return Array.from({ length: count }, (_, i) =>
      this.create({ id: i, sender })
    );
  }

  static createConversation(): Message[] {
    return [
      this.createUser('Qual é o melhor exercício para peito?'),
      this.createAI('Para peito, recomendo supino reto, supino inclinado e crucifixo.'),
      this.createUser('E para costas?'),
      this.createAI('Para costas: barra fixa, remada com barra e remada machine.')
    ];
  }
}
