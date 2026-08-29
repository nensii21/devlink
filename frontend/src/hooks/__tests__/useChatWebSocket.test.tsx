import { renderHook, act } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useChatWebSocket, getReconnectDelay } from "../useChatWebSocket";

class FakeWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  static instances: FakeWebSocket[] = [];
  static throwOnNextConstruct = false;

  readyState = FakeWebSocket.CONNECTING;
  sent: string[] = [];
  closeCalls = 0;

  onopen: (() => void) | null = null;
  onmessage: ((e: { data: string }) => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;

  constructor(public url: string) {
    if (FakeWebSocket.throwOnNextConstruct) {
      FakeWebSocket.throwOnNextConstruct = false;
      throw new Error("cannot construct");
    }
    FakeWebSocket.instances.push(this);
  }

  send(data: string) {
    this.sent.push(data);
  }

  close() {
    this.closeCalls += 1;
    const wasOpen = this.readyState !== FakeWebSocket.CLOSED;
    this.readyState = FakeWebSocket.CLOSED;
    if (wasOpen) this.onclose?.();
  }

  open() {
    this.readyState = FakeWebSocket.OPEN;
    this.onopen?.();
  }

  drop() {
    this.readyState = FakeWebSocket.CLOSED;
    this.onclose?.();
  }

  deliver(payload: unknown) {
    this.onmessage?.({ data: JSON.stringify(payload) });
  }

  get messages(): Array<Record<string, unknown>> {
    return this.sent.map((raw) => JSON.parse(raw));
  }

  static get latest(): FakeWebSocket {
    return FakeWebSocket.instances[FakeWebSocket.instances.length - 1];
  }

  static reset() {
    FakeWebSocket.instances = [];
    FakeWebSocket.throwOnNextConstruct = false;
  }
}

