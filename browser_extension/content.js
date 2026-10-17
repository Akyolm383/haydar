/**
 * Haydar Web Bridge - Content Script
 * Injected into web pages (and iframes) to locate elements, click buttons, and handle scrolling.
 */

// Turkish-aware text normalization
function normalizeTr(text) {
  if (!text) return "";
  const map = { "İ": "i", "I": "ı", "Ğ": "ğ", "Ü": "ü", "Ş": "ş", "Ö": "ö", "Ç": "ç" };
  let str = String(text);
  for (const [upper, lower] of Object.entries(map)) {
    str = str.replaceAll(upper, lower);
  }
  return str.toLowerCase().replace(/[^\w\s\dçğıöşü]/g, " ").replace(/\s+/g, " ").trim();
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

// Known platform-specific selector maps
const PLATFORM_SELECTORS = {
  "sonraki bölüm": [
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
    // Yerli & yabancı dizi/film siteleri & video oynatıcıları
    ".next-episode",
    "button.next-episode",
    "a.next-episode",
    ".sonraki-bolum",
    "a.sonraki-bolum",
    "button.sonraki-bolum",
    ".nextEpisode",
    "a[title*='Sonraki' i]",
    "button[title*='Sonraki' i]",
    "a[title*='Next' i]",
    "button[title*='Next' i]",
    "a[aria-label*='Sonraki' i]",
    "button[aria-label*='Sonraki' i]",
    "[data-action='next-episode']",
    ".jw-icon-next",
    ".vjs-next-button",
    ".fa-step-forward",
    ".fa-forward"
  ],
  "önceki bölüm": [
    ".prev-episode",
    "button.prev-episode",
    "a.prev-episode",
    ".onceki-bolum",
    "a.onceki-bolum",
    "button.onceki-bolum",
    "a[title*='Önceki' i]",
    "button[title*='Önceki' i]",
    "a[title*='Previous' i]",
    "button[title*='Previous' i]",
    "a[aria-label*='Önceki' i]",
    "button[aria-label*='Önceki' i]",
    ".jw-icon-prev",
    ".vjs-prev-button",
    ".fa-step-backward",
    ".fa-backward"
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
  "reklamı geç": [
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

const SYNONYM_MAP = {
  "sonraki bölüm": [
    "sonraki bölüm", "sonraki bolum", "sonraki", "next", "next episode", "next video",
    "sonraki video", "sıradaki bölüm", "siradaki bolum", "sıradaki", "sonraki part", "ileri"
  ],
  "önceki bölüm": [
    "önceki bölüm", "önceki bolum", "onceki bölüm", "onceki bolum", "önceki", "onceki",
    "bir önceki bölüm", "previous episode", "previous", "prev", "geri"
  ],
  "introyu atla": [
    "introyu atla", "intro atla", "jeneriği atla", "jenerik atla", "skip intro", "atla", "skip"
  ],
  "reklamı geç": [
    "reklamı geç", "reklamı atla", "reklam geç", "reklam atla", "skip ad", "skip ads", "reklam"
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

  // 1. YouTube specific fast path
  if (window.location.hostname.includes("youtube.com")) {
    const isNext = normTarget.includes("sonraki") || normTarget.includes("next") || normTarget.includes("bolum") || normTarget.includes("video");
    const isPrev = normTarget.includes("onceki") || normTarget.includes("prev");
    const isSkipAd = normTarget.includes("reklam") || normTarget.includes("ad");

    if (isNext) {
      // YouTube player next video button
      const ytNext = document.querySelector(".ytp-next-button, a.ytp-next-button");
      if (ytNext) {
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
      if (ytPrev) {
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

  // 2. Check known platform selectors for Netflix, Anime, Series sites
  for (const [key, selectors] of Object.entries(PLATFORM_SELECTORS)) {
    const normKey = normalizeTr(key);
    if (normTarget.includes(normKey) || normKey.includes(normTarget)) {
      for (const sel of selectors) {
        try {
          const els = document.querySelectorAll(sel);
          for (const el of els) {
            const clickable = el.closest("button, a, [role='button']") || el;
            if (isElementVisible(clickable)) {
              return { element: clickable, label: key, isYouTube: false };
            }
          }
        } catch (_) {}
      }
    }
  }

  // 3. Universal DOM search on clickable elements
  const candidates = document.querySelectorAll(
    "button, a, [role='button'], input[type='button'], input[type='submit'], [onclick], div[class*='btn' i], span[class*='btn' i], [tabindex]"
  );

  let bestMatch = null;
  let bestScore = 0;

  for (const el of candidates) {
    if (!isElementVisible(el)) continue;

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
        // Exact match
        if (norm === syn) {
          return { element: el, label: raw.trim() || syn, isYouTube: false };
        }

        // Substring / contains match
        if (norm.includes(syn) || syn.includes(norm)) {
          const score = Math.min(norm.length, syn.length) / Math.max(norm.length, syn.length);
          if (score > bestScore) {
            bestScore = score;
            bestMatch = { element: el, label: raw.trim() || targetPhrase, isYouTube: false };
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
        return { status: "success", element: "Video Oynatıcı" };
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
          return { status: "success", element: "Video Oynatıcı" };
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
    "play video", "play movie", "play", "watch now", "click to play", "tikla izle", "tıkla izle"
  ];

  for (const el of textCandidates) {
    if (!isElementVisible(el)) continue;
    const txt = normalizeTr(el.innerText || el.getAttribute("aria-label") || el.getAttribute("title") || "");
    if (txt && playTerms.includes(txt)) {
      const clickable = el.closest("button, a, [role='button'], div") || el;
      simulateUserClick(clickable);
      return { status: "success", element: el.innerText.trim() || "Video Başlat" };
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
            return { status: "success", element: "Video Oynatıcı" };
          }
          const innerBtn = iframe.contentDocument.querySelector(".vjs-big-play-button, .jw-display-icon-container, [class*='play' i], button");
          if (innerBtn) {
            simulateUserClick(innerBtn);
            highlightElement(iframe);
            return { status: "success", element: "Video Oynatıcı" };
          }
        }
      } catch (_) {}

      // Cross-origin iframes cannot be penetrated via parent DOM click events.
      // We focus/scroll the iframe, and let background.js execute directly inside the child frame.
      continue;
    }
  }

  // 5. Fallback: Player container wrapper (#player, .video-player, etc.)
  const containers = document.querySelectorAll(
    "#player, #vplayer, #video-player, #embed-player, .player-container, .video-container, .video-wrapper, [data-player]"
  );
  for (const c of containers) {
    if (isElementVisible(c)) {
      simulateUserClick(c);
      return { status: "success", element: "Video Alanı" };
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
      // Send success response immediately BEFORE navigation destroys context
      sendResponse({ status: "success", element: result.label });
      // Execute click on next frame so message has already left the page
      setTimeout(() => {
        executeElementClick(result.element, result.label, result.isYouTube);
      }, 15);
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
