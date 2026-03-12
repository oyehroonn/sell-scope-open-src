chrome.runtime.onInstalled.addListener(() => {
  console.log("SellScope extension installed");
});

chrome.action.onClicked.addListener((tab) => {
  if (tab.url?.includes("stock.adobe.com")) {
    chrome.tabs.sendMessage(tab.id, { action: "togglePanel" });
  }
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "fetchAPI") {
    fetch(request.url, request.options)
      .then((response) => response.json())
      .then((data) => sendResponse({ success: true, data }))
      .catch((error) => sendResponse({ success: false, error: error.message }));
    return true;
  }
});
