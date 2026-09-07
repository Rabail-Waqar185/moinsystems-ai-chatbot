interface LauncherButtonProps {
  isOpen: boolean;
  onClick: () => void;
}

export function LauncherButton({ isOpen, onClick }: LauncherButtonProps) {
  return (
    <button
      type="button"
      className="moin-chat-launcher"
      onClick={onClick}
      aria-label={isOpen ? "Close chat" : "Open chat"}
      aria-expanded={isOpen}
    >
      {isOpen ? "\u2715" : "\u{1F4AC}"}
    </button>
  );
}
