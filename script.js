const menuContainer = document.getElementById("menu-container");
const searchInput = document.getElementById("search");

fetch("menu.csv")
.then(response => response.text())
.then(data => {
const rows = data.split("\n").slice(1);

```
const grouped = {};

rows.forEach(row => {
  const cols = row.split(",");

  if (cols.length >= 5 && cols[4].trim() !== "FALSE") {
    const category = cols[0].trim();
    const item = {
      name: cols[1],
      desc: cols[2],
      price: cols[3]
    };

    if (!grouped[category]) grouped[category] = [];
    grouped[category].push(item);
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
```

});

function renderMenu(grouped) {
menuContainer.innerHTML = "";

Object.keys(grouped).forEach(category => {
const section = document.createElement("section");

```
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
```

});
}
