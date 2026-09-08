import "@testing-library/jest-dom/vitest";
import { afterEach, vi } from "vitest";
import { cleanup } from "@testing-library/react";

// jsdom doesn't implement scrollIntoView (MessageList calls it on new messages).
Element.prototype.scrollIntoView = vi.fn();

// Reset DOM and any persisted session between tests so they stay isolated.
afterEach(() => {
  cleanup();
  window.localStorage.clear();
});
