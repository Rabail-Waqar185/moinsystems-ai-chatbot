// Mirrors app/schemas/chat.py, session.py, lead.py on the backend.
// Keep these in sync manually if the backend contract changes — there's no
// shared codegen between the two repos (SRS 7.10: widget only ever
// consumes the stable HTTP contract, never assumes internal shapes).

export type LeadState =
  | "not_active"
  | "collecting_name"
  | "collecting_email"
  | "collecting_phone"
  | "complete";

export interface ChatMessageRequest {
  message: string;
  session_token?: string;
  source_page?: string;
}

export interface ChatMessageResponse {
  session_token: string;
  reply: string;
  intent: string | null;
  lead_state: LeadState | null;
}

export interface SessionCreateResponse {
  session_token: string;
}

export interface LeadCaptureRequest {
  session_token?: string;
  full_name: string;
  email: string;
  contact_number: string;
  source_page?: string;
}

export interface LeadCaptureResponse {
  session_token: string;
  success: boolean;
  errors: Record<string, string> | null;
}

// Local UI-only representation of a chat turn — not the backend's ChatMessage row.
export interface DisplayMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
}
