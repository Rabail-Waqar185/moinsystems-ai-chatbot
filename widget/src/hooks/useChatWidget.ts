import { useCallback, useEffect, useState } from "react";
import { ApiError, sendChatMessage, submitLead } from "../api/client";
import type { DisplayMessage, LeadState } from "../types";

const SESSION_STORAGE_KEY = "moin_chat_session_token";

function uid(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export function useChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [sessionToken, setSessionToken] = useState<string | null>(() =>
    localStorage.getItem(SESSION_STORAGE_KEY)
  );
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [leadState, setLeadState] = useState<LeadState>("not_active");
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (sessionToken) {
      localStorage.setItem(SESSION_STORAGE_KEY, sessionToken);
    }
  }, [sessionToken]);

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isSending) return;

      setError(null);
      setMessages((prev) => [...prev, { id: uid(), role: "user", content: trimmed }]);
      setIsSending(true);

      try {
        const response = await sendChatMessage({
          message: trimmed,
          session_token: sessionToken ?? undefined,
          source_page: window.location.href,
        });
        setSessionToken(response.session_token);
        setLeadState(response.lead_state ?? "not_active");
        setMessages((prev) => [...prev, { id: uid(), role: "assistant", content: response.reply }]);
      } catch (err) {
        const message = err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
        setError(message);
      } finally {
        setIsSending(false);
      }
    },
    [sessionToken, isSending]
  );

  const submitLeadForm = useCallback(
    async (fields: { full_name: string; email: string; contact_number: string }) => {
      setError(null);
      setIsSending(true);
      try {
        const response = await submitLead({
          ...fields,
          session_token: sessionToken ?? undefined,
          source_page: window.location.href,
        });
        setSessionToken(response.session_token);
        if (response.success) {
          setLeadState("complete");
          setMessages((prev) => [
            ...prev,
            {
              id: uid(),
              role: "system",
              content: "Thanks! Your details have been recorded and our team will be in touch.",
            },
          ]);
          return { success: true as const };
        }
        // Field-level validation errors — let the form display them inline.
        return { success: false as const, errors: response.errors ?? {} };
      } catch (err) {
        const message = err instanceof ApiError ? err.message : "Something went wrong. Please try again.";
        setError(message);
        return { success: false as const, errors: {} };
      } finally {
        setIsSending(false);
      }
    },
    [sessionToken]
  );

  const showLeadForm = leadState !== "not_active" && leadState !== "complete";

  return {
    isOpen,
    setIsOpen,
    messages,
    sendMessage,
    isSending,
    error,
    dismissError: () => setError(null),
    showLeadForm,
    submitLeadForm,
  };
}
