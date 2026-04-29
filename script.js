const menuContainer = document.getElementById("menu-container");
const searchInput = document.getElementById("search");
const categoryTabs = document.getElementById("category-tabs");

let fullMenu = {};
let activeCategory = "All";

fetch("menu.csv")
  .then(response => {
    if (!response.ok) throw new Error("menu.csv not found");
    return response.text();
  })
  .then(data => {
    const rows = parseCSV(data);
    const headers = rows.shift();

    const grouped = {};

    rows.forEach(cols => {
      if (cols.length < 5) return;

      const category = clean(cols[0]) || "Menu";
      const name = clean(cols[1]);
      const desc = clean(cols[2]);
      const price = clean(cols[3]);
      const available = clean(cols[4]).toUpperCase();

      if (!name || available === "FALSE") return;

      if (!grouped[category]) grouped[category] = [];
      grouped[category].push({ name, desc, price });
    });

    fullMenu = grouped;

    renderTabs(Object.keys(fullMenu));
    renderMenu(fullMenu);

    searchInput.addEventListener("input", handleSearch);
  })
  .catch(() => {
    menuContainer.innerHTML = `
      <p style="text-align:center; color:#8B0000; font-weight:bold;">
        Menu file not found. Please upload menu.csv to the main/root folder.
      </p>
    `;
  });

function clean(value) {
  return String(value || "").trim();
}

function renderTabs(categories) {
  categoryTabs.innerHTML = "";

  categoryTabs.appendChild(createTabButton("All"));

  categories.forEach(category => {
    categoryTabs.appendChild(createTabButton(category));
  });
}

function createTabButton(category) {
  const button = document.createElement("button");
  button.textContent = category;
  button.className = category === activeCategory ? "tab active" : "tab";

  button.addEventListener("click", () => {
    activeCategory = category;
    searchInput.value = "";

    document.querySelectorAll(".tab").forEach(tab => tab.classList.remove("active"));
    button.classList.add("active");

    if (category === "All") {
      renderMenu(fullMenu);
    } else {
      renderMenu({ [category]: fullMenu[category] });
    }

    document.querySelector(".menu-page").scrollIntoView({ behavior: "smooth" });
  });

  return button;
}

function handleSearch() {
  const keyword = searchInput.value.toLowerCase();

  const source =
    activeCategory === "All"
      ? fullMenu
      : { [activeCategory]: fullMenu[activeCategory] };

  const filtered = {};

  Object.keys(source).forEach(category => {
    const items = source[category].filter(item =>
      item.name.toLowerCase().includes(keyword) ||
      item.desc.toLowerCase().includes(keyword)
    );

    if (items.length) filtered[category] = items;
  });

  renderMenu(filtered);
}

function renderMenu(grouped) {
  menuContainer.innerHTML = "";

  if (!grouped || Object.keys(grouped).length === 0) {
    menuContainer.innerHTML = `<p style="text-align:center;">No menu items found.</p>`;
    return;
  }

  Object.keys(grouped).forEach(category => {
    const section = document.createElement("section");
    section.className = "category-section";

    section.innerHTML = `
      <div class="separator">❦</div>
      <h2>${category}</h2>
    `;

    grouped[category].forEach(item => {
      const div = document.createElement("div");
      div.className = "menu-item";

      div.innerHTML = `
        <div class="item-top">
          <h3>${item.name}</h3>
          <span class="price">$${item.price}</span>
        </div>
        ${item.desc ? `<p>${item.desc}</p>` : ""}
      `;

      section.appendChild(div);
    });

    menuContainer.appendChild(section);
  });
}

function parseCSV(text) {
  const rows = [];
  let row = [];
  let value = "";
  let insideQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    const next = text[i + 1];

    if (char === '"' && insideQuotes && next === '"') {
      value += '"';
      i++;
    } else if (char === '"') {
      insideQuotes = !insideQuotes;
    } else if (char === "," && !insideQuotes) {
      row.push(value);
      value = "";
    } else if ((char === "\n" || char === "\r") && !insideQuotes) {
      if (value || row.length) {
        row.push(value);
        rows.push(row);
        row = [];
        value = "";
      }
    } else {
      value += char;
    }
  }

  if (value || row.length) {
    row.push(value);
    rows.push(row);
  }

  return rows;
}
