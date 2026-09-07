import { useEffect, useRef } from "react";
import type { DisplayMessage } from "../types";

interface MessageListProps {
  messages: DisplayMessage[];
  isSending: boolean;
}

export function MessageList({ messages, isSending }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isSending]);

  return (
    <div className="moin-chat-messages" role="log" aria-live="polite">
      {messages.length === 0 && (
        <div className="moin-chat-empty-state">
          Hi! Ask me anything about MoinSystems AI's services, pricing, or how we can help with your project.
        </div>
      )}
      {messages.map((m) => (
        <div key={m.id} className={`moin-chat-bubble moin-chat-bubble--${m.role}`}>
          {m.content}
        </div>
      ))}
      {isSending && (
        <div className="moin-chat-bubble moin-chat-bubble--assistant moin-chat-bubble--loading">
          <span className="moin-chat-dot" />
          <span className="moin-chat-dot" />
          <span className="moin-chat-dot" />
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
