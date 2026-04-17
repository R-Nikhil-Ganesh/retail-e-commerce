(() => {
  const customerPanel = document.getElementById("customerPanel");
  const chooseCustomerBtn = document.getElementById("chooseCustomerBtn");
  const createProfileForm = document.getElementById("createProfileForm");

  async function saveProfile(profile) {
    const response = await fetch("/api/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    });

    if (!response.ok) {
      throw new Error("Could not save profile");
    }
  }

  function toShopperExperience() {
    window.location.href = "/product/P001";
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
      await saveProfile(payload);
      toShopperExperience();
    } catch (error) {
      window.alert("Failed to select preset profile. Please try again.");
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

    try {
      await saveProfile(payload);
      toShopperExperience();
    } catch (error) {
      window.alert("Failed to save profile. Please try again.");
    }
  });
})();
