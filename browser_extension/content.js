/**
 * Haydar Web Bridge - Content Script
 * Injected into web pages to locate elements, click buttons, and handle scrolling.
 */

// Turkish-aware text normalization
function normalizeTr(text) {
  if (!text) return "";
  const map = { "İ": "i", "I": "ı", "Ğ": "ğ", "Ü": "ü", "Ş": "ş", "Ö": "ö", "Ç": "ç" };
  let str = text;
  for (const [upper, lower] of Object.entries(map)) {
    str = str.replaceAll(upper, lower);
  }
  return str.toLowerCase().replace(/[^\w\s\dçğıöşü]/g, " ").replace(/\s+/g, " ").trim();
}

function isElementVisible(el) {
  if (!el) return false;
  const style = window.getComputedStyle(el);
  if (style.display === "none" || style.visibility === "hidden" || parseFloat(style.opacity) === 0) {
    return false;
  }
  const rect = el.getBoundingClientRect();
  return rect.width > 0 && rect.height > 0;
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
    // Yerli & yabancı dizi/film siteleri
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
    "[data-action='next-episode']",
    ".jw-icon-next",
    ".vjs-next-button"
  ],
  "önceki bölüm": [
    ".prev-episode",
    "button.prev-episode",
    "a.prev-episode",
    ".onceki-bolum",
    "a.onceki-bolum",
    "a[title*='Önceki' i]",
    "button[title*='Önceki' i]",
    ".jw-icon-prev",
    ".vjs-prev-button"
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

// Universal smart DOM button locator
function findTargetButton(targetPhrase) {
  const normTarget = normalizeTr(targetPhrase);

  // 1. Check known platform selectors first
  for (const [key, selectors] of Object.entries(PLATFORM_SELECTORS)) {
    const normKey = normalizeTr(key);
    if (normTarget.includes(normKey) || normKey.includes(normTarget)) {
      for (const sel of selectors) {
        try {
          const els = document.querySelectorAll(sel);
          for (const el of els) {
            if (isElementVisible(el)) {
              return { element: el, label: key };
            }
          }
        } catch (_) {}
      }
    }
  }

  // 2. Universal DOM search on clickable elements
  const candidates = document.querySelectorAll(
    "button, a, [role='button'], input[type='button'], input[type='submit'], [onclick], div[class*='btn' i], span[class*='btn' i]"
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

      // Exact phrase match
      if (norm === normTarget) {
        return { element: el, label: raw.trim() || targetPhrase };
      }

      // Target phrase is fully inside element text or vice-versa
      if (norm.includes(normTarget) || (normTarget.length > 3 && norm.includes(normTarget))) {
        const score = normTarget.length / Math.max(norm.length, normTarget.length);
        if (score > bestScore) {
          bestScore = score;
          bestMatch = { element: el, label: raw.trim() || targetPhrase };
        }
      }
    }
  }

  if (bestMatch && bestScore >= 0.3) {
    return bestMatch;
  }

  return null;
}

// Executes click with visual emerald pulse animation
function executeElementClick(el, label) {
  try {
    el.scrollIntoView({ behavior: "smooth", block: "center" });
  } catch (_) {}

  // Apply visual highlight
  el.classList.add("haydar-highlight-pulse");
  setTimeout(() => {
    el.classList.remove("haydar-highlight-pulse");
  }, 1200);

  // Dispatch mouse and click events
  const mouseOpts = { bubbles: true, cancelable: true, view: window };
  el.dispatchEvent(new MouseEvent("mousedown", mouseOpts));
  el.dispatchEvent(new MouseEvent("mouseup", mouseOpts));
  el.click();

  return { status: "success", element: label };
}

// Message listener from background.js
chrome.runtime.onMessage.addListener((cmd, sender, sendResponse) => {
  console.log("[Haydar Content] Handling command:", cmd);
  const action = cmd.action;
  const target = cmd.target || "";

  if (action === "click_button") {
    const result = findTargetButton(target);
    if (result && result.element) {
      const resp = executeElementClick(result.element, result.label);
      sendResponse(resp);
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
