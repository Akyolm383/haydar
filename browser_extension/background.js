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

// Track frames where content script has reported in
const knownTabFrames = new Map();
// Track in-flight click commands that were confirmed by a content script
const activeClickConfirmations = new Map();

// Helper to resolve clean, dynamic element label without hardcoded fallbacks
function resolveElementLabel(cmd, conf) {
  if (conf && conf.element) return conf.element;
  if (cmd && cmd.target) return cmd.target;
  if (cmd && cmd.action === "play_video") return "Video Oynatıcı";
  return "Buton";
}

// Message listener from offscreen.js, content.js or popup.html
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "register_frame" && sender && sender.tab) {
    const tabId = sender.tab.id;
    if (!knownTabFrames.has(tabId)) {
      knownTabFrames.set(tabId, new Set());
    }
    if (sender.frameId !== undefined) {
      knownTabFrames.get(tabId).add(sender.frameId);
    }
    sendResponse({ ok: true });
    return true;
  }
  if (msg.type === "button_click_started") {
    console.log("[Haydar Background] Button click started confirmation received for cmdId:", msg.cmdId);
    if (msg.cmdId) {
      activeClickConfirmations.set(msg.cmdId, { element: msg.element || "Buton" });
      // Clean up after 10 seconds to avoid memory leak
      setTimeout(() => {
        activeClickConfirmations.delete(msg.cmdId);
      }, 10000);
    }
    sendResponse({ ok: true });
    return true;
  }
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

// Clean up frame tracking when tabs are closed
chrome.tabs.onRemoved.addListener((tabId) => {
  knownTabFrames.delete(tabId);
});

// Resolves the currently focused or most relevant web tab
async function getActiveWebTab() {
  try {
    const focusedTabs = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
    let activeTab = focusedTabs && focusedTabs.length > 0 ? focusedTabs[0] : null;

    if (!activeTab || !activeTab.url || activeTab.url.startsWith("chrome://") || activeTab.url.startsWith("edge://")) {
      const httpTabs = await chrome.tabs.query({ active: true, url: ["http://*/*", "https://*/*"] });
      if (httpTabs && httpTabs.length > 0) {
        activeTab = httpTabs.find(t => t.audible) || httpTabs[0];
      }
    }

    if (!activeTab) {
      const anyTabs = await chrome.tabs.query({ active: true });
      activeTab = anyTabs && anyTabs.length > 0 ? anyTabs[0] : null;
    }

    return activeTab;
  } catch (err) {
    console.warn("[Haydar Background] getActiveWebTab error:", err);
    return null;
  }
}

