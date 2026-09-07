import { ChatPanel } from "./components/ChatPanel";
import { LauncherButton } from "./components/LauncherButton";
import { useChatWidget } from "./hooks/useChatWidget";

export function App() {
  const widget = useChatWidget();

  return (
    <div className="moin-chat-root">
      {widget.isOpen && <ChatPanel widget={widget} />}
      <LauncherButton isOpen={widget.isOpen} onClick={() => widget.setIsOpen((v) => !v)} />
    </div>
  );
}
