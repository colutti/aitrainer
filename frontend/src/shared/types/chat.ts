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
  temperature?: number | null;
  max_tokens?: number | null;
  top_p?: number | null;
  frequency_penalty?: number | null;
  provider_sort?: string | null;
  tool_policy?: string | null;
  tool_names?: string[];
  parallel_tool_calls?: boolean | null;
  reasoning?: Record<string, unknown> | null;
  context_blocks?: string[];
  peer_inputs?: string[];
  output_contract?: string;
  resolved_input?: string;
  resolved_context?: string;
  resolved_peer_outputs?: string;
  raw_output?: string;
  structured_output?: Record<string, unknown> | null;
  state_before?: Record<string, unknown> | null;
  state_after?: Record<string, unknown> | null;
  state_diff?: Record<string, unknown> | null;
  specialist_state?: Record<string, unknown> | null;
  pending_action?: Record<string, unknown> | null;
}

export interface ChatGraphTraceTimelineSummary {
  slowest_node: string | null;
  largest_output_node: string | null;
  largest_output_chars: number | null;
  nodes_with_state_changes: string[];
  nodes_with_pending_actions: string[];
  interrupted_at: string | null;
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
  graph_error?: string | null;
  request_payload_sanitized?: string;
  conversation_state_before?: Record<string, unknown>;
  conversation_state_after?: Record<string, unknown>;
  pending_action_resolution?: Record<string, unknown>;
  timeline_summary?: ChatGraphTraceTimelineSummary;
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
