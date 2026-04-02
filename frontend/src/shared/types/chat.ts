export type Sender = 'Student' | 'Trainer' | 'System';

export interface ChatMessage {
  text: string;
  translations?: Record<string, string>;
  images?: MessageImagePayload[];
  sender: Sender;
  timestamp: string;
  trainer_type?: string;
  summarized?: boolean;
}

export interface MessageImagePayload {
  base64: string;
  mimeType: 'image/jpeg' | 'image/png' | 'image/webp';
}

export interface MessageRequest {
  user_message: string;
  images?: {
    base64: string;
    mime_type: MessageImagePayload['mimeType'];
  }[];
}
