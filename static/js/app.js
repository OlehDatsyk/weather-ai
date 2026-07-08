/**
 * app.js
 * ------
 * Frontend logic for the Skyline weather assistant. No frameworks —
 * plain DOM APIs, kept modular via small focused functions.
 */

(() => {
  "use strict";

  // ------------------------------------------------------------------
  // State
  // ------------------------------------------------------------------
  const state = {
    currentCity: null, // last successfully loaded city name (for chat context)
    chatHistory: [], // [{role, content}]
    searchHistory: JSON.parse(localStorage.getItem("skyline_history") || "[]"),
    theme: localStorage.getItem("skyline_theme") || "dark",
  };

  const MAX_HISTORY_ITEMS = 8;

  // ------------------------------------------------------------------
  // DOM refs
  // ------------------------------------------------------------------
  const $ = (id) => document.getElementById(id);

  const el = {
    themeToggle: $("themeToggle"),
    themeIconSun: $("themeIconSun"),
    themeIconMoon: $("themeIconMoon"),

    searchForm: $("searchForm"),
    cityInput: $("cityInput"),

    compareForm: $("compareForm"),

    historyList: $("historyList"),

    heroEmpty: $("heroEmpty"),
    heroContent: $("heroContent"),
    heroLoading: $("heroLoading"),
    heroError: $("heroError"),
    heroErrorText: $("heroErrorText"),

    heroCity: $("heroCity"),
    heroCountry: $("heroCountry"),
    heroIcon: $("heroIcon"),
    heroTemp: $("heroTemp"),
    heroCondition: $("heroCondition"),
    heroFeels: $("heroFeels"),
    statGrid: $("statGrid"),

    comfortCard: $("comfortCard"),
    ringFg: $("ringFg"),
    comfortScoreValue: $("comfortScoreValue"),
    comfortLabel: $("comfortLabel"),
    comfortExplanation: $("comfortExplanation"),

    insightGrid: $("insightGrid"),
    insightClothing: $("insightClothing"),
    insightTravel: $("insightTravel"),
    insightSports: $("insightSports"),

    compareResult: $("compareResult"),
    compareCities: $("compareCities"),
    compareText: $("compareText"),

    chatMessages: $("chatMessages"),
    chatForm: $("chatForm"),
    chatInput: $("chatInput"),
    sendBtn: $("sendBtn"),
    clearChatBtn: $("clearChatBtn"),
    suggestedPrompts: $("suggestedPrompts"),

    toastContainer: $("toastContainer"),
    skyBar: $("skyBar"),
  };

  // ------------------------------------------------------------------
  // Utilities
  // ------------------------------------------------------------------

  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast ${type === "error" ? "error" : ""}`.trim();
    toast.textContent = message;
    el.toastContainer.appendChild(toast);
    setTimeout(() => toast.remove(), 4200);
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  /** Very small markdown-ish renderer: **bold**, bullet lines, newlines. */
  function renderRichText(text) {
    const safe = escapeHtml(text);
    const withBold = safe.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    const lines = withBold.split(/\n+/).filter(Boolean);
    let html = "";
    let inList = false;
    for (const line of lines) {
      const trimmed = line.trim();
      if (/^[-*•]\s+/.test(trimmed)) {
        if (!inList) { html += "<ul>"; inList = true; }
        html += `<li>${trimmed.replace(/^[-*•]\s+/, "")}</li>`;
      } else {
        if (inList) { html += "</ul>"; inList = false; }
        html += `<p>${trimmed}</p>`;
      }
    }
    if (inList) html += "</ul>";
    return html || `<p>${withBold}</p>`;
  }

  async function apiPost(path, body) {
    const resp = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    let data;
    try {
      data = await resp.json();
    } catch {
      throw new Error("The server returned an unreadable response.");
    }
    if (!resp.ok) {
      throw new Error(data?.error || `Request failed (HTTP ${resp.status}).`);
    }
    return data;
  }

  // ------------------------------------------------------------------
  // Theme
  // ------------------------------------------------------------------

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    el.themeIconSun.style.display = theme === "dark" ? "block" : "none";
    el.themeIconMoon.style.display = theme === "dark" ? "none" : "block";
    localStorage.setItem("skyline_theme", theme);
    state.theme = theme;
  }

  el.themeToggle.addEventListener("click", () => {
    applyTheme(state.theme === "dark" ? "light" : "dark");
  });

  applyTheme(state.theme);

  // ------------------------------------------------------------------
  // Weather icon rendering (simple inline SVGs, no external image calls)
  // ------------------------------------------------------------------

  function iconMarkup(main) {
    const key = (main || "").toLowerCase();
    const common = 'width="56" height="56" viewBox="0 0 64 64"';
    if (key.includes("clear")) {
      return `<svg ${common}><circle cx="32" cy="32" r="14" fill="var(--accent-sun)"/></svg>`;
    }
    if (key.includes("cloud")) {
      return `<svg ${common}><path d="M18 42c-6 0-10-4.5-10-10s4.5-10 10-10c1.6-6 7-10 13-10 7.5 0 13.5 6 13.5 13.5 0 .5 0 1-.1 1.5 4.6.7 8.1 4.7 8.1 9.5 0 5.5-4.5 10-10 10H18z" fill="var(--accent-sky)"/></svg>`;
    }
    if (key.includes("rain") || key.includes("drizzle")) {
      return `<svg ${common}><path d="M16 34c-5.5 0-10-4.5-10-10s4.5-10 10-10c1.5-5.5 6.5-9.5 12.5-9.5 7 0 12.8 5.5 13.2 12.5 4.6.6 8.3 4.6 8.3 9.5 0 5.2-4.3 9.5-9.5 9.5H16z" fill="var(--accent-storm)"/><g stroke="var(--accent-sky)" stroke-width="2.4" stroke-linecap="round"><line x1="20" y1="46" x2="17" y2="54"/><line x1="32" y1="46" x2="29" y2="54"/><line x1="44" y1="46" x2="41" y2="54"/></g></svg>`;
    }
    if (key.includes("thunder") || key.includes("storm")) {
      return `<svg ${common}><path d="M16 32c-5.5 0-10-4.5-10-10s4.5-10 10-10c1.5-5.5 6.5-9.5 12.5-9.5 7 0 12.8 5.5 13.2 12.5 4.6.6 8.3 4.6 8.3 9.5 0 5.2-4.3 9.5-9.5 9.5H16z" fill="var(--accent-storm)"/><polygon points="30,34 22,50 30,50 26,60 42,42 33,42 38,34" fill="var(--accent-sun)"/></svg>`;
    }
    if (key.includes("snow")) {
      return `<svg ${common}><path d="M18 34c-6 0-10.5-4.5-10.5-10s4.5-10 10.5-10c1.6-6 7-10 13-10 7.5 0 13.5 6 13.5 13.5 4.6.7 8.1 4.7 8.1 9.5 0 5.5-4.5 10-10 10H18z" fill="var(--bg-panel-raised)" stroke="var(--border)"/><g stroke="var(--accent-sky)" stroke-width="2" stroke-linecap="round"><line x1="20" y1="44" x2="20" y2="56"/><line x1="14" y1="50" x2="26" y2="50"/><line x1="44" y1="44" x2="44" y2="56"/><line x1="38" y1="50" x2="50" y2="50"/></g></svg>`;
    }
    // mist/fog/haze/default
    return `<svg ${common}><g stroke="var(--text-muted)" stroke-width="3" stroke-linecap="round"><line x1="10" y1="24" x2="54" y2="24"/><line x1="10" y1="34" x2="54" y2="34"/><line x1="10" y1="44" x2="54" y2="44"/></g></svg>`;
  }

  function updateSkyBar(main) {
    const key = (main || "").toLowerCase();
    let gradient;
    if (key.includes("clear")) gradient = "linear-gradient(90deg, var(--accent-sun), #ffd98a)";
    else if (key.includes("rain") || key.includes("drizzle") || key.includes("thunder")) gradient = "linear-gradient(90deg, var(--accent-storm), var(--accent-sky))";
    else if (key.includes("snow")) gradient = "linear-gradient(90deg, #cfe3f5, var(--accent-sky))";
    else gradient = "linear-gradient(90deg, var(--accent-storm), var(--accent-sky), var(--accent-sun))";
    el.skyBar.style.background = gradient;
  }

  // ------------------------------------------------------------------
  // Weather hero rendering
  // ------------------------------------------------------------------

  function setHeroView(view) {
    // view: "empty" | "loading" | "content" | "error" | "compare"
    el.heroEmpty.hidden = view !== "empty";
    el.heroLoading.hidden = view !== "loading";
    el.heroContent.hidden = view !== "content";
    el.heroError.hidden = view !== "error";
    el.compareResult.hidden = view !== "compare";
  }

  function statChip(label, value) {
    return `<div class="stat-chip"><span class="stat-label">${label}</span><span class="stat-value">${value}</span></div>`;
  }

  function renderWeather(weather) {
    el.heroCity.textContent = weather.city;
    el.heroCountry.textContent = weather.country;
    el.heroIcon.innerHTML = iconMarkup(weather.condition_main);
    el.heroTemp.textContent = `${Math.round(weather.temperature_c)}°C`;
    el.heroCondition.textContent = weather.condition_description;
    el.heroFeels.textContent = `Feels like ${Math.round(weather.feels_like_c)}°C`;

    el.statGrid.innerHTML = [
      statChip("Humidity", `${weather.humidity_pct}%`),
      statChip("Wind", `${weather.wind_speed_ms.toFixed(1)} m/s`),
      statChip("Pressure", `${weather.pressure_hpa} hPa`),
      statChip("Cloud cover", `${weather.cloudiness_pct}%`),
      statChip("Min / Max", `${Math.round(weather.temp_min_c)}° / ${Math.round(weather.temp_max_c)}°`),
      statChip("Visibility", `${(weather.visibility_m / 1000).toFixed(1)} km`),
    ].join("");

    updateSkyBar(weather.condition_main);
  }

  function animateComfortRing(score) {
    const circumference = 264;
    const offset = circumference - (circumference * score) / 100;
    let color = "var(--accent-sky)";
    if (score < 40) color = "var(--danger)";
    else if (score < 70) color = "var(--accent-sun)";
    else color = "var(--success)";
    el.ringFg.style.stroke = color;
    requestAnimationFrame(() => {
      el.ringFg.style.strokeDashoffset = String(offset);
    });
    el.comfortScoreValue.textContent = String(score);
  }

  function renderInsights(insights) {
    if (!insights) {
      el.comfortCard.hidden = true;
      el.insightGrid.hidden = true;
      return;
    }
    el.comfortCard.hidden = false;
    el.insightGrid.hidden = false;

    el.comfortLabel.textContent = `${insights.comfort_label} · Comfort score`;
    el.comfortExplanation.textContent = insights.explanation;
    animateComfortRing(insights.comfort_score);

    el.insightClothing.textContent = insights.clothing;
    el.insightTravel.textContent = insights.travel;
    el.insightSports.textContent = insights.sports;
  }

  // ------------------------------------------------------------------
  // Search history (localStorage)
  // ------------------------------------------------------------------

  function saveToHistory(weather) {
    const entry = { city: weather.city, country: weather.country, temp: Math.round(weather.temperature_c) };
    state.searchHistory = state.searchHistory.filter((h) => h.city.toLowerCase() !== entry.city.toLowerCase());
    state.searchHistory.unshift(entry);
    state.searchHistory = state.searchHistory.slice(0, MAX_HISTORY_ITEMS);
    localStorage.setItem("skyline_history", JSON.stringify(state.searchHistory));
    renderHistory();
  }

  function renderHistory() {
    if (state.searchHistory.length === 0) {
      el.historyList.innerHTML = `<li class="history-empty">No searches yet</li>`;
      return;
    }
    el.historyList.innerHTML = state.searchHistory
      .map(
        (h) => `<li class="history-item" data-city="${escapeHtml(h.city)}">
          <span>${escapeHtml(h.city)}</span>
          <span class="history-temp">${h.temp}°</span>
        </li>`
      )
      .join("");

    el.historyList.querySelectorAll(".history-item").forEach((li) => {
      li.addEventListener("click", () => {
        el.cityInput.value = li.dataset.city;
        searchCity(li.dataset.city);
      });
    });
  }

  // ------------------------------------------------------------------
  // Weather search
  // ------------------------------------------------------------------

  async function searchCity(city) {
    setHeroView("loading");
    try {
      const data = await apiPost("/api/weather", { city });
      state.currentCity = data.weather.city;
      renderWeather(data.weather);
      renderInsights(data.insights);
      setHeroView("content");
      saveToHistory(data.weather);
      if (data.insights_error) {
        showToast("Weather loaded, but AI insights are unavailable right now.", "error");
      }
      refreshSuggestions();
    } catch (err) {
      el.heroErrorText.textContent = err.message || "Something went wrong fetching that city.";
      setHeroView("error");
    }
  }

  el.searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const city = el.cityInput.value.trim();
    if (!city) return;
    searchCity(city);
  });

  // ------------------------------------------------------------------
  // Compare cities
  // ------------------------------------------------------------------

  el.compareForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const inputs = Array.from(el.compareForm.querySelectorAll(".compare-input"));
    const cities = inputs.map((i) => i.value.trim()).filter(Boolean);
    if (cities.length < 2) {
      showToast("Enter at least two cities to compare.", "error");
      return;
    }
    setHeroView("loading");
    try {
      const data = await apiPost("/api/compare", { cities });
      el.compareCities.innerHTML = data.cities
        .map(
          (w) =>
            `<div class="compare-city-chip"><b>${escapeHtml(w.city)}</b><span class="compare-temp">${Math.round(w.temperature_c)}°C</span></div>`
        )
        .join("");
      el.compareText.innerHTML = renderRichText(data.comparison);
      setHeroView("compare");
    } catch (err) {
      el.heroErrorText.textContent = err.message || "Could not compare those cities.";
      setHeroView("error");
    }
  });

  // ------------------------------------------------------------------
  // Chat
  // ------------------------------------------------------------------

  function appendMessage(role, content) {
    const wrapper = document.createElement("div");
    wrapper.className = `msg ${role}`;
    wrapper.innerHTML = renderRichText(content);
    el.chatMessages.appendChild(wrapper);
    el.chatMessages.scrollTop = el.chatMessages.scrollHeight;
    return wrapper;
  }

  /** Reveal assistant text progressively for a lightweight "typing" feel. */
  function typeMessage(node, fullText, speedMs = 12) {
    return new Promise((resolve) => {
      let i = 0;
      const plain = fullText;
      node.innerHTML = "";
      const cursor = document.createElement("span");
      cursor.textContent = "▍";
      cursor.style.opacity = "0.6";

      function step() {
        i += Math.max(1, Math.round(plain.length / 120));
        const slice = plain.slice(0, i);
        node.innerHTML = renderRichText(slice);
        node.appendChild(cursor);
        el.chatMessages.scrollTop = el.chatMessages.scrollHeight;
        if (i < plain.length) {
          setTimeout(step, speedMs);
        } else {
          node.innerHTML = renderRichText(plain);
          resolve();
        }
      }
      step();
    });
  }

  function showTypingIndicator() {
    const indicator = document.createElement("div");
    indicator.className = "typing-indicator";
    indicator.id = "typingIndicator";
    indicator.innerHTML = "<span></span><span></span><span></span>";
    el.chatMessages.appendChild(indicator);
    el.chatMessages.scrollTop = el.chatMessages.scrollHeight;
    return indicator;
  }

  async function sendChatMessage(message) {
    appendMessage("user", message);
    state.chatHistory.push({ role: "user", content: message });

    el.sendBtn.disabled = true;
    const indicator = showTypingIndicator();

    try {
      const data = await apiPost("/api/chat", {
        message,
        history: state.chatHistory.slice(-12),
        context_city: state.currentCity,
      });
      indicator.remove();
      const node = appendMessage("assistant", "");
      await typeMessage(node, data.reply);
      state.chatHistory.push({ role: "assistant", content: data.reply });
    } catch (err) {
      indicator.remove();
      appendMessage("error", err.message || "I couldn't reach the AI service. Please try again.");
    } finally {
      el.sendBtn.disabled = false;
    }
  }

  el.chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const message = el.chatInput.value.trim();
    if (!message) return;
    el.chatInput.value = "";
    el.chatInput.style.height = "auto";
    sendChatMessage(message);
  });

  el.chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      el.chatForm.requestSubmit();
    }
  });

  el.chatInput.addEventListener("input", () => {
    el.chatInput.style.height = "auto";
    el.chatInput.style.height = `${Math.min(el.chatInput.scrollHeight, 140)}px`;
  });

  el.clearChatBtn.addEventListener("click", () => {
    state.chatHistory = [];
    el.chatMessages.innerHTML = `<div class="chat-welcome"><p>Ask me anything about the weather — clothing choices, travel plans, or how two cities compare.</p></div>`;
  });

  // ------------------------------------------------------------------
  // Suggested prompts
  // ------------------------------------------------------------------

  async function refreshSuggestions() {
    try {
      const data = await apiPost("/api/suggestions", { context_city: state.currentCity });
      renderSuggestions(data.suggestions || []);
    } catch {
      // Suggestions are a nice-to-have; fail silently.
    }
  }

  function renderSuggestions(suggestions) {
    el.suggestedPrompts.innerHTML = suggestions
      .map((s) => `<button type="button" class="suggested-chip">${escapeHtml(s)}</button>`)
      .join("");
    el.suggestedPrompts.querySelectorAll(".suggested-chip").forEach((chip) => {
      chip.addEventListener("click", () => {
        el.chatInput.value = chip.textContent;
        el.chatForm.requestSubmit();
      });
    });
  }

  // ------------------------------------------------------------------
  // Init
  // ------------------------------------------------------------------

  renderHistory();
  setHeroView("empty");
  refreshSuggestions();
})();
