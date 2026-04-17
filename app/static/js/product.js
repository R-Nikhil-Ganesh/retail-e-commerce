(() => {
  const product = ALL_PRODUCTS.find((item) => item.id === PRODUCT_ID);
  let shopperProfile = INITIAL_PROFILE || null;
  const selectedState = {
    size: null,
  };

  const elements = {};

  function getCurrentSize() {
    return selectedState.size || SIZES[Math.floor(SIZES.length / 2)] || SIZES[0];
  }

  function setActiveSize(size) {
    selectedState.size = size;
    document.querySelectorAll(".size-btn").forEach((button) => {
      button.classList.toggle("active", button.dataset.size === size);
    });
  }

  function renderInsightList(container, insights) {
    container.innerHTML = "";
    insights.forEach((insight) => {
      const item = document.createElement("div");
      item.className = "fit-insight-item";
      item.textContent = insight;
      container.appendChild(item);
    });
  }

  function renderProfile(profile) {
    if (!profile) {
      return;
    }
    elements.profileName.textContent = profile.name || "Demo Shopper";
    elements.profileHeight.textContent = `${profile.height_cm} cm`;
    elements.profileWeight.textContent = `${profile.weight_kg} kg`;
    elements.profileBodyType.textContent = profile.body_type || "regular";
    elements.profileUsualSize.textContent = profile.usual_size || "M";
    elements.profileFitPref.textContent = profile.fit_preference || "regular";
    if (SIZES.includes(profile.usual_size)) {
      setActiveSize(profile.usual_size);
    }
  }

  function selectedProfileOrDefault() {
    return {
      height_cm: Number(shopperProfile?.height_cm) || 170,
      weight_kg: Number(shopperProfile?.weight_kg) || 65,
      body_type: shopperProfile?.body_type || "regular",
      usual_brand_size: shopperProfile?.usual_size || getCurrentSize(),
      fit_preference: shopperProfile?.fit_preference || "regular",
      gender: shopperProfile?.gender || "unisex",
    };
  }

  async function loadShopperProfile() {
    const response = await fetch("/api/profile");
    if (!response.ok) {
      shopperProfile = INITIAL_PROFILE;
      renderProfile(shopperProfile);
      return;
    }
    shopperProfile = await response.json();
    renderProfile(shopperProfile);
  }

  function showToast(message) {
    const toast = document.getElementById("toast");
    if (!toast) return;
    toast.textContent = message;
    toast.classList.remove("hidden");
    window.clearTimeout(showToast.timer);
    showToast.timer = window.setTimeout(() => toast.classList.add("hidden"), 2200);
  }

  function renderRiskBadge(score, band, reasons) {
    const badge = elements.riskBadge;
    if (!badge) return;
    badge.classList.remove("risk-low", "risk-medium", "risk-high");
    badge.classList.add(`risk-${band}`);
    const headline = `${score}/100 · ${band.toUpperCase()}`;
    const reason = reasons && reasons.length ? ` · ${reasons[0]}` : "";
    elements.riskLabel.textContent = `Return risk: ${headline}${reason}`;
    elements.riskIcon.textContent = band === "high" ? "⚠" : band === "medium" ? "◔" : "◉";
  }

  function chooseAlternativeProduct() {
    if (!product) return null;
    const sameCategory = ALL_PRODUCTS.filter((item) => item.category === product.category && item.id !== product.id);
    const lowerRiskSameCategory = sameCategory
      .filter((item) => item.historical_return_rate < product.historical_return_rate)
      .sort((a, b) => a.historical_return_rate - b.historical_return_rate);
    if (lowerRiskSameCategory.length) {
      return lowerRiskSameCategory[0];
    }
    const lowerRiskAny = ALL_PRODUCTS.filter((item) => item.id !== product.id).sort((a, b) => a.historical_return_rate - b.historical_return_rate);
    return lowerRiskAny[0] || null;
  }

  async function updateRiskPreview() {
    if (!product) return;
    const profile = selectedProfileOrDefault();
    const response = await fetch("/api/return-risk", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        product_id: PRODUCT_ID,
        selected_size: getCurrentSize(),
        height_cm: profile.height_cm,
        weight_kg: profile.weight_kg,
        body_type: profile.body_type,
        fit_preference: profile.fit_preference,
      }),
    });
    if (!response.ok) return;
    const payload = await response.json();
    renderRiskBadge(payload.score, payload.band, payload.top_reasons);
  }

  async function getFitRecommendation() {
    const profile = selectedProfileOrDefault();
    const button = document.getElementById("fitBtn");
    button.disabled = true;
    button.textContent = "Analyzing fit...";

    try {
      const response = await fetch("/api/fit-recommendation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_id: PRODUCT_ID,
          height_cm: profile.height_cm,
          weight_kg: profile.weight_kg,
          body_type: profile.body_type,
          usual_brand_size: profile.usual_brand_size,
          fit_preference: profile.fit_preference,
          gender: profile.gender,
        }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Fit recommendation failed");
      }

      elements.fitResult.classList.remove("hidden");
      elements.recSize.textContent = payload.recommended_size;
      elements.confPct.textContent = payload.confidence;
      elements.confBar.style.width = `${payload.confidence}%`;
      elements.fitExplain.innerHTML = payload.explanation;
      elements.fitWarning.textContent = payload.warning || "";
      elements.fitWarning.classList.toggle("hidden", !payload.warning);

      renderInsightList(elements.fitInsights, payload.fit_insights || []);
      if (payload.alternate_size) {
        elements.altSizeVal.textContent = payload.alternate_size;
        elements.altSize.classList.remove("hidden");
      } else {
        elements.altSize.classList.add("hidden");
      }

      const alternativeProduct = chooseAlternativeProduct();
      if (alternativeProduct) {
        elements.altProductVal.textContent = `${alternativeProduct.title} - est. return rate ${Math.round(alternativeProduct.historical_return_rate * 100)}%`;
        elements.altProduct.classList.remove("hidden");
      } else {
        elements.altProduct.classList.add("hidden");
      }

      if (payload.recommended_size) {
        setActiveSize(payload.recommended_size);
      }
      await updateRiskPreview();
      showToast(`Recommended size ${payload.recommended_size}`);
    } catch (error) {
      elements.fitExplain.innerHTML = `<strong>Could not generate fit guidance.</strong> ${error.message}`;
      elements.fitResult.classList.remove("hidden");
      elements.fitWarning.textContent = error.message;
      elements.fitWarning.classList.remove("hidden");
    } finally {
      button.disabled = false;
      button.textContent = "Get My Size →";
    }
  }

  async function loadReviewSummary() {
    const response = await fetch(`/api/review-summary/${PRODUCT_ID}`);
    const payload = await response.json();
    if (!response.ok) {
      return;
    }

    document.getElementById("reviewLoading")?.classList.add("hidden");
    document.getElementById("reviewContent")?.classList.remove("hidden");
    document.getElementById("fitTag").textContent = payload.fit_tag;
    document.getElementById("fitSummaryText").textContent = payload.fit_summary;
    const totalSentiment = Math.max(1, payload.sentiment_breakdown.positive + payload.sentiment_breakdown.neutral + payload.sentiment_breakdown.negative);
    document.getElementById("sPos").style.width = `${Math.max(8, (payload.sentiment_breakdown.positive / totalSentiment) * 100)}%`;
    document.getElementById("sNeu").style.width = `${Math.max(8, (payload.sentiment_breakdown.neutral / totalSentiment) * 100)}%`;
    document.getElementById("sNeg").style.width = `${Math.max(8, (payload.sentiment_breakdown.negative / totalSentiment) * 100)}%`;
    document.getElementById("sPosCount").textContent = payload.sentiment_breakdown.positive;
    document.getElementById("sNeuCount").textContent = payload.sentiment_breakdown.neutral;
    document.getElementById("sNegCount").textContent = payload.sentiment_breakdown.negative;
    const concerns = document.getElementById("topConcerns");
    concerns.innerHTML = "";
    (payload.top_concerns || []).forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      concerns.appendChild(li);
    });
    document.getElementById("shopperQuote").textContent = payload.shopper_quote;
  }

  window.selectSize = function selectSize(button) {
    setActiveSize(button.dataset.size);
    updateRiskPreview();
  };

  window.getFitRecommendation = getFitRecommendation;

  window.setMain = function setMain(thumb) {
    window.dhukanSetMainImage(thumb);
  };

  window.scrollToFit = function scrollToFit() {
    document.getElementById("fitPanel")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  window.addToCart = function addToCart() {
    showToast(`Added ${product.title} to bag`);
  };

  document.addEventListener("DOMContentLoaded", async () => {
    elements.profileName = document.getElementById("profileName");
    elements.profileHeight = document.getElementById("profileHeight");
    elements.profileWeight = document.getElementById("profileWeight");
    elements.profileBodyType = document.getElementById("profileBodyType");
    elements.profileUsualSize = document.getElementById("profileUsualSize");
    elements.profileFitPref = document.getElementById("profileFitPref");
    elements.fitResult = document.getElementById("fitResult");
    elements.recSize = document.getElementById("recSize");
    elements.confPct = document.getElementById("confPct");
    elements.confBar = document.getElementById("confBar");
    elements.fitExplain = document.getElementById("fitExplain");
    elements.fitWarning = document.getElementById("fitWarning");
    elements.fitInsights = document.getElementById("fitInsights");
    elements.altSize = document.getElementById("altSize");
    elements.altSizeVal = document.getElementById("altSizeVal");
    elements.altProduct = document.getElementById("altProduct");
    elements.altProductVal = document.getElementById("altProductVal");
    elements.fitBtn = document.getElementById("fitBtn");
    elements.riskBadge = document.getElementById("riskBadge");
    elements.riskLabel = document.getElementById("riskLabel");
    elements.riskIcon = document.getElementById("riskIcon");

    const preferredSize = SIZES.includes("M") ? "M" : SIZES[Math.floor(SIZES.length / 2)];
    setActiveSize(preferredSize);

    await Promise.all([
      loadShopperProfile(),
      loadReviewSummary(),
    ]);
    await updateRiskPreview();
  });
})();
