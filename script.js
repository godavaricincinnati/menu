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
    const rows = data.trim().split("\n").slice(1);
    const grouped = {};

    rows.forEach(row => {
      const cols = row.split(",");

      if (cols.length >= 5 && cols[4].trim().toUpperCase() !== "FALSE") {
        const category = cols[0]?.trim() || "Menu";
        const name = cols[1]?.trim() || "";
        const desc = cols[2]?.trim() || "";
        const price = cols[3]?.trim() || "";

        if (!name) return;

        if (!grouped[category]) grouped[category] = [];

        grouped[category].push({ name, desc, price });
      }
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

function renderTabs(categories) {
  categoryTabs.innerHTML = "";

  const allButton = createTabButton("All");
  categoryTabs.appendChild(allButton);

  categories.forEach(category => {
    const button = createTabButton(category);
    categoryTabs.appendChild(button);
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

    window.scrollTo({ top: 0, behavior: "smooth" });
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
        <p>${item.desc}</p>
      `;

      section.appendChild(div);
    });

    menuContainer.appendChild(section);
  });
}
