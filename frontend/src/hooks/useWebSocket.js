import { useEffect, useRef, useState, useCallback } from 'react';

export const useWebSocket = (url, onMessage) => {
  const [status, setStatus] = useState('disconnected');
  const ws = useRef(null);
  const onMessageRef = useRef(onMessage);

  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const connect = useCallback(() => {
    try {
      ws.current = new WebSocket(url);
      setStatus('connecting');

      ws.current.onopen = () => {
        setStatus('connected');
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

      ws.current.onclose = () => {
        setStatus('disconnected');
        console.log('WebSocket connection closed. Reconnecting in 3 seconds...');
        setTimeout(() => {
          connect();
        }, 3000);
      };

      ws.current.onerror = (err) => {
        console.error('WebSocket connection error:', err);
        if (ws.current) {
          ws.current.close();
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
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [connect]);

  return { status };
};

export default useWebSocket;
