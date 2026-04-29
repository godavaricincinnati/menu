const MENU_CSV_URL = "data/sample-menu.csv";
const FALLBACK_CSV_URL = "data/sample-menu.csv";
const currency = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" });
let allItems = [];
let activeCategory = "All";
const els = {
  search: document.getElementById("searchInput"),
  tabs: document.getElementById("categoryTabs"),
  status: document.getElementById("status"),
  menu: document.getElementById("menuContainer")
};
async function loadMenu() {
  try {
    const response = await fetch(MENU_CSV_URL, { cache: "no-store" });
    if (!response.ok) throw new Error("Menu source not available");
    const text = await response.text();
    allItems = parseCSV(text).map(normalizeItem).filter(item => item.available);
    if (!allItems.length) throw new Error("No available menu items found");
    els.status.classList.add("hidden");
    renderTabs();
    renderMenu();
  } catch (error) {
    els.status.textContent = "Menu is temporarily unavailable. Please ask your server for assistance.";
    console.error(error);
    if (MENU_CSV_URL !== FALLBACK_CSV_URL) {
      try {
        const fallback = await fetch(FALLBACK_CSV_URL, { cache: "no-store" });
        const text = await fallback.text();
        allItems = parseCSV(text).map(normalizeItem).filter(item => item.available);
        els.status.classList.add("hidden");
        renderTabs();
        renderMenu();
      } catch {}
    }
  }
}
function parseCSV(text) {
  const rows = [];
  let row = [], field = "", inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const char = text[i], next = text[i + 1];
    if (char === '"' && inQuotes && next === '"') { field += '"'; i++; }
    else if (char === '"') inQuotes = !inQuotes;
    else if (char === "," && !inQuotes) { row.push(field); field = ""; }
    else if ((char === "\n" || char === "\r") && !inQuotes) {
      if (field || row.length) { row.push(field); rows.push(row); row = []; field = ""; }
      if (char === "\r" && next === "\n") i++;
    } else field += char;
  }
  if (field || row.length) { row.push(field); rows.push(row); }
  const headers = rows.shift().map(h => h.trim());
  return rows.filter(r => r.some(Boolean)).map(r => Object.fromEntries(headers.map((h, i) => [h, (r[i] || "").trim()])));
}
function normalizeItem(row) {
  const availableRaw = String(row.Available || "yes").toLowerCase();
  return {
    category: row.Category || "Menu",
    name: row["Item Name"] || row.Name || "",
    description: row.Description || "",
    price: cleanPrice(row.Price),
    type: row["Veg/Non-Veg"] || row.Type || "",
    spice: row["Spice Level"] || "",
    popular: isYes(row.Popular),
    sort: Number(row["Sort Order"] || 9999),
    available: !["no", "false", "0", "n", "unavailable", "hide"].includes(availableRaw)
  };
}
function cleanPrice(value) {
  const number = Number(String(value || "").replace(/[^0-9.]/g, ""));
  return Number.isFinite(number) && number > 0 ? number : null;
}
function isYes(value) {
  return ["yes", "true", "1", "y"].includes(String(value || "").toLowerCase());
}
function renderTabs() {
  const categories = ["All", ...new Set(allItems.sort((a, b) => a.sort - b.sort).map(i => i.category))];
  els.tabs.innerHTML = categories.map(cat => `<button class="tab ${cat === activeCategory ? "active" : ""}" data-cat="${escapeHtml(cat)}">${escapeHtml(cat)}</button>`).join("");
  els.tabs.querySelectorAll(".tab").forEach(btn => btn.addEventListener("click", () => {
    activeCategory = btn.dataset.cat;
    renderTabs();
    renderMenu();
  }));
}
function renderMenu() {
  const query = els.search.value.trim().toLowerCase();
  const filtered = allItems
    .filter(item => activeCategory === "All" || item.category === activeCategory)
    .filter(item => !query || `${item.category} ${item.name} ${item.description}`.toLowerCase().includes(query))
    .sort((a, b) => a.category.localeCompare(b.category) || a.sort - b.sort || a.name.localeCompare(b.name));
  if (!filtered.length) {
    els.menu.innerHTML = `<div class="status">No matching menu items found.</div>`;
    return;
  }
  const grouped = groupBy(filtered, item => item.category);
  els.menu.innerHTML = Object.entries(grouped).map(([category, items]) => `
    <section class="category" id="${slug(category)}">
      <h2 class="category-title">${escapeHtml(category)}</h2>
      <div class="items">${items.map(renderItem).join("")}</div>
    </section>
  `).join("");
}
function renderItem(item) {
  const typeClass = item.type.toLowerCase().includes("non") ? "nonveg" : item.type.toLowerCase().includes("veg") ? "veg" : "";
  const badges = [
    item.type ? `<span class="badge ${typeClass}">${escapeHtml(item.type)}</span>` : "",
    item.spice ? `<span class="badge">${escapeHtml(item.spice)}</span>` : "",
    item.popular ? `<span class="badge">Popular</span>` : ""
  ].filter(Boolean).join("");
  return `<article class="item-card">
    <div class="item-top">
      <h3 class="item-name">${escapeHtml(item.name)}</h3>
      <div class="price">${item.price ? currency.format(item.price) : ""}</div>
    </div>
    ${item.description ? `<p class="desc">${escapeHtml(item.description)}</p>` : ""}
    ${badges ? `<div class="badges">${badges}</div>` : ""}
  </article>`;
}
function groupBy(items, fn) {
  return items.reduce((acc, item) => {
    const key = fn(item);
    acc[key] = acc[key] || [];
    acc[key].push(item);
    return acc;
  }, {});
}
function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","'":"&#39;",'"':"&quot;"}[c]));
}
function slug(value) {
  return String(value).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}
els.search.addEventListener("input", renderMenu);
loadMenu();
