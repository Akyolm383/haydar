/**
 * Haydar Web Bridge - Popup Controller
 */

function updateUI(connected) {
  const badge = document.getElementById("statusBadge");
  const dot = document.getElementById("statusDot");
  const text = document.getElementById("statusText");
  const desc = document.getElementById("statusDesc");

  if (connected) {
    badge.className = "badge badge-connected";
    dot.className = "dot dot-connected";
    text.textContent = "Bağlı";
    desc.textContent = "Haydar masaüstü asistanına canlı bağlı.";
  } else {
    badge.className = "badge badge-disconnected";
    dot.className = "dot dot-disconnected";
    text.textContent = "Bağlantı Yok";
    desc.textContent = "Haydar'ın açık olduğundan emin olun (ws://127.0.0.1:8765).";
  }
}

function checkStatus() {
  chrome.runtime.sendMessage({ type: "get_status" }, (res) => {
    if (chrome.runtime.lastError || !res) {
      updateUI(false);
    } else {
      updateUI(!!res.connected);
    }
  });
}

document.getElementById("btnReconnect").addEventListener("click", () => {
  chrome.runtime.sendMessage({ type: "force_reconnect" }, () => {
    setTimeout(checkStatus, 400);
  });
});

document.getElementById("btnTestNext").addEventListener("click", () => {
  chrome.runtime.sendMessage({
    type: "execute_command",
    command: {
      id: "test_" + Date.now(),
      action: "click_button",
      target: "sonraki bölüm"
    }
  }, (res) => {
    console.log("Test result:", res);
    alert(res && res.status === "success" ? "✔ Başarılı: " + res.element : "⚠️ Buton bulunamadı");
  });
});

document.getElementById("btnTestScroll").addEventListener("click", () => {
  chrome.runtime.sendMessage({
    type: "execute_command",
    command: {
      id: "test_" + Date.now(),
      action: "scroll_down"
    }
  }, (res) => {
    console.log("Scroll result:", res);
  });
});

// Initial check
checkStatus();
setInterval(checkStatus, 1500);
