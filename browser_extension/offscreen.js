/**
 * Haydar Web Bridge - Offscreen Document
 * Runs in a dedicated document context to maintain a 100% persistent,
 * non-sleeping WebSocket connection to Haydar desktop server.
 */

const WS_URL = "ws://127.0.0.1:8765";
let socket = null;
let isConnected = false;

function connect() {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  console.log("[Haydar Offscreen] Connecting to Haydar at", WS_URL);
  try {
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      isConnected = true;
      console.log("[Haydar Offscreen] WebSocket connected successfully!");
      chrome.runtime.sendMessage({ type: "ws_status", connected: true }).catch(() => {});
    };

    socket.onmessage = async (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("[Haydar Offscreen] Command received:", data);

        if (data.type === "ping") {
          socket.send(JSON.stringify({ type: "pong" }));
          return;
        }

        // Forward to background to execute in active tab
        chrome.runtime.sendMessage({ type: "execute_command", command: data }, (response) => {
          if (socket && socket.readyState === WebSocket.OPEN && response) {
            console.log("[Haydar Offscreen] Sending execution response back:", response);
            socket.send(JSON.stringify(response));
          }
        });
      } catch (err) {
        console.error("[Haydar Offscreen] Message parse error:", err);
      }
    };

    socket.onclose = () => {
      isConnected = false;
      console.warn("[Haydar Offscreen] WebSocket closed. Reconnecting in 2s...");
      chrome.runtime.sendMessage({ type: "ws_status", connected: false }).catch(() => {});
      setTimeout(connect, 2000);
    };

    socket.onerror = (err) => {
      console.warn("[Haydar Offscreen] WebSocket error:", err);
      try { socket.close(); } catch (_) {}
    };
  } catch (ex) {
    console.error("[Haydar Offscreen] Connection exception:", ex);
    setTimeout(connect, 2500);
  }
}

// Listen for status inquiries from popup or background
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "get_status") {
    sendResponse({ connected: isConnected && socket && socket.readyState === WebSocket.OPEN });
    return true;
  }
  if (msg.type === "force_reconnect") {
    try { if (socket) socket.close(); } catch (_) {}
    connect();
    sendResponse({ started: true });
    return true;
  }
});

// Start immediately and maintain keepalive
connect();
setInterval(() => {
  if (!socket || socket.readyState === WebSocket.CLOSED) {
    connect();
  } else if (socket.readyState === WebSocket.OPEN) {
    // Send periodic lightweight heartbeat
    try {
      socket.send(JSON.stringify({ type: "ping" }));
    } catch (_) {}
  }
}, 5000);
