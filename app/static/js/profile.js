(() => {
  const elements = {};

  function fillForm(profile) {
    elements.name.value = profile.name || "Demo Shopper";
    elements.height.value = profile.height_cm ?? "";
    elements.weight.value = profile.weight_kg ?? "";
    elements.bodyType.value = profile.body_type || "regular";
    elements.usualSize.value = profile.usual_size || "M";
    elements.fitPref.value = profile.fit_preference || "regular";
    elements.gender.value = profile.gender || "unisex";
  }

  async function loadProfile() {
    const response = await fetch("/api/profile");
    if (!response.ok) {
      fillForm(INITIAL_PROFILE);
      return;
    }
    const profile = await response.json();
    fillForm(profile);
  }

  async function saveProfile(event) {
    event.preventDefault();
    const payload = {
      name: elements.name.value.trim() || "Demo Shopper",
      height_cm: Number(elements.height.value),
      weight_kg: Number(elements.weight.value),
      body_type: elements.bodyType.value,
      usual_size: elements.usualSize.value,
      fit_preference: elements.fitPref.value,
      gender: elements.gender.value,
    };

    const response = await fetch("/api/profile", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      return;
    }

    elements.saved.classList.remove("hidden");
    window.setTimeout(() => elements.saved.classList.add("hidden"), 2500);
  }

  window.applySample = function applySample(index) {
    const sample = SAMPLE_USERS[index];
    if (!sample) return;
    fillForm({
      name: sample.name,
      height_cm: sample.height_cm,
      weight_kg: sample.weight_kg,
      body_type: sample.body_type,
      usual_size: sample.usual_size,
      fit_preference: sample.fit_preference,
      gender: "unisex",
    });
  };

  document.addEventListener("DOMContentLoaded", async () => {
    elements.form = document.getElementById("profileForm");
    elements.name = document.getElementById("name");
    elements.height = document.getElementById("height");
    elements.weight = document.getElementById("weight");
    elements.bodyType = document.getElementById("bodyType");
    elements.usualSize = document.getElementById("usualSize");
    elements.fitPref = document.getElementById("fitPref");
    elements.gender = document.getElementById("gender");
    elements.saved = document.getElementById("profileSaved");

    elements.form.addEventListener("submit", saveProfile);
    await loadProfile();
  });
})();
