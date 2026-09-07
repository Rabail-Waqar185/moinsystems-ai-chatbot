# MoinSystems AI Chat Widget

React + TypeScript chat widget (Day 7). Talks only to the backend's stable
HTTP API — no AI/RAG/DB/email logic lives here (SRS 7.10).

## Setup

```bash
npm install
```

## Local development

Make sure the backend is running first (`uvicorn app.main:app --reload` in
the `moin-ai-chatbot` folder), then:

```bash
npm run dev
```

Opens a dev harness page (`index.html`) with the widget mounted bottom-right,
pointed at `http://localhost:8000/api/v1` (configured in `index.html`'s
`window.MoinChatWidgetConfig`).

## Production build

```bash
npm run build
```

Outputs `dist/moin-chat-widget.js` and `dist/moin-chat-widget.css` — fixed
filenames (not content-hashed) so a WordPress plugin/shortcode can reference
them directly.

## Embedding on a real site (e.g. WordPress)

Before the widget's `<script>` tag, set the real API URL:

```html
<script>
  window.MoinChatWidgetConfig = {
    apiBaseUrl: "https://your-railway-app.up.railway.app/api/v1",
  };
</script>
<link rel="stylesheet" href="/path/to/moin-chat-widget.css" />
<script type="module" src="/path/to/moin-chat-widget.js"></script>
```

The widget self-mounts (creates its own container div) — no specific host
element required. It reads the current page URL automatically and sends it
as `source_page` on every request.

## Notes / known limitations (Day 7 scope)

- CSS is prefixed (`.moin-chat-*`) but **not** Shadow-DOM isolated — a very
  aggressive host page stylesheet could theoretically leak in. Worth
  revisiting if WordPress theme conflicts show up during Day 8 integration.
- Session continuity uses `localStorage` (`moin_chat_session_token`) — a
  returning visitor within the same browser continues their conversation.
- CORS: the backend's `ALLOWED_ORIGINS` must include whatever origin this
  widget is served from, or requests will be blocked by the browser.
