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

export interface ChatGraphNodeTrace {
  node_name: string;
  status: string;
  started_at?: string | null;
  completed_at?: string | null;
  duration_ms?: number | null;
  output_preview?: string;
  error?: string | null;
  config_hash?: string | null;
  config_version?: string | null;
  model?: string | null;
  tools_called?: string[];
}

export interface ChatGraphTrace {
  user_email: string;
  request_id: string;
  conversation_id: string;
  turn_id: string;
  channel: string;
  status: string;
  error?: string | null;
  started_at: string;
  ended_at: string;
  duration_ms: number;
  intent: string;
  security_status: string;
  plan_needs_revision: boolean;
  tools_called: string[];
  persistence_actions: string[];
  final_response: string;
  technical_response: string;
  node_outputs: Record<string, string>;
  nodes: ChatGraphNodeTrace[];
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
