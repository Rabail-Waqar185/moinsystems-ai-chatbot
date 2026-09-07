import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

/// <reference types="vitest/config" />

// Produces a predictably-named JS + CSS bundle in dist/ (not content-hashed),
// so a WordPress plugin/shortcode can reference fixed filenames per the SRS's
// widget-embedding diagram ("loads chatbot widget JS/CSS").
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
  },
  build: {
    cssCodeSplit: false,
    rollupOptions: {
      output: {
        entryFileNames: "moin-chat-widget.js",
        chunkFileNames: "moin-chat-widget-[name].js",
        assetFileNames: (assetInfo) =>
          assetInfo.name?.endsWith(".css") ? "moin-chat-widget.css" : "assets/[name][extname]",
      },
    },
  },
});
