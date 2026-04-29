const menuContainer = document.getElementById("menu-container");
const searchInput = document.getElementById("search");

fetch("menu.csv")
  .then(response => {
    if (!response.ok) {
      throw new Error("menu.csv not found");
    }
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

        grouped[category].push({
          name,
          desc,
          price
        });
      }
    });

    renderMenu(grouped);

    searchInput.addEventListener("input", function () {
      const keyword = this.value.toLowerCase();
      const filtered = {};

      Object.keys(grouped).forEach(category => {
        const items = grouped[category].filter(item =>
          item.name.toLowerCase().includes(keyword) ||
          item.desc.toLowerCase().includes(keyword)
        );

        if (items.length) filtered[category] = items;
      });

      renderMenu(filtered);
    });
  })
  .catch(error => {
    menuContainer.innerHTML = `
      <p style="text-align:center; color:#8B0000; font-weight:bold;">
        Menu file not found. Please upload menu.csv to the main/root folder.
      </p>
    `;
  });

function renderMenu(grouped) {
  menuContainer.innerHTML = "";

  if (Object.keys(grouped).length === 0) {
    menuContainer.innerHTML = `
      <p style="text-align:center;">No menu items found.</p>
    `;
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
