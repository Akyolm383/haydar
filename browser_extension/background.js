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

// Executes multi-frame penetrating video search and playback across all frames (including cross-origin streaming iframes)
async function executeUniversalVideoPlay(tabId) {
  try {
    const frameResults = await chrome.scripting.executeScript({
      target: { tabId: tabId, allFrames: true },
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

        // 1. Bypass transparent/invisible ad overlays covering video players on streaming sites
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

        // 2. Direct HTML5 <video> elements
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

              // Try play directly
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

        // 3. Player buttons & big play controls (JWPlayer, Video.js, Doodstream, Streamtape, Vidmoly, Plyr, etc.)
        const playerSelectors = [
          // Video.js
          ".vjs-big-play-button",
          ".vjs-play-control",
          ".vjs-poster",
          // JW Player
          ".jw-display-icon-container",
          ".jw-display-icon-display",
          ".jw-overlay",
          ".jw-preview",
          ".jw-icon-playback",
          ".jw-icon-play",
          // Plyr & others
          ".plyr__control--overlaid",
          "button[data-plyr='play']",
          // Doodstream / Streamtape / Vidmoly / Filelions / Voe
          "#play_btn",
          "#btn-play",
          ".playbtn",
          ".play-btn",
          ".play_btn",
          ".btn-play",
          ".play-icon",
          "#player_overlay",
          ".player-overlay",
          ".play-overlay",
          "#videolink",
          "#cclink",
          "[id*='play_btn' i]",
          "[id*='play-btn' i]",
          "[class*='big-play' i]",
          "[class*='bigplay' i]",
          "[class*='play-button' i]",
          "[class*='playButton' i]",
          "[class*='play-btn' i]",
          // YouTube
          "button.ytp-large-play-button",
          "button.ytp-play-button",
          ".ytp-cued-thumbnail-overlay-image",
          // Generic accessible play controls
          "button[aria-label*='play' i]",
          "button[aria-label*='oynat' i]",
          "button[aria-label*='başlat' i]",
          "button[title*='play' i]",
          "button[title*='oynat' i]",
          "button[title*='başlat' i]",
          "[data-action*='play' i]",
          "[data-testid*='play' i]"
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

        // 4. Text-based play candidates inside player or buttons
        const candidates = document.querySelectorAll(
          "[id*='player' i] *, [class*='player' i] *, [id*='video' i] *, [class*='video' i] *, button, a, [role='button']"
        );
        const playTerms = [
          "filmi baslat", "filmi başlat", "videoyu baslat", "videoyu başlat",
          "videoyu oynat", "filmi oynat", "oynat", "baslat", "başlat",
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

    if (frameResults && frameResults.length > 0) {
      const successFrames = frameResults
        .filter(r => r.result && r.result.found)
        .sort((a, b) => (a.result.priority || 99) - (b.result.priority || 99));

      if (successFrames.length > 0) {
        return { status: "success", element: successFrames[0].result.element || "Video Oynatıcı" };
      }
    }
  } catch (err) {
    console.warn("[Haydar Background] executeUniversalVideoPlay isolated world warning:", err);
  }

  // Fallback: Invoke player APIs in main world across all frames
  try {
    const mainResults = await chrome.scripting.executeScript({
      target: { tabId: tabId, allFrames: true },
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

    // Fast-path for play_video: always execute universal frame-penetrating runner FIRST
    if (cmd.action === "play_video") {
      const videoResult = await executeUniversalVideoPlay(activeTab.id);
      if (videoResult && videoResult.status === "success") {
        return {
          id: msgId,
          status: "success",
          element: videoResult.element || "Video Oynatıcı"
        };
      }
    }

    // Try sending command to content script
    try {
      const tabResponse = await chrome.tabs.sendMessage(activeTab.id, cmd);

      // If action is play_video and was not started yet, execute runner
      if (cmd.action === "play_video" && (!tabResponse || tabResponse.status !== "success")) {
        const retryVideo = await executeUniversalVideoPlay(activeTab.id);
        if (retryVideo && retryVideo.status === "success") {
          return { id: msgId, status: "success", element: retryVideo.element || "Video Oynatıcı" };
        }
      }

      return {
        id: msgId,
        ...(tabResponse || { status: "success", element: cmd.target || "Video Oynatıcı" })
      };
    } catch (sendErr) {
      if (sendErr && sendErr.message && (sendErr.message.includes("closed before a response") || sendErr.message.includes("navigating"))) {
        return {
          id: msgId,
          status: "success",
          element: cmd.target || "Video Oynatıcı"
        };
      }
      console.log("[Haydar Background] Content script not detected in tab, injecting dynamically...");
      // Tab was opened before extension installation; inject dynamically across all frames
      await chrome.scripting.executeScript({
        target: { tabId: activeTab.id, allFrames: true },
        files: ["content.js"]
      });
      await chrome.scripting.insertCSS({
        target: { tabId: activeTab.id, allFrames: true },
        files: ["styles.css"]
      });

      // Small delay for DOM content listener registration
      await new Promise(r => setTimeout(r, 80));

      if (cmd.action === "play_video") {
        const retryVideo = await executeUniversalVideoPlay(activeTab.id);
        if (retryVideo && retryVideo.status === "success") {
          return { id: msgId, status: "success", element: retryVideo.element || "Video Oynatıcı" };
        }
      }

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
