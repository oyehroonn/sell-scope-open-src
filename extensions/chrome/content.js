const SELLSCOPE_API = "http://localhost:8000";

let sellscopeOverlay = null;

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "showKeywordSuggestions") {
    showKeywordSuggestions();
  }
  return true;
});

function showKeywordSuggestions() {
  if (sellscopeOverlay) {
    sellscopeOverlay.remove();
    sellscopeOverlay = null;
    return;
  }

  const currentKeyword = getCurrentKeyword();

  sellscopeOverlay = document.createElement("div");
  sellscopeOverlay.id = "sellscope-overlay";
  sellscopeOverlay.innerHTML = `
    <div class="sellscope-panel">
      <div class="sellscope-header">
        <span class="sellscope-logo">SellScope</span>
        <button class="sellscope-close">&times;</button>
      </div>
      <div class="sellscope-content">
        <div class="sellscope-section">
          <h3>Detected Keyword</h3>
          <p class="sellscope-keyword">${currentKeyword || "Not detected"}</p>
        </div>
        <div class="sellscope-section">
          <h3>Keyword Suggestions</h3>
          <div class="sellscope-loading">Loading suggestions...</div>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(sellscopeOverlay);

  sellscopeOverlay.querySelector(".sellscope-close").addEventListener("click", () => {
    sellscopeOverlay.remove();
    sellscopeOverlay = null;
  });

  if (currentKeyword) {
    fetchKeywordSuggestions(currentKeyword);
  }
}

function getCurrentKeyword() {
  const url = window.location.href;
  if (url.includes("/search")) {
    const params = new URLSearchParams(window.location.search);
    return params.get("k");
  }

  const titleElement = document.querySelector("h1, .asset-title");
  if (titleElement) {
    return titleElement.textContent.trim().substring(0, 50);
  }

  return null;
}

async function fetchKeywordSuggestions(keyword) {
  try {
    const response = await fetch(
      `${SELLSCOPE_API}/keywords/suggestions/?q=${encodeURIComponent(keyword)}&limit=10`
    );

    if (!response.ok) throw new Error("Failed to fetch");

    const suggestions = await response.json();

    const container = sellscopeOverlay.querySelector(".sellscope-section:last-child");
    container.innerHTML = `
      <h3>Keyword Suggestions</h3>
      <div class="sellscope-suggestions">
        ${suggestions.map((s) => `<span class="sellscope-tag">${s}</span>`).join("")}
      </div>
    `;
  } catch (error) {
    console.error("SellScope error:", error);
    const container = sellscopeOverlay.querySelector(".sellscope-loading");
    if (container) {
      container.textContent = "Could not load suggestions";
    }
  }
}

function injectOpportunityBadge() {
  if (!window.location.href.includes("/search")) return;

  const searchItems = document.querySelectorAll("[data-testid='search-result-item']");

  searchItems.forEach((item) => {
    if (item.querySelector(".sellscope-badge")) return;

    const badge = document.createElement("div");
    badge.className = "sellscope-badge";
    badge.innerHTML = `
      <span class="sellscope-badge-score">--</span>
      <span class="sellscope-badge-label">Score</span>
    `;

    const imageContainer = item.querySelector("a");
    if (imageContainer) {
      imageContainer.style.position = "relative";
      imageContainer.appendChild(badge);
    }
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", injectOpportunityBadge);
} else {
  injectOpportunityBadge();
}

const observer = new MutationObserver(() => {
  injectOpportunityBadge();
});

observer.observe(document.body, {
  childList: true,
  subtree: true,
});
