export type Sender = 'Student' | 'Trainer' | 'System';

export interface ChatMessage {
  text: string;
  translations?: Record<string, string>;
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
  image_base64?: string;
  image_mime_type?: MessageImagePayload['mimeType'];
}
