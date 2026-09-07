import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import "./styles.css";

// Self-mounting: creates its own container rather than requiring the host
// page (WordPress or otherwise) to include a specific <div id="..."> —
// dropping in the <script> tag is enough. See README.md for embed instructions.
const MOUNT_ID = "moin-chat-widget-root";

function mount() {
  let container = document.getElementById(MOUNT_ID);
  if (!container) {
    container = document.createElement("div");
    container.id = MOUNT_ID;
    document.body.appendChild(container);
  }
  createRoot(container).render(
    <StrictMode>
      <App />
    </StrictMode>
  );
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", mount);
} else {
  mount();
}