describe("useChatWebSocket", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    FakeWebSocket.reset();
    vi.stubGlobal("WebSocket", FakeWebSocket);
    localStorage.clear();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
    localStorage.clear();
  });

  it("calculates exponential backoff delays with jitter ceiling", () => {
    vi.spyOn(Math, "random").mockReturnValue(1);
    expect(getReconnectDelay(0)).toBe(1000);
    expect(getReconnectDelay(1)).toBe(2000);
    expect(getReconnectDelay(2)).toBe(4000);
    expect(getReconnectDelay(10)).toBe(30000); // capped at 30s
    vi.restoreAllMocks();
  });

  it("connects and joins the room on open", () => {
    const onNewMessage = vi.fn();
    const { result } = renderHook(() => useChatWebSocket("conv-123", "user-1", onNewMessage));

    expect(FakeWebSocket.instances.length).toBe(1);
    const socket = FakeWebSocket.latest;
    expect(socket.url).toContain("/api/v1/ws/collab");
    expect(result.current.isConnected).toBe(false);

    act(() => {
      socket.open();
    });

    expect(result.current.isConnected).toBe(true);
    expect(socket.messages).toEqual([{ type: "chat.join", conversation_id: "conv-123" }]);
  });

  it("does not connect if conversationId is empty", () => {
    const onNewMessage = vi.fn();
    const { result } = renderHook(() => useChatWebSocket("", "user-1", onNewMessage));

    expect(FakeWebSocket.instances.length).toBe(0);
    expect(result.current.isConnected).toBe(false);
  });

  it("delivers new chat messages for the active conversation", () => {
    const onNewMessage = vi.fn();
    renderHook(() => useChatWebSocket("conv-123", "user-1", onNewMessage));

    const socket = FakeWebSocket.latest;
    act(() => {
      socket.open();
    });

    const msgEvent = {
      type: "chat.message.new",
      conversation_id: "conv-123",
      content: "Hello world",
    };

    act(() => {
      socket.deliver(msgEvent);
    });

    expect(onNewMessage).toHaveBeenCalledTimes(1);
    expect(onNewMessage).toHaveBeenCalledWith(msgEvent);

    // Message for different conversation is ignored
    act(() => {
      socket.deliver({
        type: "chat.message.new",
        conversation_id: "other-conv",
        content: "Wrong room",
      });
    });

    expect(onNewMessage).toHaveBeenCalledTimes(1);
  });

  it("tracks typing users and clears after 3 seconds", () => {
    const onNewMessage = vi.fn();
    const { result } = renderHook(() => useChatWebSocket("conv-123", "user-1", onNewMessage));

    const socket = FakeWebSocket.latest;
    act(() => {
      socket.open();
    });

    // Typing event from another user
    act(() => {
      socket.deliver({
        type: "chat.typing",
        conversation_id: "conv-123",
        user_id: "user-2",
      });
    });

    expect(result.current.typingUsers).toEqual(["user-2"]);

    // Own typing event is ignored
    act(() => {
      socket.deliver({
        type: "chat.typing",
        conversation_id: "conv-123",
        user_id: "user-1",
      });
    });

    expect(result.current.typingUsers).toEqual(["user-2"]);

    // Advance time past 3 seconds
    act(() => {
      vi.advanceTimersByTime(3000);
    });

    expect(result.current.typingUsers).toEqual([]);
  });

  it("sends leave and closes socket on unmount without triggering reconnect", () => {
    const onNewMessage = vi.fn();
    const { unmount } = renderHook(() => useChatWebSocket("conv-123", "user-1", onNewMessage));

    const socket = FakeWebSocket.latest;
    act(() => {
      socket.open();
    });

    unmount();

    expect(socket.messages).toEqual([
      { type: "chat.join", conversation_id: "conv-123" },
      { type: "chat.leave", conversation_id: "conv-123" },
    ]);
    expect(socket.closeCalls).toBe(1);

    // Advancing timers should not create any new socket
    act(() => {
      vi.advanceTimersByTime(10000);
    });

    expect(FakeWebSocket.instances.length).toBe(1);
  });

  it("properly tears down previous socket when rapidly switching conversations", () => {
    const onNewMessage = vi.fn();
    let convId = "conv-1";
    const { rerender } = renderHook(() => useChatWebSocket(convId, "user-1", onNewMessage));

    expect(FakeWebSocket.instances.length).toBe(1);
    const socket1 = FakeWebSocket.instances[0];

    // Switch rapidly to conv-2 before socket1 opens
    convId = "conv-2";
    rerender();

    expect(FakeWebSocket.instances.length).toBe(2);
    const socket2 = FakeWebSocket.instances[1];

    // Stale socket1 now fires open / message -- should be safely ignored and not corrupt state
    act(() => {
      socket1.open();
      socket1.deliver({
        type: "chat.message.new",
        conversation_id: "conv-1",
        content: "Stale message",
      });
    });

    expect(onNewMessage).not.toHaveBeenCalled();

    // Now open socket2 and deliver message
    act(() => {
      socket2.open();
      socket2.deliver({
        type: "chat.message.new",
        conversation_id: "conv-2",
        content: "Valid message",
      });
    });

    expect(onNewMessage).toHaveBeenCalledTimes(1);
    expect(onNewMessage).toHaveBeenCalledWith({
      type: "chat.message.new",
      conversation_id: "conv-2",
      content: "Valid message",
    });
  });

  it("reconnects with backoff when socket drops unexpectedly", () => {
    vi.spyOn(Math, "random").mockReturnValue(1); // max delay for deterministic timer
    const onNewMessage = vi.fn();
    const { result } = renderHook(() => useChatWebSocket("conv-123", "user-1", onNewMessage));

    const socket1 = FakeWebSocket.latest;
    act(() => {
      socket1.open();
    });
    expect(result.current.isConnected).toBe(true);

    // Socket drops
    act(() => {
      socket1.drop();
    });
    expect(result.current.isConnected).toBe(false);

    // Timer expires and triggers reconnect
    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(FakeWebSocket.instances.length).toBe(2);
    const socket2 = FakeWebSocket.latest;

    act(() => {
      socket2.open();
    });
    expect(result.current.isConnected).toBe(true);

    vi.restoreAllMocks();
  });

  it("broadcasts messages and typing when connected", () => {
    const onNewMessage = vi.fn();
    const { result } = renderHook(() => useChatWebSocket("conv-123", "user-1", onNewMessage));

    const socket = FakeWebSocket.latest;
    act(() => {
      socket.open();
    });

    act(() => {
      result.current.broadcastMessage("Hi all");
      result.current.broadcastTyping();
    });

    expect(socket.messages).toEqual([
      { type: "chat.join", conversation_id: "conv-123" },
      {
        type: "chat.message",
        conversation_id: "conv-123",
        content: "Hi all",
      },
      {
        type: "chat.typing",
        conversation_id: "conv-123",
      },
    ]);
  });
});
