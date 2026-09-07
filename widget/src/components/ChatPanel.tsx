import { Composer } from "./Composer";
import { ErrorBanner } from "./ErrorBanner";
import { LeadForm } from "./LeadForm";
import { MessageList } from "./MessageList";
import type { useChatWidget } from "../hooks/useChatWidget";

type ChatWidgetState = ReturnType<typeof useChatWidget>;

interface ChatPanelProps {
  widget: ChatWidgetState;
}

export function ChatPanel({ widget }: ChatPanelProps) {
  const { messages, sendMessage, isSending, error, dismissError, showLeadForm, submitLeadForm, setIsOpen } =
    widget;

  return (
    <div className="moin-chat-panel" role="dialog" aria-label="MoinSystems AI chat">
      <div className="moin-chat-header">
        <span>MoinSystems AI</span>
        <button
          type="button"
          className="moin-chat-header__close"
          onClick={() => setIsOpen(false)}
          aria-label="Close chat"
        >
          &times;
        </button>
      </div>

      {error && <ErrorBanner message={error} onDismiss={dismissError} />}

      <MessageList messages={messages} isSending={isSending && !showLeadForm} />

      {showLeadForm ? (
        <LeadForm onSubmit={submitLeadForm} disabled={isSending} />
      ) : (
        <Composer onSend={sendMessage} disabled={isSending} />
      )}
    </div>
  );
}
