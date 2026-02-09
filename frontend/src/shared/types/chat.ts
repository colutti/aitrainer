export type Sender = 'Student' | 'Trainer' | 'System';

export interface ChatMessage {
  text: string;
  sender: Sender;
  timestamp: string;
  trainer_type?: string;
  summarized?: boolean;
}

export interface MessageRequest {
  user_message: string;
}
