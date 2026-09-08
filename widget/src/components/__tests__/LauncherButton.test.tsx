import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { LauncherButton } from "../LauncherButton";

describe("LauncherButton", () => {
  it("shows the closed (chat bubble) state by default and calls onClick when pressed", async () => {
    const onClick = vi.fn();
    render(<LauncherButton isOpen={false} onClick={onClick} />);

    const button = screen.getByRole("button", { name: /open chat/i });
    expect(button).toBeInTheDocument();

    await userEvent.click(button);
    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it("shows the open (close/X) state and correct label when isOpen is true", () => {
    render(<LauncherButton isOpen={true} onClick={vi.fn()} />);
    expect(
      screen.getByRole("button", { name: /close chat/i }),
    ).toBeInTheDocument();
  });
});
