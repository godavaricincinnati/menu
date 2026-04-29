fetch('menu.csv')
  .then(response => response.text())
  .then(data => {
    const rows = data.split('\n').slice(1);
    const container = document.getElementById('menu-container');

    rows.forEach(row => {
      const cols = row.split(',');

      if (cols.length >= 4 && cols[4]?.trim() !== 'FALSE') {
        const item = document.createElement('div');
        item.className = 'menu-item';

        item.innerHTML = `
          <h3>${cols[1]}</h3>
          <p>${cols[2]}</p>
          <p class="price">$${cols[3]}</p>
        `;

        container.appendChild(item);
      }
    });
  });
