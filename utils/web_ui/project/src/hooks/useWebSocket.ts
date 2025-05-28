import { useEffect, useRef, useState, useCallback } from 'react';

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: number;
}

export interface UseWebSocketOptions {
  url: string;
  protocols?: string | string[];
  onOpen?: (event: Event) => void;
  onClose?: (event: CloseEvent) => void;
  onError?: (event: Event) => void;
  onMessage?: (message: WebSocketMessage) => void;
  shouldReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export interface WebSocketState {
  socket: WebSocket | null;
  lastMessage: WebSocketMessage | null;
  readyState: number;
  isConnected: boolean;
  error: Event | null;
  reconnectCount: number;
}

export const useWebSocket = (options: UseWebSocketOptions): WebSocketState & {
  sendMessage: (message: any) => void;
  reconnect: () => void;
  disconnect: () => void;
} => {
  const {
    url,
    protocols,
    onOpen,
    onClose,
    onError,
    onMessage,
    shouldReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options;

  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  const [readyState, setReadyState] = useState<number>(WebSocket.CONNECTING);
  const [error, setError] = useState<Event | null>(null);
  const [reconnectCount, setReconnectCount] = useState(0);

  const reconnectTimeoutRef = useRef<number>();
  const shouldReconnectRef = useRef(shouldReconnect);
  const urlRef = useRef(url);

  // Update refs when props change
  useEffect(() => {
    shouldReconnectRef.current = shouldReconnect;
    urlRef.current = url;
  }, [shouldReconnect, url]);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(urlRef.current, protocols);
      
      ws.onopen = (event) => {
        setReadyState(WebSocket.OPEN);
        setError(null);
        setReconnectCount(0);
        onOpen?.(event);
      };

      ws.onclose = (event) => {
        setReadyState(WebSocket.CLOSED);
        onClose?.(event);

        // Attempt to reconnect if enabled and not manually closed
        if (
          shouldReconnectRef.current &&
          !event.wasClean &&
          reconnectCount < maxReconnectAttempts
        ) {
          reconnectTimeoutRef.current = window.setTimeout(() => {
            setReconnectCount(prev => prev + 1);
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = (event) => {
        setError(event);
        onError?.(event);
      };

      ws.onmessage = (event) => {
        try {
          const parsedData = JSON.parse(event.data);
          const message: WebSocketMessage = {
            type: parsedData.type || 'message',
            data: parsedData.data || parsedData,
            timestamp: Date.now(),
          };
          setLastMessage(message);
          onMessage?.(message);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      setSocket(ws);
      setReadyState(WebSocket.CONNECTING);
    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setError(err as Event);
    }
  }, [protocols, onOpen, onClose, onError, onMessage, reconnectInterval, maxReconnectAttempts, reconnectCount]);

  const sendMessage = useCallback((message: any) => {
    if (socket && readyState === WebSocket.OPEN) {
      try {
        const messageToSend = typeof message === 'string' ? message : JSON.stringify(message);
        socket.send(messageToSend);
      } catch (err) {
        console.error('Failed to send WebSocket message:', err);
      }
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
    }
  }, [socket, readyState]);

  const reconnect = useCallback(() => {
    if (socket) {
      socket.close();
    }
    setReconnectCount(0);
    connect();
  }, [socket, connect]);

  const disconnect = useCallback(() => {
    shouldReconnectRef.current = false;
    if (reconnectTimeoutRef.current) {
      window.clearTimeout(reconnectTimeoutRef.current);
    }
    if (socket) {
      socket.close(1000, 'Manual disconnect');
    }
  }, [socket]);

  // Initial connection
  useEffect(() => {
    connect();

    return () => {
      shouldReconnectRef.current = false;
      if (reconnectTimeoutRef.current) {
        window.clearTimeout(reconnectTimeoutRef.current);
      }
      if (socket) {
        socket.close();
      }
    };
  }, []);

  // Update ready state when socket changes
  useEffect(() => {
    if (socket) {
      setReadyState(socket.readyState);
    }
  }, [socket]);

  return {
    socket,
    lastMessage,
    readyState,
    isConnected: readyState === WebSocket.OPEN,
    error,
    reconnectCount,
    sendMessage,
    reconnect,
    disconnect,
  };
}; 