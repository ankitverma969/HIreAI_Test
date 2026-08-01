import { useEffect, useRef, useState, useCallback } from 'react';

export const useWebSocket = (url, onMessage) => {
  const [status, setStatus] = useState('disconnected');
  const ws = useRef(null);
  const onMessageRef = useRef(onMessage);
  const attemptRef = useRef(0);
  const reconnectTimeoutRef = useRef(null);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const connect = useCallback(() => {
    // Prevent creating duplicate connections (React StrictMode may double-invoke effects)
    if (ws.current && (ws.current.readyState === WebSocket.OPEN || ws.current.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      ws.current = new WebSocket(url);
      setStatus('connecting');

      ws.current.onopen = () => {
        setStatus('connected');
        attemptRef.current = 0;
        console.log('WebSocket progress connection opened.');
      };

      ws.current.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (onMessageRef.current) {
            onMessageRef.current(msg);
          }
        } catch (e) {
          console.error('Failed to parse WS payload:', event.data);
        }
      };

      ws.current.onclose = (ev) => {
        setStatus('disconnected');
        console.warn('WebSocket closed', { code: ev.code, reason: ev.reason });
        // Exponential backoff for reconnects
        const delay = Math.min(30000, 1000 * Math.pow(2, attemptRef.current));
        attemptRef.current += 1;
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, delay || 1000);
      };

      ws.current.onerror = (err) => {
        console.error('WebSocket connection error:', err);
        // Close socket to trigger onclose and reconnection logic
        try {
          if (ws.current && ws.current.readyState !== WebSocket.CLOSED) ws.current.close();
        } catch (e) {
          // ignore
        }
      };
    } catch (e) {
      console.error('WebSocket connection initialization failed:', e);
      setStatus('disconnected');
    }
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      if (ws.current) {
        try {
          ws.current.close();
        } catch (e) {
          // ignore
        }
      }
    };
  }, [connect]);

  return { status };
};

export default useWebSocket;
