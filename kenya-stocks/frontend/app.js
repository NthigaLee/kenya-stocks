async function loadSampleStocks() {
  const statusEl = document.getElementById("status");
  const tbody = document.querySelector("#stocks-table tbody");

  statusEl.textContent = "Loading sample data from backend...";

  try {
    const res = await fetch("http://127.0.0.1:8000/stocks/sample");
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json();
    tbody.innerHTML = "";

    for (const stock of data.stocks || []) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${stock.symbol}</td>
        <td>${stock.name}</td>
        <td>${stock.price.toFixed(2)}</td>
        <td>${stock.change >= 0 ? "+" : ""}${stock.change.toFixed(2)}</td>
      `;
      tbody.appendChild(tr);
    }

    statusEl.textContent = "Loaded sample data (live NSE integration coming next).";
  } catch (err) {
    console.error(err);
    statusEl.textContent = "Failed to load from backend. Is the FastAPI server running on 127.0.0.1:8000?";
  }
}

async function loadAnnouncementsSample() {
  const statusEl = document.getElementById("ann-status");
  const tbody = document.querySelector("#announcements-table tbody");

  statusEl.textContent = "Loading sample announcements from backend...";

  try {
    const res = await fetch("http://127.0.0.1:8000/announcements/nse");
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`);
    }
    const data = await res.json();
    tbody.innerHTML = "";

    for (const ann of data.announcements || []) {
      const tr = document.createElement("tr");
      const dateDisplay = ann.date || "-";
      tr.innerHTML = `
        <td>${ann.company}</td>
        <td><a href="${ann.url}" target="_blank" rel="noopener noreferrer">${ann.title}</a></td>
        <td>${dateDisplay}</td>
      `;
      tbody.appendChild(tr);
    }

    statusEl.textContent = `Loaded ${data.count ?? (data.announcements || []).length} announcements (structure will improve as we tune the scraper).`;
  } catch (err) {
    console.error(err);
    statusEl.textContent = "Failed to load announcements. Is the FastAPI server running and online?";
  }
}

window.addEventListener("DOMContentLoaded", () => {
  loadSampleStocks();
  loadAnnouncementsSample();
});
