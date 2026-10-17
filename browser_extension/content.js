/**
 * Haydar Web Bridge - Content Script
 * Injected into web pages (and iframes) to locate elements, click buttons, and handle scrolling.
 */

// Notify background worker of frame existence for multi-frame dispatch
try {
  chrome.runtime.sendMessage({
    type: "register_frame",
    isTop: window === window.top,
    url: window.location.href,
    hasVideo: !!document.querySelector("video, [class*='player' i], [id*='player' i], [class*='play' i], iframe")
  }).catch(() => {});
} catch (_) {}

// Turkish-aware text normalization with full ASCII folding
function normalizeTr(text) {
  if (!text) return "";
  const map = {
    "İ": "i", "I": "i", "ı": "i",
    "Ğ": "g", "ğ": "g",
    "Ü": "u", "ü": "u",
    "Ş": "s", "ş": "s",
    "Ö": "o", "ö": "o",
    "Ç": "c", "ç": "c"
  };
  let str = String(text);
  for (const [k, v] of Object.entries(map)) {
    str = str.replaceAll(k, v);
  }
  return str.toLowerCase().replace(/[^\w\s\d]/g, " ").replace(/\s+/g, " ").trim();
}

function isElementVisible(el) {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (style.display === "none" || style.visibility === "hidden") {
    return false;
  }
  // Video player controls often have opacity: 0 when autohidden; don't reject on opacity
  const rect = el.getBoundingClientRect();
  return (rect.width > 0 && rect.height > 0) || el.offsetWidth > 0 || el.offsetHeight > 0;
}

// Known platform-specific selector maps (Site and player explicit hooks)
const PLATFORM_SELECTORS = {
  "sonraki bolum": [
    // YouTube
    ".ytp-next-button",
    "a.ytp-next-button",
    // Netflix
    "[data-uia='next-episode-seamless-button']",
    "[data-uia='control-next']",
    ".button-nfVideos-next",
    // Disney+ / Prime
    "[data-testid='player-next-button']",
    ".atvwebplayersdk-next-episode",
    // Standard and yerli & yabancı dizi/film siteleri
    "a[rel='next']",
    ".next-episode",
    "button.next-episode",
    "a.next-episode",
    ".sonraki-bolum",
    "a.sonraki-bolum",
    "button.sonraki-bolum",
    ".nextEpisode",
    "a.next",
    "button.next",
    "a.btn-next",
    "button.btn-next",
    "a[class*='next' i]",
    "button[class*='next' i]",
    "a[id*='next' i]",
    "button[id*='next' i]",
    "a[title*='Sonraki' i]",
    "button[title*='Sonraki' i]",
    "a[title*='sonraki' i]",
    "button[title*='sonraki' i]",
    "a[title*='Next' i]",
    "button[title*='Next' i]",
    "a[aria-label*='Sonraki' i]",
    "button[aria-label*='Sonraki' i]",
    "a[aria-label*='sonraki' i]",
    "button[aria-label*='sonraki' i]",
    "a[aria-label*='Next' i]",
    "button[aria-label*='Next' i]",
    "[data-action='next-episode']"
  ],
  "onceki bolum": [
    // Standard and yerli & yabancı dizi/film siteleri
    "a[rel='prev']",
    ".prev-episode",
    "button.prev-episode",
    "a.prev-episode",
    ".onceki-bolum",
    "a.onceki-bolum",
    "button.onceki-bolum",
    ".prevEpisode",
    "a.prev",
    "button.prev",
    "a.btn-prev",
    "button.btn-prev",
    "a[class*='prev' i]",
    "button[class*='prev' i]",
    "a[id*='prev' i]",
    "button[id*='prev' i]",
    "a[title*='Önceki' i]",
    "button[title*='Önceki' i]",
    "a[title*='onceki' i]",
    "button[title*='onceki' i]",
    "a[title*='Previous' i]",
    "button[title*='Previous' i]",
    "a[aria-label*='Önceki' i]",
    "button[aria-label*='Önceki' i]",
    "a[aria-label*='onceki' i]",
    "button[aria-label*='onceki' i]",
    "a[aria-label*='Previous' i]",
    "button[aria-label*='Previous' i]",
    "[data-action='prev-episode']",
    "[data-action='previous-episode']"
  ],
  "introyu atla": [
    // Netflix
    "[data-uia='player-skip-intro']",
    ".skip-credits",
    // Prime Video
    ".atvwebplayersdk-skipelement-button",
    // Genel video oynatıcılar
    ".skip-intro",
    "button.skip-intro",
    "a.skip-intro",
    "[aria-label*='Atla' i]",
    "[aria-label*='Skip' i]"
  ],
  "reklami gec": [
    // YouTube
    ".ytp-ad-skip-button",
    ".ytp-ad-skip-button-modern",
    ".ytp-skip-ad-button",
    ".videoAdUiSkipButton",
    // Genel oynatıcılar
    ".skip-ad",
    "button.skip-ad",
    ".ad-skip"
  ]
};