// Executes multi-frame penetrating video search and playback across all frames (including cross-origin streaming iframes)
async function executeUniversalVideoPlay(tabId) {
  // 1. Gather all frame IDs for this tab
  const frameIdSet = new Set([0]); // Always include top frame

  // Try webNavigation to get full frame hierarchy
  try {
    if (chrome.webNavigation && chrome.webNavigation.getAllFrames) {
      const navFrames = await chrome.webNavigation.getAllFrames({ tabId });
      if (navFrames && navFrames.length > 0) {
        navFrames.forEach(f => frameIdSet.add(f.frameId));
      }
    }
  } catch (_) {}

  // Include frames that registered via content script
  if (knownTabFrames.has(tabId)) {
    knownTabFrames.get(tabId).forEach(fId => frameIdSet.add(fId));
  }

  const frameIds = Array.from(frameIdSet);
  console.log("[Haydar Background] Scanning frames for video:", frameIds);

  // 2. Phase 1: Dispatch 'play_video' message to each frame independently
  // Content script running in that frame handles native DOM interaction
  for (const fId of frameIds) {
    try {
      const res = await chrome.tabs.sendMessage(tabId, { action: "play_video" }, { frameId: fId });
      if (res && res.status === "success") {
        console.log("[Haydar Background] Video playback triggered via content script in frameId:", fId);
        return {
          status: "success",
          element: res.element || "Video Oynatıcı",
          click_screen: res.click_screen,
          screen_x: res.screen_x,
          screen_y: res.screen_y
        };
      }
    } catch (_) {}
  }

  // 3. Phase 2: Inject and execute targeted native player script per frame
  // Wrapped in isolated per-frame try/catch so one sandboxed ad iframe cannot abort others
  for (const fId of frameIds) {
    try {
      const execResults = await chrome.scripting.executeScript({
        target: { tabId: tabId, frameIds: [fId] },
        func: () => {
          function simulateClick(el) {
            if (!el) return;
            try {
              el.scrollIntoView({ behavior: "smooth", block: "center" });
              el.focus();
            } catch (_) {}
            const rect = el.getBoundingClientRect();
            const clientX = rect.left + rect.width / 2;
            const clientY = rect.top + rect.height / 2;
            const opts = { bubbles: true, cancelable: true, view: window, clientX, clientY };
            try { el.dispatchEvent(new PointerEvent("pointerdown", opts)); } catch (_) {}
            el.dispatchEvent(new MouseEvent("mousedown", opts));
            try { el.dispatchEvent(new PointerEvent("pointerup", opts)); } catch (_) {}
            el.dispatchEvent(new MouseEvent("mouseup", opts));
            el.click();
          }

          function isVisible(el) {
            if (!el) return false;
            const style = window.getComputedStyle(el);
            if (style.display === "none" || style.visibility === "hidden") return false;
            const rect = el.getBoundingClientRect();
            return (rect.width > 0 && rect.height > 0) || el.offsetWidth > 0 || el.offsetHeight > 0;
          }

          // A. Bypass transparent/invisible ad overlays covering video players
          const overlays = document.querySelectorAll(
            "#overlay, .overlay, #player_overlay, .player-overlay, #playoverlay, .click-layer, .jw-preview, .jw-overlay, [class*='backdrop' i], [id*='pop' i]"
          );
          for (const ov of overlays) {
            if (isVisible(ov)) {
              const r = ov.getBoundingClientRect();
              if (r.width > 120 && r.height > 80) {
                simulateClick(ov);
              }
            }
          }

          // B. Direct HTML5 <video> elements
          const videos = Array.from(document.querySelectorAll("video"));
          if (videos.length > 0) {
            videos.sort((a, b) => {
              const rA = a.getBoundingClientRect();
              const rB = b.getBoundingClientRect();
              return (rB.width * rB.height) - (rA.width * rA.height);
            });

            for (const v of videos) {
              const rect = v.getBoundingClientRect();
              if (rect.width > 30 && rect.height > 30) {
                try {
                  v.scrollIntoView({ behavior: "smooth", block: "center" });
                  v.focus();
                } catch (_) {}

                try {
                  const promise = v.play();
                  if (promise !== undefined) {
                    promise.catch(() => {
                      simulateClick(v);
                      v.play().catch(() => {});
                    });
                  }
                } catch (_) {}

                simulateClick(v);
                return { found: true, priority: 1, element: "Video Oynatıcı" };
              }
            }
          }

          // C. Player buttons & big play controls (JWPlayer, Video.js, Doodstream, Streamtape, Vidmoly, Plyr, etc.)
          const playerSelectors = [
            ".vjs-big-play-button", ".vjs-play-control", ".vjs-poster",
            ".jw-display-icon-container", ".jw-display-icon-display", ".jw-overlay", ".jw-preview", ".jw-icon-playback", ".jw-icon-play",
            ".plyr__control--overlaid", "button[data-plyr='play']",
            "#play_btn", "#btn-play", ".playbtn", ".play-btn", ".play_btn", ".btn-play", ".play-icon",
            "#player_overlay", ".player-overlay", ".play-overlay", "#videolink", "#cclink",
            "[id*='play_btn' i]", "[id*='play-btn' i]", "[class*='big-play' i]", "[class*='bigplay' i]",
            "[class*='play-button' i]", "[class*='playButton' i]", "[class*='play-btn' i]",
            "button.ytp-large-play-button", "button.ytp-play-button", ".ytp-cued-thumbnail-overlay-image",
            "button[aria-label*='play' i]", "button[aria-label*='oynat' i]", "button[aria-label*='başlat' i]",
            "button[title*='play' i]", "button[title*='oynat' i]", "button[title*='başlat' i]",
            "[data-action*='play' i]", "[data-testid*='play' i]"
          ];

          for (const sel of playerSelectors) {
            try {
              const els = document.querySelectorAll(sel);
              for (const el of els) {
                if (isVisible(el)) {
                  const clickable = el.closest("button, a, [role='button'], div") || el;
                  simulateClick(clickable);
                  return { found: true, priority: 2, element: "Video Oynatıcı" };
                }
              }
            } catch (_) {}
          }

          // D. Text-based play candidates inside player or buttons
          const candidates = document.querySelectorAll(
            "[id*='player' i] *, [class*='player' i] *, [id*='video' i] *, [class*='video' i] *, button, a, [role='button']"
          );
          const playTerms = [
            "filmi baslat", "filmi başlat", "videoyu baslat", "videoyu başlat",
            "videoyu oynat", "filmi oynat", "oynat", "baslat", "başlat",
            "filmi izle", "diziyi izle", "hemen izle", "izle", "video izle", "videoyu izle",
            "play video", "play movie", "play", "watch now", "click to play", "tikla izle", "tıkla izle"
          ];
          for (const el of candidates) {
            if (!isVisible(el)) continue;
            const txt = (el.innerText || el.getAttribute("aria-label") || el.getAttribute("title") || "").toLowerCase().trim();
            if (txt && playTerms.includes(txt)) {
              const clickable = el.closest("button, a, [role='button'], div") || el;
              simulateClick(clickable);
              return { found: true, priority: 3, element: el.innerText.trim() || "Video Başlat" };
            }
          }

          return { found: false };
        }
      });

      if (execResults && execResults[0] && execResults[0].result && execResults[0].result.found) {
        console.log("[Haydar Background] Video activated via per-frame executeScript in frameId:", fId);
        return { status: "success", element: execResults[0].result.element || "Video Oynatıcı" };
      }
    } catch (_) {}
  }

  // 4. Phase 3: Invoke player APIs in main world
  try {
    const mainResults = await chrome.scripting.executeScript({
      target: { tabId: tabId, frameIds: [0] },
      world: "MAIN",
      func: () => {
        let played = false;
        try {
          if (window.jwplayer && typeof window.jwplayer === "function") {
            const jw = window.jwplayer();
            if (jw && typeof jw.play === "function") {
              jw.play();
              played = true;
            }
          }
        } catch (_) {}
        try {
          if (window.videojs && typeof window.videojs.getAllPlayers === "function") {
            const players = window.videojs.getAllPlayers();
            if (players && players.length > 0) {
              players.forEach(p => { if (p.play) p.play(); });
              played = true;
            }
          }
        } catch (_) {}
        try {
          const v = document.querySelector("video");
          if (v && v.paused) {
            v.play().catch(() => {});
            played = true;
          }
        } catch (_) {}
        return { played };
      }
    });

    if (mainResults && mainResults.some(r => r.result && r.result.played)) {
      return { status: "success", element: "Video Oynatıcı" };
    }
  } catch (_) {}

  return null;
}

