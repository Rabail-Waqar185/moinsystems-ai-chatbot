import type {
  ChatMessageRequest,
  ChatMessageResponse,
  LeadCaptureRequest,
  LeadCaptureResponse,
  SessionCreateResponse,
} from "../types";

// Set by the embedding page (WordPress plugin in production, index.html in dev)
// before this script loads — see index.html's window.MoinChatWidgetConfig.
declare global {
  interface Window {
    MoinChatWidgetConfig?: { apiBaseUrl?: string };
  }
}

const API_BASE_URL = window.MoinChatWidgetConfig?.apiBaseUrl ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<TResponse>(path: string, body: unknown): Promise<TResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    // Network failure — offline, DNS, CORS block, server unreachable entirely.
    throw new ApiError(0, "Network error — could not reach the chat service.");
  }

  if (response.status === 429) {
    throw new ApiError(429, "You're sending messages a bit fast — please wait a moment and try again.");
  }
  if (!response.ok) {
    // Covers 422 (validation), 413 (too large), 500/503 — all handled generically
    // here; per-field validation errors from /lead-capture come back as a 200
    // with success:false instead, so this branch is for hard request failures.
    throw new ApiError(response.status, "Something went wrong. Please try again.");
  }
  return (await response.json()) as TResponse;
}

export function createSession(sourcePage: string): Promise<SessionCreateResponse> {
  return request<SessionCreateResponse>("/sessions", { source_page: sourcePage });
}

export function sendChatMessage(payload: ChatMessageRequest): Promise<ChatMessageResponse> {
  return request<ChatMessageResponse>("/chat/messages", payload);
}

export function submitLead(payload: LeadCaptureRequest): Promise<LeadCaptureResponse> {
  return request<LeadCaptureResponse>("/lead-capture", payload);
}
