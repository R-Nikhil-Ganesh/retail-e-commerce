(() => {
  const customerPanel = document.getElementById("customerPanel");
  const chooseCustomerBtn = document.getElementById("chooseCustomerBtn");
  const createProfileForm = document.getElementById("createProfileForm");
  const statusNode = document.getElementById("loginStatus");

  function setStatus(message, isError = false) {
    if (!statusNode) return;
    statusNode.textContent = message;
    statusNode.style.color = isError ? "#d08d8d" : "";
  }

  async function loginWithProfile(profile) {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });

    if (!response.ok) {
      const payload = await response.json().catch(() => ({}));
      throw new Error(payload.detail || "Could not sign in");
    }
  }

  function toStorePage() {
    const safeNext = typeof NEXT_PATH === "string" && NEXT_PATH.startsWith("/") ? NEXT_PATH : "/store";
    window.location.href = safeNext;
  }

  window.usePresetProfile = async function usePresetProfile(index) {
    const sample = SAMPLE_USERS[index];
    if (!sample) return;

    const payload = {
      name: sample.name,
      height_cm: sample.height_cm,
      weight_kg: sample.weight_kg,
      body_type: sample.body_type,
      usual_size: sample.usual_size,
      fit_preference: sample.fit_preference,
      gender: "unisex",
    };

    try {
      setStatus("Signing in...");
      await loginWithProfile(payload);
      toStorePage();
    } catch (error) {
      setStatus(error.message || "Failed to select preset profile. Please try again.", true);
    }
  };

  chooseCustomerBtn?.addEventListener("click", () => {
    customerPanel?.classList.remove("hidden");
    customerPanel?.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  createProfileForm?.addEventListener("submit", async (event) => {
    event.preventDefault();

    const payload = {
      name: document.getElementById("name").value.trim() || "Demo Shopper",
      height_cm: Number(document.getElementById("height").value),
      weight_kg: Number(document.getElementById("weight").value),
      body_type: document.getElementById("bodyType").value,
      usual_size: document.getElementById("usualSize").value,
      fit_preference: document.getElementById("fitPref").value,
      gender: document.getElementById("gender").value,
    };

    if (!Number.isFinite(payload.height_cm) || !Number.isFinite(payload.weight_kg)) {
      setStatus("Please enter valid height and weight values.", true);
      return;
    }

    try {
      setStatus("Signing in...");
      await loginWithProfile(payload);
      toStorePage();
    } catch (error) {
      setStatus(error.message || "Failed to save profile. Please try again.", true);
    }
  });
})();
