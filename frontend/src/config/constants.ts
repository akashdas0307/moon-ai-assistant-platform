/**
 * Application-wide constants
 */

// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const WEBSOCKET_URL = import.meta.env.VITE_WEBSOCKET_URL || 'ws://localhost:8000/ws';

// WebSocket Configuration
export const WEBSOCKET_RECONNECT_INTERVAL = 3000; // 3 seconds
export const WEBSOCKET_MAX_RECONNECT_ATTEMPTS = 5;

// UI Configuration
export const MESSAGE_TYPING_DELAY = 1500; // ms
export const AUTO_SCROLL_THRESHOLD = 100; // px from bottom