// Fallback player control icons (only checked if NO webpage link/button exists)
const PLAYER_FALLBACK_ICONS = {
  "sonraki bolum": [
    ".jw-icon-next",
    ".vjs-next-button",
    ".fa-step-forward",
    ".fa-forward"
  ],
  "onceki bolum": [
    ".jw-icon-prev",
    ".vjs-prev-button",
    ".fa-step-backward",
    ".fa-backward"
  ]
};

const SYNONYM_MAP = {
  "sonraki bolum": [
    "sonraki bolum", "sonraki", "next", "next episode", "next video",
    "sonraki video", "siradaki bolum", "siradaki", "sonraki part", "ileri",
    "sonraki bolume gec", "sonraki bolume atla", "sonraki bolumu ac",
    "siradaki bolume gec", "sonraki bolume git"
  ],
  "onceki bolum": [
    "onceki bolum", "onceki", "bir onceki bolum", "bir onceki", "previous episode",
    "previous", "prev", "geri", "onceki bolume gec", "onceki bolume git", "onceki bolume atla"
  ],
  "introyu atla": [
    "introyu atla", "intro atla", "jenerigi atla", "jenerik atla", "skip intro", "atla", "skip"
  ],
  "reklami gec": [
    "reklami gec", "reklami atla", "reklam gec", "reklam atla", "skip ad", "skip ads", "reklam"
  ]
};

function getSearchSynonyms(targetPhrase) {
  const norm = normalizeTr(targetPhrase);
  for (const [key, list] of Object.entries(SYNONYM_MAP)) {
    const normKey = normalizeTr(key);
    if (norm.includes(normKey) || normKey.includes(norm)) {
      return list.map(normalizeTr);
    }
  }
  return [norm];
}