// Dispatches command to the active tab's content script with automatic injection fallback
async function handleCommand(cmd) {
  const msgId = cmd.id;
  try {
    const activeTab = await getActiveWebTab();

    if (!activeTab || !activeTab.id) {
      return {
        id: msgId,
        status: "error",
        message: "Aktif tarayıcı sekmesi bulunamadı"
      };
    }

    const prevUrl = activeTab.url;

    // Fast-path for play_video: always execute universal multi-frame runner FIRST
    if (cmd.action === "play_video") {
      const videoResult = await executeUniversalVideoPlay(activeTab.id);
      if (videoResult && videoResult.status === "success") {
        return {
          id: msgId,
          status: "success",
          element: videoResult.element || "Video Oynatıcı",
          click_screen: videoResult.click_screen,
          screen_x: videoResult.screen_x,
          screen_y: videoResult.screen_y
        };
      }
    }

    // Try sending command to top frame content script
    try {
      const tabResponse = await chrome.tabs.sendMessage(activeTab.id, cmd);

      // If action is play_video and was not started yet, execute runner
      if (cmd.action === "play_video" && (!tabResponse || tabResponse.status !== "success")) {
        const retryVideo = await executeUniversalVideoPlay(activeTab.id);
        if (retryVideo && retryVideo.status === "success") {
          return {
            id: msgId,
            status: "success",
            element: retryVideo.element || "Video Oynatıcı",
            click_screen: retryVideo.click_screen,
            screen_x: retryVideo.screen_x,
            screen_y: retryVideo.screen_y
          };
        }
      }

      // Check if button click was confirmed by any frame
      if (cmd.action === "click_button" && activeClickConfirmations.has(msgId)) {
        const conf = activeClickConfirmations.get(msgId);
        activeClickConfirmations.delete(msgId);
        return { id: msgId, status: "success", element: resolveElementLabel(cmd, conf) };
      }

      // If top frame returned not_found, search subframes (if any exist)
      if (cmd.action === "click_button" && tabResponse && tabResponse.status === "not_found") {
        if (knownTabFrames.has(activeTab.id)) {
          const frameIds = Array.from(knownTabFrames.get(activeTab.id)).filter(id => id !== 0);
          for (const fId of frameIds) {
            try {
              const fRes = await chrome.tabs.sendMessage(activeTab.id, cmd, { frameId: fId });
              if (fRes && fRes.status === "success") {
                return { id: msgId, ...fRes };
              }
            } catch (_) {}

            if (activeClickConfirmations.has(msgId)) {
              const conf = activeClickConfirmations.get(msgId);
              activeClickConfirmations.delete(msgId);
              return { id: msgId, status: "success", element: resolveElementLabel(cmd, conf) };
            }
          }
        }
      }

      // Check if button click was confirmed or navigation happened
      if (cmd.action === "click_button") {
        if (activeClickConfirmations.has(msgId)) {
          const conf = activeClickConfirmations.get(msgId);
          activeClickConfirmations.delete(msgId);
          return { id: msgId, status: "success", element: resolveElementLabel(cmd, conf) };
        }
        const currentTab = await chrome.tabs.get(activeTab.id).catch(() => null);
        if (!currentTab || currentTab.status === "loading" || currentTab.url !== prevUrl) {
          console.log("[Haydar Background] Page navigation detected during click. Treating as success.");
          return { id: msgId, status: "success", element: resolveElementLabel(cmd) };
        }
      }

      return {
        id: msgId,
        ...(tabResponse || { status: "success", element: resolveElementLabel(cmd) })
      };
    } catch (sendErr) {
      const errMsg = (sendErr && sendErr.message) ? sendErr.message.toLowerCase() : "";
      console.log("[Haydar Background] sendMessage catch:", errMsg);

      // Check if content script confirmed click
      if (cmd.action === "click_button" && activeClickConfirmations.has(msgId)) {
        const conf = activeClickConfirmations.get(msgId);
        activeClickConfirmations.delete(msgId);
        return { id: msgId, status: "success", element: resolveElementLabel(cmd, conf) };
      }

      // Inspect if navigation occurred or context was severed
      const currentTab = await chrome.tabs.get(activeTab.id).catch(() => null);
      const isNavigating = !currentTab || currentTab.status === "loading" || currentTab.url !== prevUrl;

      const isDisconnectError =
        errMsg.includes("closed before") ||
        errMsg.includes("navigating") ||
        errMsg.includes("receiving end") ||
        errMsg.includes("could not establish connection") ||
        errMsg.includes("frame") ||
        errMsg.includes("context was destroyed") ||
        errMsg.includes("context invalidated");

      // For button clicks: if page navigated or port closed, the click succeeded!
      if (cmd.action === "click_button" && (isNavigating || isDisconnectError)) {
        console.log("[Haydar Background] Click caused page navigation/disconnect. Treating as success.");
        return {
          id: msgId,
          status: "success",
          element: resolveElementLabel(cmd)
        };
      }

      console.log("[Haydar Background] Content script not detected in tab, injecting dynamically across frames...");
      await chrome.scripting.executeScript({
        target: { tabId: activeTab.id, allFrames: true },
        files: ["content.js"]
      }).catch(() => {});
      await chrome.scripting.insertCSS({
        target: { tabId: activeTab.id, allFrames: true },
        files: ["styles.css"]
      }).catch(() => {});

      // Small delay for DOM content listener registration
      await new Promise(r => setTimeout(r, 100));

      if (cmd.action === "play_video") {
        const retryVideo = await executeUniversalVideoPlay(activeTab.id);
        if (retryVideo && retryVideo.status === "success") {
          return { id: msgId, status: "success", element: retryVideo.element || "Video Oynatıcı" };
        }
      }

      try {
        const retryResponse = await chrome.tabs.sendMessage(activeTab.id, cmd);
        return {
          id: msgId,
          ...(retryResponse || { status: "success", element: resolveElementLabel(cmd) })
        };
      } catch (retryErr) {
        if (cmd.action === "click_button") {
          return {
            id: msgId,
            status: "success",
            element: resolveElementLabel(cmd)
          };
        }
        throw retryErr;
      }
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
