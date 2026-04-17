(() => {
  const storageKey = "dhukan-theme";

  function applyTheme(theme) {
    document.body.classList.toggle("theme-dark", theme === "dark");
    document.documentElement.dataset.theme = theme;
  }

  function getPreferredTheme() {
    const saved = window.localStorage.getItem(storageKey);
    if (saved === "dark" || saved === "light") {
      return saved;
    }
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  }

  document.addEventListener("DOMContentLoaded", () => {
    const initialTheme = getPreferredTheme();
    applyTheme(initialTheme);

    const toggle = document.getElementById("themeToggle");
    if (toggle) {
      toggle.textContent = initialTheme === "dark" ? "Light" : "Dark";
      toggle.addEventListener("click", () => {
        const nextTheme = document.body.classList.contains("theme-dark") ? "light" : "dark";
        window.localStorage.setItem(storageKey, nextTheme);
        applyTheme(nextTheme);
        toggle.textContent = nextTheme === "dark" ? "Light" : "Dark";
      });
    }

    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", async () => {
        try {
          await fetch("/api/auth/logout", { method: "POST" });
        } finally {
          window.location.href = "/login";
        }
      });
    }
  });

  window.dhukanSetMainImage = function dhukanSetMainImage(thumb) {
    const mainImage = document.getElementById("mainImg");
    if (!mainImage || !thumb) {
      return;
    }
    mainImage.src = thumb.src;
    document.querySelectorAll(".thumb").forEach((node) => node.classList.remove("active"));
    thumb.classList.add("active");
  };
})();