// Universal smart DOM button locator
function findTargetButton(targetPhrase) {
  const normTarget = normalizeTr(targetPhrase);
  const synonyms = getSearchSynonyms(targetPhrase);

  function isDisabled(el) {
    if (!el) return true;
    if (el.disabled || el.getAttribute("disabled") !== null) return true;
    if (el.getAttribute("aria-disabled") === "true") return true;
    if (el.classList && (el.classList.contains("disabled") || el.classList.contains("btn-disabled"))) return true;
    return false;
  }

  // 1. YouTube specific fast path
  if (window.location.hostname.includes("youtube.com")) {
    const isNext = normTarget.includes("sonraki") || normTarget.includes("next") || normTarget.includes("bolum") || normTarget.includes("video");
    const isPrev = normTarget.includes("onceki") || normTarget.includes("prev");
    const isSkipAd = normTarget.includes("reklam") || normTarget.includes("ad");

    if (isNext) {
      // YouTube player next video button
      const ytNext = document.querySelector(".ytp-next-button, a.ytp-next-button");
      if (ytNext && !isDisabled(ytNext)) {
        return { element: ytNext, label: "Sonraki Video", isYouTube: true };
      }
      // If player control not available, first Up Next recommended video in sidebar
      const firstUpNext = document.querySelector(
        "ytd-watch-next-secondary-results-renderer #items ytd-compact-video-renderer a#thumbnail, #secondary #items ytd-compact-video-renderer a#thumbnail"
      );
      if (firstUpNext) {
        return { element: firstUpNext, label: "Sıradaki Video", isYouTube: true };
      }
    }

    if (isPrev) {
      const ytPrev = document.querySelector(".ytp-prev-button, a.ytp-prev-button");
      if (ytPrev && !isDisabled(ytPrev)) {
        return { element: ytPrev, label: "Önceki Video", isYouTube: true };
      }
    }

    if (isSkipAd) {
      const skipBtn = document.querySelector(".ytp-ad-skip-button, .ytp-ad-skip-button-modern, .ytp-skip-ad-button, .videoAdUiSkipButton");
      if (skipBtn) {
        return { element: skipBtn, label: "Reklamı Geç", isYouTube: true };
      }
    }
  }

  const candidates = document.querySelectorAll(
    "button, a, [role='button'], input[type='button'], input[type='submit'], [onclick], div[class*='btn' i], span[class*='btn' i], [tabindex]"
  );

  // 2. Exact text match on clickable elements (Highest priority for webpage episode links like 'Sonraki Bölüm')
  for (const el of candidates) {
    if (!isElementVisible(el) || isDisabled(el)) continue;

    const texts = [
      el.innerText || "",
      el.getAttribute("aria-label") || "",
      el.getAttribute("title") || "",
      el.getAttribute("value") || ""
    ];

    for (const raw of texts) {
      const norm = normalizeTr(raw);
      if (!norm) continue;

      for (const syn of synonyms) {
        if (norm === syn) {
          const clickable = el.closest("button, a, [role='button']") || el;
          return { element: clickable, label: raw.trim() || syn, isYouTube: false };
        }
      }
    }
  }

  // 3. High-priority text-contains match on <a> and <button> (e.g. 'Sonraki Bölüm (2. Bölüm)', 'Sonraki Bölüme Git')
  // This ALWAYS beats embedded player playlist icons on streaming sites!
  for (const el of candidates) {
    if (!isElementVisible(el) || isDisabled(el)) continue;

    const texts = [
      el.innerText || "",
      el.getAttribute("aria-label") || "",
      el.getAttribute("title") || ""
    ];

    for (const raw of texts) {
      const norm = normalizeTr(raw);
      if (!norm) continue;

      for (const syn of synonyms) {
        if (syn.length >= 4 && (norm.startsWith(syn) || norm.includes(syn))) {
          const clickable = el.closest("button, a, [role='button']") || el;
          return { element: clickable, label: raw.trim() || targetPhrase, isYouTube: false };
        }
      }
    }
  }

  // 4. Check known platform selectors for Netflix, Anime, Series sites (e.g. .next-episode, .sonraki-bolum, a[rel='prev'])
  for (const [key, selectors] of Object.entries(PLATFORM_SELECTORS)) {
    const normKey = normalizeTr(key);
    if (normTarget.includes(normKey) || normKey.includes(normTarget)) {
      for (const sel of selectors) {
        try {
          const els = document.querySelectorAll(sel);
          for (const el of els) {
            const clickable = el.closest("button, a, [role='button']") || el;
            if (isElementVisible(clickable) && !isDisabled(clickable)) {
              return { element: clickable, label: key, isYouTube: false };
            }
          }
        } catch (_) {}
      }
    }
  }

  // 5. Fallback player icon selectors (JWPlayer, Video.js) - ONLY if no page links found
  for (const [key, selectors] of Object.entries(PLAYER_FALLBACK_ICONS)) {
    const normKey = normalizeTr(key);
    if (normTarget.includes(normKey) || normKey.includes(normTarget)) {
      for (const sel of selectors) {
        try {
          const els = document.querySelectorAll(sel);
          for (const el of els) {
            const clickable = el.closest("button, a, [role='button']") || el;
            if (isElementVisible(clickable) && !isDisabled(clickable)) {
              return { element: clickable, label: key, isYouTube: false };
            }
          }
        } catch (_) {}
      }
    }
  }

  // 6. Substring / fuzzy text search across any candidate
  let bestMatch = null;
  let bestScore = 0;

  for (const el of candidates) {
    if (!isElementVisible(el) || isDisabled(el)) continue;

    const texts = [
      el.innerText || "",
      el.getAttribute("aria-label") || "",
      el.getAttribute("title") || "",
      el.getAttribute("value") || "",
      el.getAttribute("alt") || ""
    ];

    for (const raw of texts) {
      const norm = normalizeTr(raw);
      if (!norm) continue;

      for (const syn of synonyms) {
        if (norm.includes(syn) || syn.includes(norm)) {
          const score = Math.min(norm.length, syn.length) / Math.max(norm.length, syn.length);
          if (score > bestScore) {
            bestScore = score;
            const clickable = el.closest("button, a, [role='button']") || el;
            bestMatch = { element: clickable, label: raw.trim() || targetPhrase, isYouTube: false };
          }
        }
      }
    }
  }

  if (bestMatch && bestScore >= 0.25) {
    return bestMatch;
  }

  return null;
}

