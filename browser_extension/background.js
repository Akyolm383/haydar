/**
 * Haydar Web Bridge - Background Service Worker
 * Manages offscreen document lifecycle, dynamic content script injection, and active tab routing.
 */

let isOffscreenCreating = false;

async function ensureOffscreenDocument() {
  if (isOffscreenCreating) return;
  try {
    const existing = await chrome.offscreen.hasDocument();
    if (existing) return;

    isOffscreenCreating = true;
    await chrome.offscreen.createDocument({
      url: "offscreen.html",
      reasons: ["MATCH_MEDIA"],
      justification: "Maintain persistent WebSocket connection with Haydar desktop assistant"
    });
    console.log("[Haydar Background] Offscreen keepalive document created successfully");
  } catch (err) {
    console.warn("[Haydar Background] Offscreen creation notice:", err);
  } finally {
    isOffscreenCreating = false;
  }
}

// Ensure offscreen document on service worker start
ensureOffscreenDocument();

// Use alarm to periodically verify offscreen document health
chrome.alarms.create("offscreen_check", { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "offscreen_check") {
    ensureOffscreenDocument();
  }
});

// Auto-inject content script into open tabs on extension install / update
chrome.runtime.onInstalled.addListener(async () => {
  ensureOffscreenDocument();
  try {
    const tabs = await chrome.tabs.query({ url: ["http://*/*", "https://*/*"] });
    for (const tab of tabs) {
      if (!tab.id || tab.url.startsWith("chrome://") || tab.url.startsWith("edge://")) continue;
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ["content.js"]
      }).catch(() => {});
      chrome.scripting.insertCSS({
        target: { tabId: tab.id },
        files: ["styles.css"]
      }).catch(() => {});
    }
  } catch (err) {
    console.debug("[Haydar Background] Batch injection notice:", err);
  }
});

// Message listener from offscreen.js or popup.html
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "execute_command") {
    handleCommand(msg.command).then(sendResponse);
    return true; // Keep message channel open for async response
  }
  if (msg.type === "check_status") {
    chrome.runtime.sendMessage({ type: "get_status" }, (res) => {
      sendResponse(res || { connected: false });
    });
    return true;
  }
});

// Dispatches command to the active tab's content script with automatic injection fallback
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

    // Try sending command to content script
    try {
      const tabResponse = await chrome.tabs.sendMessage(activeTab.id, cmd);
      return {
        id: msgId,
        ...(tabResponse || { status: "success", element: cmd.target || "Sonraki Video" })
      };
    } catch (sendErr) {
      if (sendErr && sendErr.message && (sendErr.message.includes("closed before a response") || sendErr.message.includes("navigating"))) {
        return {
          id: msgId,
          status: "success",
          element: cmd.target || "Sonraki Video"
        };
      }
      console.log("[Haydar Background] Content script not detected in tab, injecting dynamically...");
      // Tab was opened before extension installation; inject dynamically
      await chrome.scripting.executeScript({
        target: { tabId: activeTab.id },
        files: ["content.js"]
      });
      await chrome.scripting.insertCSS({
        target: { tabId: activeTab.id },
        files: ["styles.css"]
      });

      // Small delay for DOM content listener registration
      await new Promise(r => setTimeout(r, 80));

      const retryResponse = await chrome.tabs.sendMessage(activeTab.id, cmd);
      return {
        id: msgId,
        ...(retryResponse || { status: "success" })
      };
    }
  } catch (err) {
    console.error("[Haydar Background] handleCommand failure:", err);
    return {
      id: msgId,
      status: "error",
      message: "Sekme içeriğiyle bağlantı kurulamadı veya sayfa yükleniyor"
    };
  }
}
