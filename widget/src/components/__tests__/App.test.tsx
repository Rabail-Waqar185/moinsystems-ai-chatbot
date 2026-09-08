import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { App } from "../../App";

function mockFetchOnce(response: {
  ok: boolean;
  status: number;
  body: unknown;
}) {
  return vi.fn().mockResolvedValueOnce({
    ok: response.ok,
    status: response.status,
    json: async () => response.body,
  });
}

async function openWidgetAndSendMessage(text: string) {
  const user = userEvent.setup();
  render(<App />);
  await user.click(screen.getByRole("button", { name: /open chat/i }));
  const input = screen.getByPlaceholderText(/type your message/i);
  await user.type(input, text);
  await user.click(screen.getByRole("button", { name: /send message/i }));
  return user;
}

describe("App - critical chat flows", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("opens the panel and shows the empty-state greeting before any messages", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole("button", { name: /open chat/i }));
    expect(
      screen.getByText(/ask me anything about moinsystems ai/i),
    ).toBeInTheDocument();
  });

  it("sends a message and displays both the user bubble and the assistant's reply", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchOnce({
        ok: true,
        status: 200,
        body: {
          session_token: "tok_123",
          reply: "We build custom software.",
          intent: "service_inquiry",
          lead_state: "not_active",
        },
      }),
    );

    await openWidgetAndSendMessage("Do you build software?");

    expect(
      await screen.findByText("Do you build software?"),
    ).toBeInTheDocument();
    expect(
      await screen.findByText("We build custom software."),
    ).toBeInTheDocument();
  });

  it("persists the session token to localStorage after a successful reply", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchOnce({
        ok: true,
        status: 200,
        body: {
          session_token: "tok_persisted",
          reply: "Hello!",
          intent: null,
          lead_state: "not_active",
        },
      }),
    );

    await openWidgetAndSendMessage("hi");

    await waitFor(() => {
      expect(window.localStorage.getItem("moin_chat_session_token")).toBe(
        "tok_persisted",
      );
    });
  });

  it("shows an error banner when the request fails over the network", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValueOnce(new Error("network down")),
    );

    await openWidgetAndSendMessage("hello");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /could not reach the chat service/i,
    );
  });

  it("shows a friendly message when the backend rate-limits the request (429)", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce({
          ok: false,
          status: 429,
          json: async () => ({}),
        }),
    );

    await openWidgetAndSendMessage("hello");

    expect(await screen.findByRole("alert")).toHaveTextContent(
      /sending messages a bit fast/i,
    );
  });

  it("switches from the composer to the lead-capture form once lead_state becomes active", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetchOnce({
        ok: true,
        status: 200,
        body: {
          session_token: "tok_lead",
          reply: "Could you share your full name?",
          intent: "pricing_quote",
          lead_state: "collecting_name",
        },
      }),
    );

    await openWidgetAndSendMessage("How much does it cost?");

    expect(await screen.findByLabelText(/full name/i)).toBeInTheDocument();
    expect(
      screen.queryByPlaceholderText(/type your message/i),
    ).not.toBeInTheDocument();
  });

  it("submits the lead form successfully and returns to the composer with a confirmation message", async () => {
    // First call: the pricing question that triggers lead capture.
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          session_token: "tok_lead2",
          reply: "Could you share your full name?",
          intent: "pricing_quote",
          lead_state: "collecting_name",
        }),
      })
      // Second call: the lead form submission.
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          session_token: "tok_lead2",
          success: true,
          errors: null,
        }),
      });
    vi.stubGlobal("fetch", fetchMock);

    const user = await openWidgetAndSendMessage("How much does it cost?");
    await screen.findByLabelText(/full name/i);

    await user.type(screen.getByLabelText(/full name/i), "Jane Doe");
    await user.type(screen.getByLabelText(/email/i), "jane@example.com");
    await user.type(screen.getByLabelText(/phone number/i), "03001234567");
    await user.click(screen.getByRole("button", { name: /submit/i }));

    expect(
      await screen.findByText(/details have been recorded/i),
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/type your message/i),
    ).toBeInTheDocument();
  });

  it("shows inline field errors when the backend rejects the lead form as invalid", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          session_token: "tok_lead3",
          reply: "Could you share your full name?",
          intent: "pricing_quote",
          lead_state: "collecting_name",
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => ({
          session_token: "tok_lead3",
          success: false,
          errors: { email: "That email address doesn't look valid." },
        }),
      });
    vi.stubGlobal("fetch", fetchMock);

    const user = await openWidgetAndSendMessage("How much does it cost?");
    await screen.findByLabelText(/full name/i);

    await user.type(screen.getByLabelText(/full name/i), "Jane Doe");
    await user.type(screen.getByLabelText(/email/i), "not-an-email");
    await user.type(screen.getByLabelText(/phone number/i), "03001234567");
    await user.click(screen.getByRole("button", { name: /submit/i }));

    expect(
      await screen.findByText(/that email address doesn't look valid/i),
    ).toBeInTheDocument();
    // Form should still be showing, not the composer, since capture isn't complete.
    expect(screen.getByLabelText(/full name/i)).toBeInTheDocument();
  });
});