// Executes click with visual emerald pulse animation
function executeElementClick(el, label, isYouTube = false) {
  try {
    el.scrollIntoView({ behavior: "smooth", block: "center" });
  } catch (_) {}

  // Apply visual highlight
  el.classList.add("haydar-highlight-pulse");
  setTimeout(() => {
    el.classList.remove("haydar-highlight-pulse");
  }, 1200);

  // If YouTube next button, also dispatch Shift+N shortcut to trigger immediate player action
  if (isYouTube && (label.includes("Sonraki") || label.includes("Next") || label.includes("Sıradaki"))) {
    try {
      document.dispatchEvent(new KeyboardEvent("keydown", {
        key: "N",
        code: "KeyN",
        shiftKey: true,
        bubbles: true,
        cancelable: true
      }));
    } catch (_) {}
  }

  // Dispatch full mouse and click sequence
  const mouseOpts = { bubbles: true, cancelable: true, view: window };
  el.dispatchEvent(new MouseEvent("mousedown", mouseOpts));
  el.dispatchEvent(new MouseEvent("mouseup", mouseOpts));
  el.click();

  // If element is a link and page did not navigate, enforce SPA navigation
  if (el.tagName === "A" && el.href && !el.href.startsWith("javascript:")) {
    const currentUrl = window.location.href;
    setTimeout(() => {
      if (window.location.href === currentUrl) {
        window.location.href = el.href;
      }
    }, 180);
  }

  return { status: "success", element: label };
}

function highlightElement(el) {
  if (!el) return;
  el.classList.add("haydar-highlight-pulse");
  setTimeout(() => {
    el.classList.remove("haydar-highlight-pulse");
  }, 1200);
}

function simulateUserClick(el) {
  if (!el) return;
  try {
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.focus();
  } catch (_) {}

  highlightElement(el);

  const rect = el.getBoundingClientRect();
  const clientX = rect.left + rect.width / 2;
  const clientY = rect.top + rect.height / 2;
  const opts = { bubbles: true, cancelable: true, view: window, clientX, clientY };

  try {
    el.dispatchEvent(new PointerEvent("pointerdown", opts));
  } catch (_) {}
  el.dispatchEvent(new MouseEvent("mousedown", opts));
  try {
    el.dispatchEvent(new PointerEvent("pointerup", opts));
  } catch (_) {}
  el.dispatchEvent(new MouseEvent("mouseup", opts));
  el.click();
}

function getElementScreenCoords(el) {
  if (!el) return null;
  const rect = el.getBoundingClientRect();
  const titleBarHeight = Math.max(0, window.outerHeight - window.innerHeight);
  const borderWidth = Math.max(0, (window.outerWidth - window.innerWidth) / 2);
  const screenX = Math.round(window.screenLeft + borderWidth + rect.left + rect.width / 2);
  const screenY = Math.round(window.screenTop + titleBarHeight + rect.top + rect.height / 2);
  return { x: screenX, y: screenY };
}

