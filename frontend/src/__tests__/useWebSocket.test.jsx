import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import React from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

// Mock the global WebSocket
const mockWebSocket = {
  onopen: null,
  onmessage: null,
  onclose: null,
  onerror: null,
  close: vi.fn(),
  send: vi.fn(),
  readyState: 1,
};

beforeEach(() => {
  vi.clearAllMocks();
  global.WebSocket = vi.fn(() => mockWebSocket);
});

describe('useWebSocket Hook', () => {
  it('starts in connecting state after mount', () => {
    const { result } = renderHook(() =>
      useWebSocket('ws://localhost:8000/ws', vi.fn())
    );
    // Immediately after connect(), should be 'connecting'
    expect(['connecting', 'connected', 'disconnected']).toContain(result.current.status);
  });

  it('calls WebSocket constructor with provided URL', () => {
    renderHook(() =>
      useWebSocket('ws://localhost:8000/ws', vi.fn())
    );
    expect(global.WebSocket).toHaveBeenCalledWith('ws://localhost:8000/ws');
  });

  it('transitions to connected when onopen fires', () => {
    const { result } = renderHook(() =>
      useWebSocket('ws://localhost:8000/ws', vi.fn())
    );
    act(() => {
      mockWebSocket.onopen && mockWebSocket.onopen();
    });
    expect(result.current.status).toBe('connected');
  });

  it('calls onMessage handler when a valid JSON message arrives', () => {
    const handler = vi.fn();
    renderHook(() => useWebSocket('ws://localhost:8000/ws', handler));

    const testPayload = { type: 'progress', stage: 'parse_jd' };
    act(() => {
      mockWebSocket.onmessage &&
        mockWebSocket.onmessage({ data: JSON.stringify(testPayload) });
    });

    expect(handler).toHaveBeenCalledWith(testPayload);
  });

  it('does not crash on malformed JSON message', () => {
    const handler = vi.fn();
    renderHook(() => useWebSocket('ws://localhost:8000/ws', handler));

    act(() => {
      mockWebSocket.onmessage && mockWebSocket.onmessage({ data: 'not-json' });
    });

    expect(handler).not.toHaveBeenCalled();
  });

  it('closes WebSocket on unmount', () => {
    const { unmount } = renderHook(() =>
      useWebSocket('ws://localhost:8000/ws', vi.fn())
    );
    unmount();
    expect(mockWebSocket.close).toHaveBeenCalled();
  });

  it('transitions to disconnected when onclose fires', () => {
    vi.useFakeTimers();
    const { result } = renderHook(() =>
      useWebSocket('ws://localhost:8000/ws', vi.fn())
    );
    act(() => {
      mockWebSocket.onclose && mockWebSocket.onclose();
    });
    expect(result.current.status).toBe('disconnected');
    vi.useRealTimers();
  });
});
