/**
 * Haydar Web Bridge - Background Service Worker
 * Maintains WebSocket connection with Haydar desktop server and routes DOM commands.
 */

const WS_URL = "ws://127.0.0.1:8765";
let socket = null;
let reconnectTimer = null;

function connect() {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  console.log("[Haydar Extension] Connecting to Haydar Web Bridge at", WS_URL);
  socket = new WebSocket(WS_URL);

  socket.onopen = () => {
    console.log("[Haydar Extension] Connected to Haydar desktop successfully!");
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  };

  socket.onmessage = async (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log("[Haydar Extension] Received command:", data);

      const response = await handleCommand(data);
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(response));
      }
    } catch (err) {
      console.error("[Haydar Extension] Error handling message:", err);
    }
  };

  socket.onclose = () => {
    console.warn("[Haydar Extension] Disconnected from Haydar. Retrying in 3 seconds...");
    scheduleReconnect();
  };

  socket.onerror = (err) => {
    console.warn("[Haydar Extension] WebSocket error:", err);
    socket.close();
  };
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connect();
  }, 3000);
}

// Routes commands to the active tab's content script
async function handleCommand(cmd) {
  const msgId = cmd.id;
  try {
    const tabs = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
    let activeTab = tabs && tabs.length > 0 ? tabs[0] : null;

    if (!activeTab) {
      const anyTabs = await chrome.tabs.query({ active: true });
      activeTab = anyTabs && anyTabs.length > 0 ? anyTabs[0] : null;
    }

    if (!activeTab || !activeTab.id) {
      return {
        id: msgId,
        status: "error",
        message: "Aktif tarayıcı sekmesi bulunamadı"
      };
    }

    // Forward command to content script
    const tabResponse = await chrome.tabs.sendMessage(activeTab.id, cmd);
    return {
      id: msgId,
      ...(tabResponse || { status: "success" })
    };
  } catch (err) {
    console.warn("[Haydar Extension] Failed to communicate with content script:", err);
    return {
      id: msgId,
      status: "error",
      message: "Sekme içeriğine erişilemedi veya sayfa henüz yüklenmedi"
    };
  }
}

// Start connection on service worker activation
connect();

// Periodically keepalive check
setInterval(() => {
  if (!socket || socket.readyState === WebSocket.CLOSED) {
    connect();
  }
}, 5000);
