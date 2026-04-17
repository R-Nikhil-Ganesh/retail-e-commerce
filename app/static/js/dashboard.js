(() => {
  let trendChart;
  let categoryChart;
  let currentBand = "all";

  function bandForScore(score) {
    if (score >= 67) return "high";
    if (score >= 34) return "medium";
    return "low";
  }

  function reasonChips(reasons) {
    return (reasons || []).map((reason) => `<span class="badge-chip">${reason}</span>`).join("");
  }

  function renderRow(product) {
    const bandClass = `band-${product.risk_band}`;
    return `
      <tr data-band="${product.risk_band}">
        <td>
          <strong>${product.title}</strong><br />
          <span class="rating">${product.brand} · ${product.category}</span>
        </td>
        <td><span class="risk-score ${bandClass}">${product.risk_score}</span></td>
        <td>${product.return_rate}%</td>
        <td>${reasonChips(product.top_reasons)}</td>
        <td>${product.suggested_action}</td>
        <td><a class="btn btn-sm btn-ghost" href="/product/${product.id}">Open</a></td>
      </tr>
    `;
  }

  function applyFilter() {
    document.querySelectorAll("#riskTable tbody tr").forEach((row) => {
      row.style.display = currentBand === "all" || row.dataset.band === currentBand ? "" : "none";
    });
  }

  function setupCharts(metrics) {
    if (typeof Chart === "undefined") return;

    const trendCtx = document.getElementById("trendChart");
    const categoryCtx = document.getElementById("categoryChart");

    if (trendChart) trendChart.destroy();
    if (categoryChart) categoryChart.destroy();

    trendChart = new Chart(trendCtx, {
      type: "line",
      data: {
        labels: metrics.monthly_trend.map((item) => item.month),
        datasets: [
          {
            label: "Actual",
            data: metrics.monthly_trend.map((item) => item.return_rate),
            borderColor: "#0f766e",
            backgroundColor: "rgba(15,118,110,0.12)",
            tension: 0.35,
            fill: true,
            pointRadius: 3,
          },
          {
            label: "AI Projected",
            data: metrics.monthly_trend.map((item) => item.ai_projected),
            borderColor: "#1d4ed8",
            backgroundColor: "rgba(29,78,216,0.10)",
            borderDash: [6, 4],
            tension: 0.35,
            fill: false,
            pointRadius: 3,
          },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, grid: { color: "rgba(148,163,184,.18)" } },
          x: { grid: { display: false } },
        },
      },
    });

    categoryChart = new Chart(categoryCtx, {
      type: "doughnut",
      data: {
        labels: Object.keys(metrics.category_breakdown),
        datasets: [{
          data: Object.values(metrics.category_breakdown),
          backgroundColor: ["#0f766e", "#1d4ed8", "#b45309", "#be123c"],
          borderWidth: 0,
        }],
      },
      options: {
        plugins: { legend: { position: "bottom" } },
        cutout: "66%",
      },
    });
  }

  async function loadReviewTiles() {
    const tasks = PRODUCTS.map(async (product) => {
      const node = document.getElementById(`ri-${product.id}`);
      if (!node) return;
      const response = await fetch(`/api/review-summary/${product.id}`);
      const payload = await response.json();
      if (!response.ok) {
        node.innerHTML = `<div class="ri-product">${product.title}</div><div class="rating">Review summary unavailable</div>`;
        return;
      }
      node.innerHTML = `
        <div class="ri-product">${product.title}</div>
        <div class="review-fit-tag">${payload.fit_tag}</div>
        <div class="rating" style="margin-bottom: 8px;">${payload.fit_summary}</div>
        <ul class="ri-list">${(payload.top_concerns || []).map((item) => `<li>${item}</li>`).join("")}</ul>
      `;
    });
    await Promise.all(tasks);
  }

  async function loadMetrics() {
    const response = await fetch("/api/dashboard-metrics");
    const metrics = await response.json();
    if (!response.ok) return;

    document.getElementById("kpiOrders").textContent = metrics.total_orders.toLocaleString();
    document.getElementById("kpiReturnRate").textContent = `${metrics.estimated_return_rate}%`;
    document.getElementById("kpiReturnSub").textContent = `Projected with current catalog mix`;
    document.getElementById("kpiHighRisk").textContent = metrics.high_risk_skus;
    document.getElementById("kpiReduction").textContent = `${metrics.reduction_potential}%`;

    document.getElementById("tableBody").innerHTML = metrics.products.map(renderRow).join("");
    document.getElementById("actionsList").innerHTML = metrics.top_actions.map((item) => `<li class="action-item">${item}</li>`).join("");

    setupCharts(metrics);
    applyFilter();
    await loadReviewTiles();
  }

  window.filterTable = function filterTable(band, button) {
    currentBand = band;
    document.querySelectorAll(".filter-btn").forEach((node) => node.classList.remove("active"));
    if (button) button.classList.add("active");
    applyFilter();
  };

  document.addEventListener("DOMContentLoaded", loadMetrics);
})();
