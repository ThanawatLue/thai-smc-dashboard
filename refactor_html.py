import re

with open('dashboard/templates/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace sidebar brand block to add tabs
old_sidebar = '''    <div class="brand">
      <h1>Thai SMC Dashboard</h1>
      <p>Auto universe from VCP, CANSLIM, Dip Buy, Momentum</p>
    </div>
    <button id="scanBtn" class="primary" type="button" style="width:100%; margin-bottom: 16px;">'''

new_sidebar = '''    <div class="brand">
      <h1 id="dashboardTitle">Thai SMC Dashboard</h1>
      <p id="dashboardSubtitle">Auto universe from VCP, CANSLIM, Dip Buy, Momentum</p>
    </div>
    <div class="market-tabs" style="display: flex; gap: 4px; margin-bottom: 16px; background: var(--surface-2); padding: 4px; border-radius: var(--radius);">
      <button id="tabTH" class="tab-btn active" data-market="TH" style="flex:1; border:none; padding: 6px; font-size: 0.8rem;">TH</button>
      <button id="tabUS" class="tab-btn" data-market="US" style="flex:1; border:none; padding: 6px; font-size: 0.8rem; background: transparent;">US</button>
      <button id="tabGOLD" class="tab-btn" data-market="GOLD" style="flex:1; border:none; padding: 6px; font-size: 0.8rem; background: transparent;">GOLD</button>
    </div>
    <button id="scanBtn" class="primary" type="button" style="width:100%; margin-bottom: 16px;">'''

content = content.replace(old_sidebar, new_sidebar)

# Replace Market Metric label
content = content.replace('<div class="metric"><b>Market</b><span>TH</span></div>', '<div class="metric"><b>Market</b><span id="metricMarket">TH</span></div>')


# Replace JS scan function
old_scan = '''async function scan(forceRefresh = false) {
  try {
    document.getElementById("timestamp").textContent = forceRefresh ? "Analyzing market data..." : "Loading...";
    document.getElementById("scanBtn").classList.add("loading");
    
    const minRr = document.getElementById("minRrInput").value;
    const qs = forceRefresh ? `?refresh=1&min_rr=${minRr}` : `?min_rr=${minRr}`;
    const response = await fetch(`/api/scan${qs}`);'''

new_scan = '''async function scan(forceRefresh = false) {
  try {
    document.getElementById("timestamp").textContent = forceRefresh ? "Analyzing market data..." : "Loading...";
    document.getElementById("scanBtn").classList.add("loading");
    
    const minRr = document.getElementById("minRrInput").value;
    const qs = forceRefresh ? `?refresh=1&min_rr=${minRr}&market=${currentMarket}` : `?min_rr=${minRr}&market=${currentMarket}`;
    const response = await fetch(`/api/scan${qs}`);'''

content = content.replace(old_scan, new_scan)

# Append JS for Tabs at the end
old_init = '''// Init
hydrateCachedScan();
scan();'''

new_init = '''// Market Tabs Logic
let currentMarket = localStorage.getItem("smc_market") || "TH";
document.getElementById("metricMarket").textContent = currentMarket;

function setMarket(market) {
  currentMarket = market;
  localStorage.setItem("smc_market", market);
  document.getElementById("metricMarket").textContent = market;
  
  // Update Tab UI
  document.querySelectorAll(".tab-btn").forEach(btn => {
    if (btn.dataset.market === market) {
      btn.classList.add("active");
      btn.style.background = "var(--primary)";
      btn.style.color = "#fff";
    } else {
      btn.classList.remove("active");
      btn.style.background = "transparent";
      btn.style.color = "var(--text)";
    }
  });

  // Update text
  const title = document.getElementById("dashboardTitle");
  const sub = document.getElementById("dashboardSubtitle");
  if (market === "TH") {
    title.textContent = "Thai SMC Dashboard";
    sub.textContent = "Auto universe from SET/MAI";
  } else if (market === "US") {
    title.textContent = "US SMC Dashboard";
    sub.textContent = "Auto universe from S&P 500";
  } else {
    title.textContent = "Gold SMC Dashboard";
    sub.textContent = "COMEX Gold Futures (GC=F)";
  }

  scan(false);
}

// Initial Tab setup
setMarket(currentMarket);

document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", (e) => {
    setMarket(e.target.dataset.market);
  });
});

// Init
hydrateCachedScan();
if (!document.getElementById("scanBtn").classList.contains("loading")) {
  // skip if setMarket already triggered scan, but actually setMarket triggers scan synchronously above
}
'''

content = content.replace(old_init, new_init)

with open('dashboard/templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
