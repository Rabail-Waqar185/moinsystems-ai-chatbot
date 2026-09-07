import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent } from "react";

interface ComposerProps {
  onSend: (text: string) => void;
  disabled: boolean;
}

export function Composer({ onSend, disabled }: ComposerProps) {
  const [value, setValue] = useState("");
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // The textarea is disabled while a reply is in flight (so focus gets
  // stripped by the browser automatically). Once it re-enables, bring
  // focus back so the visitor doesn't have to click in again.
  useEffect(() => {
    if (!disabled) {
      inputRef.current?.focus();
    }
  }, [disabled]);

  const handleSend = () => {
    if (!value.trim() || disabled) return;
    onSend(value);
    setValue("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="moin-chat-composer">
      <textarea
        ref={inputRef}
        className="moin-chat-composer__input"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type your message..."
        rows={1}
        maxLength={4000}
        disabled={disabled}
        aria-label="Type your message"
      />
      <button
        type="button"
        className="moin-chat-composer__send"
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        aria-label="Send message"
      >
        Send
      </button>
    </div>
  );
}
