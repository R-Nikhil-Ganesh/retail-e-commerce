(() => {
  let trendChart;
  let categoryChart;
  let currentBand = "all";

  function bandForScore(score) {
    const numeric = Number(score) || 0;
    if (numeric >= 67) return "high";
    if (numeric >= 34) return "medium";
    return "low";
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function reasonChips(reasons) {
    return (reasons || []).map((reason) => `<span class="badge-chip">${escapeHtml(reason)}</span>`).join("");
  }

  function renderRow(product) {
    const band = product.risk_band || bandForScore(product.risk_score);
    const bandClass = `band-${band}`;
    return `
      <tr data-band="${band}">
        <td>
          <strong>${escapeHtml(product.title)}</strong><br />
          <span class="rating">${escapeHtml(product.brand)} · ${escapeHtml(product.category)}</span>
        </td>
        <td><span class="risk-score ${bandClass}">${Number(product.risk_score) || 0}</span></td>
        <td>${Number(product.return_rate) || 0}%</td>
        <td>${reasonChips(product.top_reasons)}</td>
        <td>${escapeHtml(product.suggested_action || "No suggestion available")}</td>
        <td><a class="btn btn-sm btn-ghost" href="/product/${encodeURIComponent(product.id)}">Open</a></td>
      </tr>
    `;
  }

  function applyFilter() {
    document.querySelectorAll("#riskTable tbody tr").forEach((row) => {
      if (!row.dataset.band) {
        row.style.display = "";
        return;
      }
      row.style.display = currentBand === "all" || row.dataset.band === currentBand ? "" : "none";
    });
  }

  function renderNoDataRow(message) {
    document.getElementById("tableBody").innerHTML = `<tr><td colspan="6" class="table-loading">${escapeHtml(message)}</td></tr>`;
  }

  function setDashboardUnavailable(message) {
    document.getElementById("kpiOrders").textContent = "N/A";
    document.getElementById("kpiReturnRate").textContent = "N/A";
    document.getElementById("kpiReturnSub").textContent = message;
    document.getElementById("kpiHighRisk").textContent = "N/A";
    document.getElementById("kpiReduction").textContent = "N/A";
    document.getElementById("actionsList").innerHTML = `<li class="action-item">${escapeHtml(message)}</li>`;
    renderNoDataRow(message);
  }

  function setupCharts(metrics) {
    if (typeof Chart === "undefined") return;

    const trendCtx = document.getElementById("trendChart");
    const categoryCtx = document.getElementById("categoryChart");

    if (trendChart) trendChart.destroy();
    if (categoryChart) categoryChart.destroy();

    const monthlyTrend = Array.isArray(metrics.monthly_trend) ? metrics.monthly_trend : [];
    const categoryBreakdown = metrics.category_breakdown || {};

    trendChart = new Chart(trendCtx, {
      type: "line",
      data: {
        labels: monthlyTrend.map((item) => item.month),
        datasets: [
          {
            label: "Actual",
            data: monthlyTrend.map((item) => item.return_rate),
            borderColor: "#0f766e",
            backgroundColor: "rgba(15,118,110,0.12)",
            tension: 0.35,
            fill: true,
            pointRadius: 3,
          },
          {
            label: "AI Projected",
            data: monthlyTrend.map((item) => item.ai_projected),
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
        labels: Object.keys(categoryBreakdown),
        datasets: [{
          data: Object.values(categoryBreakdown),
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
    const tasks = (Array.isArray(PRODUCTS) ? PRODUCTS : []).map(async (product) => {
      const node = document.getElementById(`ri-${product.id}`);
      if (!node) return;
      try {
        const response = await fetch(`/api/review-summary/${encodeURIComponent(product.id)}`);
        const payload = await response.json();
        if (!response.ok) {
          node.innerHTML = `<div class="ri-product">${escapeHtml(product.title)}</div><div class="rating">Review summary unavailable</div>`;
          return;
        }
        node.innerHTML = `
          <div class="ri-product">${escapeHtml(product.title)}</div>
          <div class="review-fit-tag">${escapeHtml(payload.fit_tag)}</div>
          <div class="rating" style="margin-bottom: 8px;">${escapeHtml(payload.fit_summary)}</div>
          <ul class="ri-list">${(payload.top_concerns || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        `;
      } catch {
        node.innerHTML = `<div class="ri-product">${escapeHtml(product.title)}</div><div class="rating">Review summary unavailable</div>`;
      }
    });
    await Promise.all(tasks);
  }

  async function loadMetrics() {
    try {
      const response = await fetch("/api/dashboard-metrics");
      const metrics = await response.json();
      if (!response.ok) {
        setDashboardUnavailable("Unable to load dashboard metrics right now.");
        return;
      }

      document.getElementById("kpiOrders").textContent = Number(metrics.total_orders || 0).toLocaleString();
      document.getElementById("kpiReturnRate").textContent = `${Number(metrics.estimated_return_rate || 0)}%`;
      document.getElementById("kpiReturnSub").textContent = "Projected with current catalog mix";
      document.getElementById("kpiHighRisk").textContent = Number(metrics.high_risk_skus || 0);
      document.getElementById("kpiReduction").textContent = `${Number(metrics.reduction_potential || 0)}%`;

      const products = Array.isArray(metrics.products) ? metrics.products : [];
      if (!products.length) {
        renderNoDataRow("No dashboard product data available.");
      } else {
        document.getElementById("tableBody").innerHTML = products.map(renderRow).join("");
      }

      const actions = Array.isArray(metrics.top_actions) ? metrics.top_actions : [];
      document.getElementById("actionsList").innerHTML = actions.length
        ? actions.map((item) => `<li class="action-item">${escapeHtml(item)}</li>`).join("")
        : '<li class="action-item">No recommended actions available yet.</li>';

      setupCharts(metrics);
      applyFilter();
      await loadReviewTiles();
    } catch {
      setDashboardUnavailable("Unable to load dashboard metrics right now.");
    }
  }

  window.filterTable = function filterTable(band, button) {
    currentBand = band;
    document.querySelectorAll(".filter-btn").forEach((node) => node.classList.remove("active"));
    if (button) button.classList.add("active");
    applyFilter();
  };

  document.addEventListener("DOMContentLoaded", loadMetrics);
})();
