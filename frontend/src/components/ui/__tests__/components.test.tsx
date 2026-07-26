import { describe, it, expect, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogTrigger,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip";
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuCheckboxItem,
} from "@/components/ui/dropdown-menu";
import { Card, TagChip, EmptyState, Avatar, StatusDot } from "@/components/shared/primitives";

// ---------------------------------------------------------------------------
// Button
// ---------------------------------------------------------------------------

describe("Button", () => {
  it("renders with default text", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole("button", { name: "Click me" })).toBeInTheDocument();
  });

  it("calls onClick when clicked", async () => {
    const handler = vi.fn();
    render(<Button onClick={handler}>Submit</Button>);
    await userEvent.click(screen.getByRole("button", { name: "Submit" }));
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it("does not call onClick when disabled", async () => {
    const handler = vi.fn();
    render(
      <Button disabled onClick={handler}>
        Disabled
      </Button>,
    );
    await userEvent.click(screen.getByRole("button", { name: "Disabled" }));
    expect(handler).not.toHaveBeenCalled();
  });

  it("applies variant classes — destructive", () => {
    render(<Button variant="destructive">Delete</Button>);
    expect(screen.getByRole("button")).toHaveClass("bg-destructive");
  });

  it("applies variant classes — outline", () => {
    render(<Button variant="outline">Outline</Button>);
    expect(screen.getByRole("button")).toHaveClass("border");
  });

  it("applies size classes — sm", () => {
    render(<Button size="sm">Small</Button>);
    expect(screen.getByRole("button")).toHaveClass("h-8");
  });

  it("applies size classes — lg", () => {
    render(<Button size="lg">Large</Button>);
    expect(screen.getByRole("button")).toHaveClass("h-10");
  });

  it("forwards additional className", () => {
    render(<Button className="custom-class">Styled</Button>);
    expect(screen.getByRole("button")).toHaveClass("custom-class");
  });

  it("renders as child element when asChild is true", () => {
    render(
      <Button asChild>
        <a href="/home">Home</a>
      </Button>,
    );
    expect(screen.getByRole("link", { name: "Home" })).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Input
// ---------------------------------------------------------------------------

describe("Input", () => {
  it("renders with placeholder", () => {
    render(<Input placeholder="Enter email" />);
    expect(screen.getByPlaceholderText("Enter email")).toBeInTheDocument();
  });

  it("accepts typed text", async () => {
    render(<Input placeholder="Type here" />);
    const input = screen.getByPlaceholderText("Type here");
    await userEvent.type(input, "hello");
    expect(input).toHaveValue("hello");
  });

  it("calls onChange on each keystroke", async () => {
    const handler = vi.fn();
    render(<Input onChange={handler} placeholder="input" />);
    await userEvent.type(screen.getByPlaceholderText("input"), "ab");
    expect(handler).toHaveBeenCalledTimes(2);
  });

  it("is disabled when disabled prop is set", () => {
    render(<Input disabled placeholder="disabled" />);
    expect(screen.getByPlaceholderText("disabled")).toBeDisabled();
  });

  it("renders as password type", () => {
    render(<Input type="password" placeholder="password" />);
    expect(screen.getByPlaceholderText("password")).toHaveAttribute("type", "password");
  });

  it("forwards additional className", () => {
    render(<Input className="extra" placeholder="cls" />);
    expect(screen.getByPlaceholderText("cls")).toHaveClass("extra");
  });
});

// ---------------------------------------------------------------------------
// Badge
// ---------------------------------------------------------------------------

describe("Badge", () => {
  it("renders children", () => {
    render(<Badge>New</Badge>);
    expect(screen.getByText("New")).toBeInTheDocument();
  });

  it("applies default variant class", () => {
    render(<Badge>Default</Badge>);
    expect(screen.getByText("Default")).toHaveClass("bg-primary");
  });

  it("applies secondary variant class", () => {
    render(<Badge variant="secondary">Secondary</Badge>);
    expect(screen.getByText("Secondary")).toHaveClass("bg-secondary");
  });

  it("applies destructive variant class", () => {
    render(<Badge variant="destructive">Error</Badge>);
    expect(screen.getByText("Error")).toHaveClass("bg-destructive");
  });

  it("applies outline variant class", () => {
    render(<Badge variant="outline">Outline</Badge>);
    expect(screen.getByText("Outline")).toHaveClass("text-foreground");
  });

  it("forwards additional className", () => {
    render(<Badge className="my-badge">Tag</Badge>);
    expect(screen.getByText("Tag")).toHaveClass("my-badge");
  });
});

// ---------------------------------------------------------------------------
// Card (shared primitive)
// ---------------------------------------------------------------------------

describe("Card", () => {
  it("renders children", () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText("Card content")).toBeInTheDocument();
  });

  it("renders as article when as='article'", () => {
    render(<Card as="article">Article card</Card>);
    expect(screen.getByRole("article")).toBeInTheDocument();
  });

  it("applies interactive hover class when interactive=true", () => {
    render(<Card interactive>Interactive</Card>);
    expect(screen.getByText("Interactive").closest("div")).toHaveClass("hover-lift");
  });

  it("does not apply hover class when interactive=false", () => {
    render(<Card>Static</Card>);
    expect(screen.getByText("Static").closest("div")).not.toHaveClass("hover-lift");
  });

  it("forwards additional className", () => {
    render(<Card className="p-8">Padded</Card>);
    expect(screen.getByText("Padded").closest("div")).toHaveClass("p-8");
  });
});

// ---------------------------------------------------------------------------
// TagChip (shared primitive)
// ---------------------------------------------------------------------------

describe("TagChip", () => {
  it("renders label text", () => {
    render(<TagChip>React</TagChip>);
    expect(screen.getByText("React")).toBeInTheDocument();
  });

  it("forwards additional className", () => {
    render(<TagChip className="text-red-500">Python</TagChip>);
    expect(screen.getByText("Python")).toHaveClass("text-red-500");
  });
});

// ---------------------------------------------------------------------------
// EmptyState (shared primitive)
// ---------------------------------------------------------------------------

describe("EmptyState", () => {
  it("renders title", () => {
    render(<EmptyState title="Nothing here" />);
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
  });

  it("renders optional description", () => {
    render(<EmptyState title="Empty" desc="Try adding something." />);
    expect(screen.getByText("Try adding something.")).toBeInTheDocument();
  });

  it("renders optional action", () => {
    render(<EmptyState title="Empty" action={<button>Add item</button>} />);
    expect(screen.getByRole("button", { name: "Add item" })).toBeInTheDocument();
  });

  it("does not render desc when not provided", () => {
    render(<EmptyState title="Empty" />);
    expect(screen.queryByText("Try adding something.")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// StatusDot (shared primitive)
// ---------------------------------------------------------------------------

describe("StatusDot", () => {
  it("renders online ping animation when online=true", () => {
    const { container } = render(<StatusDot online />);
    expect(container.querySelector(".animate-ping")).toBeInTheDocument();
  });

  it("does not render ping when online=false", () => {
    const { container } = render(<StatusDot online={false} />);
    expect(container.querySelector(".animate-ping")).not.toBeInTheDocument();
  });

  it("applies success color when online", () => {
    const { container } = render(<StatusDot online />);
    const dot = container.querySelector(".bg-success");
    expect(dot).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Avatar (shared primitive)
// ---------------------------------------------------------------------------

describe("Avatar", () => {
  it("renders image with correct src and alt", () => {
    render(<Avatar src="https://example.com/avatar.png" alt="Jane Doe" />);
    const img = screen.getByAltText("Jane Doe");
    expect(img).toBeInTheDocument();
    expect(img).toHaveAttribute("src", "https://example.com/avatar.png");
  });

  it("shows StatusDot when online prop is provided", () => {
    const { container } = render(<Avatar src="https://example.com/avatar.png" alt="User" online />);
    expect(container.querySelector(".animate-ping")).toBeInTheDocument();
  });

  it("does not render StatusDot when online is undefined", () => {
    const { container } = render(<Avatar src="https://example.com/avatar.png" alt="User" />);
    expect(container.querySelector(".animate-ping")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Dialog (modal)
// ---------------------------------------------------------------------------

describe("Dialog", () => {
  it("does not show content when closed", () => {
    render(
      <Dialog>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogTitle>My Dialog</DialogTitle>
          <DialogDescription>Dialog body text</DialogDescription>
        </DialogContent>
      </Dialog>,
    );
    expect(screen.queryByText("My Dialog")).not.toBeInTheDocument();
  });

  it("shows content after trigger click", async () => {
    render(
      <Dialog>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogTitle>My Dialog</DialogTitle>
          <DialogDescription>Dialog body text</DialogDescription>
        </DialogContent>
      </Dialog>,
    );
    await userEvent.click(screen.getByText("Open"));
    expect(await screen.findByText("My Dialog")).toBeInTheDocument();
    expect(screen.getByText("Dialog body text")).toBeInTheDocument();
  });

  it("closes when the close button is clicked", async () => {
    render(
      <Dialog>
        <DialogTrigger>Open</DialogTrigger>
        <DialogContent>
          <DialogTitle>Closeable</DialogTitle>
          <DialogDescription>Some description</DialogDescription>
        </DialogContent>
      </Dialog>,
    );
    await userEvent.click(screen.getByText("Open"));
    await screen.findByText("Closeable");
    await userEvent.click(screen.getByRole("button", { name: /close/i }));
    await waitFor(() => expect(screen.queryByText("Closeable")).not.toBeInTheDocument());
  });

  it("renders with controlled open state", () => {
    render(
      <Dialog open>
        <DialogContent>
          <DialogTitle>Controlled</DialogTitle>
          <DialogDescription>Always open</DialogDescription>
        </DialogContent>
      </Dialog>,
    );
    expect(screen.getByText("Controlled")).toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// Tooltip
// ---------------------------------------------------------------------------

describe("Tooltip", () => {
  it("shows tooltip content on hover", async () => {
    render(
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger>Hover me</TooltipTrigger>
          <TooltipContent>Tooltip text</TooltipContent>
        </Tooltip>
      </TooltipProvider>,
    );
    await userEvent.hover(screen.getByText("Hover me"));
    expect(await screen.findByRole("tooltip")).toBeInTheDocument();
    expect(screen.getByRole("tooltip")).toHaveTextContent("Tooltip text");
  });

  it("hides tooltip content when not hovered", () => {
    render(
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger>Hover me</TooltipTrigger>
          <TooltipContent>Hidden tooltip</TooltipContent>
        </Tooltip>
      </TooltipProvider>,
    );
    expect(screen.queryByText("Hidden tooltip")).not.toBeInTheDocument();
  });
});

// ---------------------------------------------------------------------------
// DropdownMenu
// ---------------------------------------------------------------------------

describe("DropdownMenu", () => {
  it("does not show items when closed", () => {
    render(
      <DropdownMenu>
        <DropdownMenuTrigger>Open menu</DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem>Profile</DropdownMenuItem>
          <DropdownMenuItem>Settings</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>,
    );
    expect(screen.queryByText("Profile")).not.toBeInTheDocument();
  });

  it("shows items after trigger click", async () => {
    render(
      <DropdownMenu>
        <DropdownMenuTrigger>Open menu</DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem>Profile</DropdownMenuItem>
          <DropdownMenuItem>Settings</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>,
    );
    await userEvent.click(screen.getByText("Open menu"));
    expect(await screen.findByText("Profile")).toBeInTheDocument();
    expect(screen.getByText("Settings")).toBeInTheDocument();
  });

  it("calls onClick when a menu item is clicked", async () => {
    const handler = vi.fn();
    render(
      <DropdownMenu>
        <DropdownMenuTrigger>Open menu</DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem onClick={handler}>Delete</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>,
    );
    await userEvent.click(screen.getByText("Open menu"));
    await userEvent.click(await screen.findByText("Delete"));
    expect(handler).toHaveBeenCalledTimes(1);
  });

  it("renders separator between items", async () => {
    render(
      <DropdownMenu>
        <DropdownMenuTrigger>Open menu</DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem>Item A</DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem>Item B</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>,
    );
    await userEvent.click(screen.getByText("Open menu"));
    await screen.findByText("Item A");
    expect(document.querySelector(".bg-muted")).toBeInTheDocument();
  });

  it("renders checkbox item and toggles checked state", async () => {
    const handler = vi.fn();
    render(
      <DropdownMenu>
        <DropdownMenuTrigger>Open menu</DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuCheckboxItem checked={false} onCheckedChange={handler}>
            Notifications
          </DropdownMenuCheckboxItem>
        </DropdownMenuContent>
      </DropdownMenu>,
    );
    await userEvent.click(screen.getByText("Open menu"));
    await userEvent.click(await screen.findByText("Notifications"));
    expect(handler).toHaveBeenCalledWith(true);
  });
});
