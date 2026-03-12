const API_URL = "http://localhost:8000";

document.addEventListener("DOMContentLoaded", async () => {
  const analyzeBtn = document.getElementById("analyzeBtn");
  const keywordsBtn = document.getElementById("keywordsBtn");
  const briefBtn = document.getElementById("briefBtn");
  const openDashboard = document.getElementById("openDashboard");
  const openSettings = document.getElementById("openSettings");
  const pageInfo = document.getElementById("pageInfo");
  const opportunityScore = document.getElementById("opportunityScore");

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const url = tab?.url || "";

  if (url.includes("stock.adobe.com")) {
    const pageType = detectPageType(url);
    pageInfo.innerHTML = `
      <p><strong>Page Type:</strong> ${pageType.type}</p>
      ${pageType.keyword ? `<p><strong>Keyword:</strong> ${pageType.keyword}</p>` : ""}
      ${pageType.contributorId ? `<p><strong>Contributor:</strong> ${pageType.contributorId}</p>` : ""}
    `;
  } else {
    pageInfo.innerHTML = `<p class="loading">Not on Adobe Stock</p>`;
  }

  analyzeBtn.addEventListener("click", async () => {
    const pageType = detectPageType(url);
    if (pageType.keyword) {
      analyzeBtn.textContent = "Analyzing...";
      try {
        const score = await fetchOpportunityScore(pageType.keyword);
        displayScore(score);
      } catch (error) {
        console.error("Error:", error);
      }
      analyzeBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/>
          <path d="m21 21-4.35-4.35"/>
        </svg>
        Analyze Page
      `;
    }
  });

  keywordsBtn.addEventListener("click", async () => {
    chrome.tabs.sendMessage(tab.id, { action: "showKeywordSuggestions" });
  });

  briefBtn.addEventListener("click", () => {
    const pageType = detectPageType(url);
    if (pageType.keyword) {
      chrome.tabs.create({
        url: `http://localhost:3000/dashboard/briefs?keyword=${encodeURIComponent(pageType.keyword)}`,
      });
    } else {
      chrome.tabs.create({ url: "http://localhost:3000/dashboard/briefs" });
    }
  });

  openDashboard.addEventListener("click", (e) => {
    e.preventDefault();
    chrome.tabs.create({ url: "http://localhost:3000/dashboard" });
  });

  openSettings.addEventListener("click", (e) => {
    e.preventDefault();
    chrome.runtime.openOptionsPage();
  });
});

function detectPageType(url) {
  const result = { type: "Unknown", keyword: null, contributorId: null };

  if (url.includes("/search")) {
    result.type = "Search Results";
    const params = new URLSearchParams(url.split("?")[1]);
    result.keyword = params.get("k");
  } else if (url.includes("/contributor/")) {
    result.type = "Contributor Portfolio";
    const match = url.match(/\/contributor\/(\d+)/);
    result.contributorId = match ? match[1] : null;
  } else if (url.includes("/images/") || url.includes("/video/")) {
    result.type = "Asset Detail";
  } else if (url.includes("contributor.stock.adobe.com")) {
    result.type = "Contributor Portal";
  } else {
    result.type = "Browse";
  }

  return result;
}

async function fetchOpportunityScore(keyword) {
  const response = await fetch(`${API_URL}/opportunities/score/${encodeURIComponent(keyword)}`);
  if (!response.ok) {
    throw new Error("Failed to fetch score");
  }
  return response.json();
}

function displayScore(score) {
  const container = document.getElementById("opportunityScore");
  const scoreClass =
    score.overall_score >= 70
      ? "high"
      : score.overall_score >= 40
        ? "medium"
        : "low";

  container.innerHTML = `
    <div class="score-value">${Math.round(score.overall_score)}</div>
    <div class="score-label">Opportunity Score</div>
    <div style="margin-top: 12px; text-align: left; font-size: 11px; color: #737373;">
      <div>Demand: ${score.demand_signal.toFixed(0)}</div>
      <div>Competition: ${score.competition_index.toFixed(0)}</div>
      <div>Urgency: ${score.urgency_level}</div>
    </div>
  `;
}