// Universal Video Finder and Player Engine
function findAndPlayVideo() {
  // 1. Direct HTML5 <video> elements
  const videos = Array.from(document.querySelectorAll("video"));
  if (videos.length > 0) {
    // Sort by visible area descending
    videos.sort((a, b) => {
      const rA = a.getBoundingClientRect();
      const rB = b.getBoundingClientRect();
      return (rB.width * rB.height) - (rA.width * rA.height);
    });

    for (const v of videos) {
      const rect = v.getBoundingClientRect();
      if (rect.width > 40 && rect.height > 40) {
        try {
          v.scrollIntoView({ behavior: "smooth", block: "center" });
          v.focus();
        } catch (_) {}

        highlightElement(v);

        if (v.paused) {
          const promise = v.play();
          if (promise !== undefined) {
            promise.catch(() => {
              simulateUserClick(v);
            });
          }
        } else {
          simulateUserClick(v);
        }
        const coords = getElementScreenCoords(v);
        return {
          status: "success",
          element: "Video Oynatıcı",
          click_screen: true,
          screen_x: coords ? coords.x : null,
          screen_y: coords ? coords.y : null
        };
      }
    }
  }

  // 2. Common player overlay buttons and big play icons
  const playerSelectors = [
    // Video.js
    ".vjs-big-play-button",
    ".vjs-play-control",
    // JW Player
    ".jw-display-icon-container",
    ".jw-display-icon-display",
    ".jw-overlay",
    ".jw-preview",
    // Plyr & Flowplayer
    ".plyr__control--overlaid",
    "button[data-plyr='play']",
    ".dmp_PlayButton",
    ".fp-play",
    ".fp-ui",
    // YouTube
    "button.ytp-large-play-button",
    "button.ytp-play-button",
    ".ytp-cued-thumbnail-overlay-image",
    // Generic player overlays and buttons
    "[class*='play-button' i]",
    "[class*='play_button' i]",
    "[class*='playButton' i]",
    "[class*='play-btn' i]",
    "[class*='play_btn' i]",
    "[class*='btn-play' i]",
    "[class*='big-play' i]",
    "[class*='bigplay' i]",
    "[class*='play-icon' i]",
    "[class*='player-cover' i]",
    "[class*='video-cover' i]",
    "[class*='player-poster' i]",
    "[class*='video-poster' i]",
    "[class*='fake-player' i]",
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
        if (isElementVisible(el)) {
          const clickable = el.closest("button, a, [role='button'], div") || el;
          simulateUserClick(clickable);
          const coords = getElementScreenCoords(clickable);
          return {
            status: "success",
            element: "Video Oynatıcı",
            click_screen: true,
            screen_x: coords ? coords.x : null,
            screen_y: coords ? coords.y : null
          };
        }
      }
    } catch (_) {}
  }

  // 3. Search for elements containing play-related text inside player containers or buttons
  const textCandidates = document.querySelectorAll(
    "[id*='player' i] *, [class*='player' i] *, [id*='video' i] *, [class*='video' i] *, button, a, [role='button']"
  );
  const playTerms = [
    "filmi baslat", "filmi başlat", "videoyu baslat", "videoyu başlat",
    "videoyu oynat", "filmi oynat", "oynat", "baslat", "başlat",
    "filmi izle", "diziyi izle", "hemen izle", "izle", "video izle", "videoyu izle",
    "play video", "play movie", "play", "watch now", "click to play", "tikla izle", "tıkla izle"
  ];

  for (const el of textCandidates) {
    if (!isElementVisible(el)) continue;
    const txt = normalizeTr(el.innerText || el.getAttribute("aria-label") || el.getAttribute("title") || "");
    if (txt && playTerms.includes(txt)) {
      const clickable = el.closest("button, a, [role='button'], div") || el;
      simulateUserClick(clickable);
      const coords = getElementScreenCoords(clickable);
      return {
        status: "success",
        element: el.innerText.trim() || "Video Başlat",
        click_screen: true,
        screen_x: coords ? coords.x : null,
        screen_y: coords ? coords.y : null
      };
    }
  }

  // 4. Video player iframes (Doodstream, Vidmoly, Streamtape, Fembed, Supervideo, Embed etc.)
  const iframes = Array.from(document.querySelectorAll("iframe"));
  for (const iframe of iframes) {
    const src = (iframe.src || "").toLowerCase();
    const id = (iframe.id || "").toLowerCase();
    const cls = (iframe.className || "").toLowerCase();
    const isPlayer =
      src.includes("embed") ||
      src.includes("player") ||
      src.includes("video") ||
      src.includes("stream") ||
      src.includes("moly") ||
      src.includes("dood") ||
      id.includes("player") ||
      cls.includes("player");

    if (isPlayer && isElementVisible(iframe)) {
      try {
        iframe.scrollIntoView({ behavior: "smooth", block: "center" });
        iframe.focus();
      } catch (_) {}

      // Try same-origin content inspection
      try {
        if (iframe.contentDocument) {
          const innerV = iframe.contentDocument.querySelector("video");
          if (innerV) {
            innerV.play().catch(() => simulateUserClick(innerV));
            highlightElement(iframe);
            const coords = getElementScreenCoords(iframe);
            return {
              status: "success",
              element: "Video Oynatıcı",
              click_screen: true,
              screen_x: coords ? coords.x : null,
              screen_y: coords ? coords.y : null
            };
          }
          const innerBtn = iframe.contentDocument.querySelector(".vjs-big-play-button, .jw-display-icon-container, [class*='play' i], button");
          if (innerBtn) {
            simulateUserClick(innerBtn);
            highlightElement(iframe);
            const coords = getElementScreenCoords(iframe);
            return {
              status: "success",
              element: "Video Oynatıcı",
              click_screen: true,
              screen_x: coords ? coords.x : null,
              screen_y: coords ? coords.y : null
            };
          }
        }
      } catch (_) {}

      // Scroll, focus, and click iframe container in parent frame
      simulateUserClick(iframe);
      const coords = getElementScreenCoords(iframe);
      return {
        status: "success",
        element: "Video Oynatıcı",
        click_screen: true,
        screen_x: coords ? coords.x : null,
        screen_y: coords ? coords.y : null
      };
    }
  }

  // 5. Fallback: Player container wrapper (#player, .video-player, etc.)
  const containers = document.querySelectorAll(
    "#player, #vplayer, #video-player, #embed-player, .player-container, .video-container, .video-wrapper, [data-player]"
  );
  for (const c of containers) {
    if (isElementVisible(c)) {
      simulateUserClick(c);
      const coords = getElementScreenCoords(c);
      return {
        status: "success",
        element: "Video Oynatıcı",
        click_screen: true,
        screen_x: coords ? coords.x : null,
        screen_y: coords ? coords.y : null
      };
    }
  }

  return { status: "not_found", message: "Sayfada video oynatıcı bulunamadı" };
}

// Message listener from background.js
chrome.runtime.onMessage.addListener((cmd, sender, sendResponse) => {
  console.log("[Haydar Content] Handling command:", cmd);
  const action = cmd.action;
  const target = cmd.target || "";

  if (action === "play_video") {
    const result = findAndPlayVideo();
    sendResponse(result);
    return true;
  }

  if (action === "click_button") {
    const result = findTargetButton(target);
    if (result && result.element) {
      const clickLabel = result.label || target;

      // 1. Immediately notify background via one-way runtime message so background KNOWS a click has started
      try {
        chrome.runtime.sendMessage({
          type: "button_click_started",
          cmdId: cmd.id,
          element: clickLabel
        }).catch(() => {});
      } catch (_) {}

      // 2. Send success response immediately BEFORE navigation destroys context
      sendResponse({ status: "success", element: clickLabel });

      // 3. Execute click with 60ms delay so message has already safely left the page and reached background.js
      setTimeout(() => {
        executeElementClick(result.element, clickLabel, result.isYouTube);
      }, 60);
    } else {
      sendResponse({
        status: "not_found",
        message: `'${target}' butonu sayfada bulunamadı`
      });
    }
    return true;
  }

  if (action === "scroll_down") {
    const amount = (cmd.params && cmd.params.pixels) || window.innerHeight * 0.75;
    window.scrollBy({ top: amount, behavior: "smooth" });
    sendResponse({ status: "success", element: "Sayfa aşağı kaydırıldı" });
    return true;
  }

  if (action === "scroll_up") {
    const amount = (cmd.params && cmd.params.pixels) || window.innerHeight * 0.75;
    window.scrollBy({ top: -amount, behavior: "smooth" });
    sendResponse({ status: "success", element: "Sayfa yukarı kaydırıldı" });
    return true;
  }

  sendResponse({ status: "unknown_action", message: `Bilinmeyen eylem: ${action}` });
  return true;
});
