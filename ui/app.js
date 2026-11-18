const byId = (id) => document.getElementById(id);
const stopKinds = {
  dinner: "Dinner",
  dessert: "Dessert",
  cafe: "Cafe",
  bar: "Bar",
  after: "After-dinner spot",
};
let requestedStops = ["dinner", "dessert"];
let currentResult = null;
let currentCatalog = null;
let map = null;
let mapLayer = null;
let running = false;
const icons = () => {
  if (window.lucide) window.lucide.createIcons();
};
const escapeHtml = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (character) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character],
  );
const icon = (name) => `<i data-lucide="${name}"></i>`;
const formatHour = (hour) => {
  const minutes = Math.round(hour * 60) % (24 * 60);
  const clockHour = Math.floor(minutes / 60);
  const clockMinutes = minutes % 60;
  return `${clockHour % 12 || 12}${clockMinutes ? ":" + String(clockMinutes).padStart(2, "0") : ""}${clockHour >= 12 ? "pm" : "am"}`;
};
byId("outing-date").value = new Intl.DateTimeFormat("en-CA", {
  timeZone: "America/Phoenix",
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
}).format(new Date());
const restrictedCatalog = (data) => data?.provider === "google" || data?.source === "Google Maps";
const googleAttribution = '<span class="google-attribution" translate="no">Google Maps</span>';
const guidance = (venue) =>
  venue.price_range_pp
    ? `$${venue.price_range_pp.low ?? "?"}-${venue.price_range_pp.high ?? "?"} / person (guidance)`
    : venue.price_level
      ? venue.price_level.replace("PRICE_LEVEL_", "").replaceAll("_", " ").toLowerCase() +
        " (price tier)"
      : "No price guidance";

function renderStopInputs() {
  byId("stop-inputs").innerHTML = requestedStops
    .map(
      (kind, index) =>
        `<div class="stop-row"><span class="stop-number">${index + 1}</span><select aria-label="Stop ${index + 1} type" data-stop="${index}">${Object.entries(
          stopKinds,
        )
          .map(
            ([value, label]) =>
              `<option value="${value}" ${kind === value ? "selected" : ""}>${label}</option>`,
          )
          .join(
            "",
          )}</select><button class="icon-button" type="button" data-up="${index}" title="Move stop up" aria-label="Move stop ${index + 1} up" ${index === 0 ? "disabled" : ""}>${icon("arrow-up")}</button><button class="icon-button" type="button" data-remove="${index}" title="Remove stop" aria-label="Remove stop ${index + 1}" ${requestedStops.length === 1 ? "disabled" : ""}>${icon("x")}</button></div>`,
    )
    .join("");
  byId("add-stop").disabled = requestedStops.length >= 4;
  icons();
}
byId("stop-inputs").addEventListener("change", (event) => {
  if (event.target.dataset.stop !== undefined)
    requestedStops[Number(event.target.dataset.stop)] = event.target.value;
});
byId("stop-inputs").addEventListener("click", (event) => {
  const button = event.target.closest("button");
  if (!button || button.disabled) return;
  if (button.dataset.remove !== undefined) requestedStops.splice(Number(button.dataset.remove), 1);
  if (button.dataset.up !== undefined) {
    const index = Number(button.dataset.up);
    [requestedStops[index - 1], requestedStops[index]] = [
      requestedStops[index],
      requestedStops[index - 1],
    ];
  }
  renderStopInputs();
});
byId("add-stop").addEventListener("click", () => {
  if (requestedStops.length < 4) {
    requestedStops.push("bar");
    renderStopInputs();
  }
});
for (let hour = 0; hour < 24; hour++)
  byId("hour").add(
    new Option(`${hour % 12 || 12}:00 ${hour >= 12 ? "PM" : "AM"}`, hour, false, hour === 19),
  );
byId("walk").addEventListener("input", () => {
  byId("walk-label").textContent = `${Number(byId("walk").value).toLocaleString()} m`;
});
document.querySelectorAll("input[name=mode]").forEach((input) =>
  input.addEventListener("change", () => {
    byId("billing-note").textContent =
      input.value === "mock"
        ? "Deterministic test mode. No LLM calls."
        : "Real model calls may incur AWS charges.";
    if (input.value === "mock") byId("data-mode").value = "fixture";
  }),
);
for (const field of ["search-area", "search-radius"])
  byId(field).addEventListener("change", () => {
    byId("area-summary").innerHTML =
      `${escapeHtml(byId("search-area").selectedOptions[0].textContent)}<small>${Number(byId("search-radius").value) / 1000} km search radius</small>`;
  });

function formPayload() {
  return {
    request: byId("request").value,
    cuisine: byId("cuisine").value,
    venue_provider: byId("venue-provider").value,
    outing_date: byId("outing-date").value,
    stop_types: [...requestedStops],
    budget_pp: Number(byId("budget").value),
    party_size: Number(byId("party").value),
    target_hour: Number(byId("hour").value),
    max_walk_m: Number(byId("walk").value),
    mood: byId("mood").value,
    vegan_required: byId("vegan").checked,
    mock: document.querySelector("input[name=mode]:checked").value === "mock",
    max_attempts: Number(byId("attempts").value),
    data_mode: byId("data-mode").value,
    search_area: byId("search-area").value,
    radius_m: Number(byId("search-radius").value),
    candidate_limit: Number(byId("candidate-limit").value),
  };
}

async function readRunResponse(response) {
  if (!response.ok || !response.headers.get("content-type")?.includes("application/x-ndjson")) {
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Request failed.");
    return data;
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result = null;
  while (true) {
    const chunk = await reader.read();
    buffer += decoder.decode(chunk.value, { stream: !chunk.done });
    const lines = buffer.split("\n");
    buffer = lines.pop();
    for (const line of lines) {
      if (!line.trim()) continue;
      const event = JSON.parse(line);
      if (event.type === "progress")
        byId("stage-title").textContent = `${event.node}: ${event.detail}`;
      if (event.type === "result") result = event.result;
      if (event.type === "error") throw new Error(event.error);
    }
    if (chunk.done) break;
  }
  if (!result) throw new Error("The connection ended before the planner returned a result.");
  return result;
}

function renderCatalog(data) {
  currentCatalog = data;
  byId("catalog-title").textContent = `Places in ${data.area?.name || "the search area"}`;
  const time = data.retrieved_at
    ? new Date(data.retrieved_at).toLocaleString()
    : "Undated fixtures";
  byId("catalog-meta").textContent =
    `${data.source} / ${data.returned_count ?? data.venues.length} returned${data.matching_count != null ? " of " + data.matching_count + " matches" : ""}${data.truncated ? " / result limit reached" : ""}. ${time}. ${data.coverage_note || ""}`;
  if (restrictedCatalog(data))
    byId("catalog-meta").insertAdjacentHTML("beforeend", "<br>" + googleAttribution);
  const query = byId("catalog-filter").value.toLowerCase();
  const venues = data.venues.filter((venue) =>
    `${venue.name} ${venue.cuisine || ""} ${venue.address || ""}`.toLowerCase().includes(query),
  );
  byId("catalog-output").innerHTML =
    `<table class="catalog-table"><thead><tr><th>Venue / category</th><th>Address / price guidance</th><th>Listed hours</th><th>Evidence</th></tr></thead><tbody>${venues.map((venue) => `<tr><td><strong>${escapeHtml(venue.name)}</strong><small>${escapeHtml(venue.category)} / ${escapeHtml(venue.cuisine || "Cuisine not listed")}</small></td><td>${escapeHtml(venue.address || "Address not listed")}<small>${escapeHtml(guidance(venue))}</small></td><td>${escapeHtml(venue.opening_hours || "Not listed")}</td><td>${/^https:\/\//.test(venue.source_url || "") ? `<a href="${escapeHtml(venue.source_url)}" target="_blank" rel="noopener noreferrer">Map source</a>` : ""} ${/^https:\/\//.test(venue.website || "") ? `<a href="${escapeHtml(venue.website)}" target="_blank" rel="noopener noreferrer">Website</a>` : ""}<small>${escapeHtml(venue.business_status || "Not independently verified")}</small></td></tr>`).join("")}</tbody></table>`;
  byId("download").disabled = restrictedCatalog(data);
}
byId("catalog-filter").addEventListener("input", () => {
  if (currentCatalog) renderCatalog(currentCatalog);
});
byId("browse-button").addEventListener("click", async () => {
  if (running) return;
  running = true;
  byId("browse-button").disabled = true;
  byId("run-button").disabled = true;
  byId("error-banner").hidden = true;
  byId("browse-button").querySelector("span").textContent = "Searching...";
  try {
    const response = await fetch("/api/venues", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(formPayload()),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Venue search failed.");
    renderCatalog(data);
    showView("venues");
  } catch (error) {
    byId("error-banner").textContent = error.message;
    byId("error-banner").hidden = false;
  } finally {
    running = false;
    byId("browse-button").disabled = false;
    byId("run-button").disabled = false;
    byId("browse-button").querySelector("span").textContent = "Browse places";
  }
});

function showView(name) {
  document.querySelectorAll(".view").forEach((view) => {
    view.hidden = view.id !== `view-${name}`;
  });
  document
    .querySelectorAll("[data-view]")
    .forEach((button) =>
      button.setAttribute("aria-selected", String(button.dataset.view === name)),
    );
  byId("summary").hidden = name === "venues" || !currentResult;
  byId("download").disabled =
    name === "venues"
      ? !currentCatalog || restrictedCatalog(currentCatalog)
      : !currentResult || currentResult.restricted_content === true;
  if (name === "plan" && map) setTimeout(() => map.invalidateSize(), 30);
}
document
  .querySelectorAll("[data-view]")
  .forEach((button) => button.addEventListener("click", () => showView(button.dataset.view)));

function initMap() {
  if (!window.L) {
    byId("map").textContent = "Map unavailable";
    return;
  }
  map = L.map("map", { scrollWheelZoom: false }).setView([33.4255, -111.94], 15);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);
  mapLayer = L.layerGroup().addTo(map);
}

function eventDescription(event) {
  const observation = event.observation;
  if (event.node === "discovery") return `${observation.candidate_ids?.length || 0} candidates`;
  if (event.node === "enrichment") return `${observation.length} venue records`;
  if (event.node === "planner") return `${observation.stops?.length || 0} stops proposed`;
  if (event.node === "transit") return `${observation.length} travel legs`;
  if (event.node === "critic") return observation.valid ? "Checks passed" : "Replan requested";
  if (event.node === "weather") return `${observation.temp_c ?? "?"} C / ${observation.condition}`;
  return "";
}

function renderResult(result) {
  currentResult = result;
  const valid = result.status === "valid";
  const provisional = result.status === "provisional";
  const metrics = result.metrics || {};
  const facts = result.facts || {};
  const stops = result.plan?.stops || [];
  const live = result.data_mode === "live";
  byId("result-title").textContent =
    valid || provisional
      ? `${provisional ? "Tentative evening" : "An evening"} in ${result.scenario?.constraints?.area?.name || "Tempe"}.`
      : "No verified itinerary.";
  byId("run-status").textContent =
    `${result.display_source || "Run"} / ${live ? "Live data" : "Fixtures"} / ${metrics.mode === "llm" ? "Real LLM" : "Mock"}`;
  byId("run-status").className = `run-status ${valid ? "success" : ""}`;
  const total = result.report?.details?.total_pp;
  const estimatedRange = result.report?.details?.estimated_range_pp;
  byId("summary").hidden = false;
  byId("summary").innerHTML = [
    [
      total == null
        ? estimatedRange
          ? `$${estimatedRange.low}-${estimatedRange.high}`
          : "Unknown"
        : `$${Number(total).toLocaleString("en-US", { maximumFractionDigits: 2 })}`,
      provisional ? "Price guidance / person" : "Estimated / person",
    ],
    [stops.length, "Stops"],
    [`${Number(metrics.latency_seconds || 0).toFixed(1)}s`, "Run time"],
    [metrics.llm_calls || 0, "LLM calls"],
  ]
    .map(
      ([value, label]) =>
        `<div class="stat"><strong>${escapeHtml(value)}</strong><span>${label}</span></div>`,
    )
    .join("");
  const labels = {
    structure: "Stops",
    budget: "Budget",
    dietary: "Diet",
    hours: "Hours",
    travel: "Travel",
  };
  byId("checks").innerHTML = Object.entries(result.report?.checks || {})
    .map(
      ([key, passed]) =>
        `<span class="check ${passed ? "" : "fail"}">${icon(passed ? "check" : "x")}${labels[key] || escapeHtml(key)}</span>`,
    )
    .join("");
  byId("stops-output").innerHTML = stops.length
    ? stops
        .map((stop, index) => {
          const venue = facts[stop.venue_id] || {};
          const kind =
            result.scenario?.constraints?.stop_types?.[index] || (index ? "after" : "dinner");
          const price =
            venue.price_per_person == null
              ? guidance(venue)
              : `$${venue.price_per_person} / person`;
          const close =
            venue.provider === "google"
              ? result.report?.checks?.hours
                ? "Listed hours pass requested date/time"
                : "Hours could not be verified"
              : venue.close_hour == null
                ? "Hours unconfirmed"
                : `Closes ${formatHour(venue.close_hour)}`;
          const url = /^https:\/\//.test(venue.website || "") ? venue.website : null;
          const card = `<article class="stop-card"><span class="stop-badge">${index + 1}</span><div class="stop-label">${escapeHtml(valid || provisional ? stopKinds[kind] || kind : "Last candidate")}</div><h3>${escapeHtml(venue.name || stop.venue_id)}</h3><div class="venue-meta"><strong>${escapeHtml(price)}</strong><span>${escapeHtml(venue.cuisine || "")}</span></div><div class="venue-meta"><span>${escapeHtml(close)}</span><span>${venue.vegan === true ? "Vegan options" : venue.vegan === false ? "Not vegan verified" : "Diet unconfirmed"}</span></div><div class="venue-footer"><span>${venue.provider === "google" ? googleAttribution : live ? "Provider listing / page extraction" : "Annotated fixture evidence"}</span>${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Website ${icon("external-link")}</a>` : ""}</div></article>`;
          const leg = result.plan.legs?.[index];
          const hop =
            index < stops.length - 1
              ? `<div class="hop">${icon("footprints")}<span>${leg?.distance_m != null ? `${escapeHtml(leg.distance_m)} m / ${escapeHtml(leg.minutes)} min` : "Route unconfirmed"} <small>${escapeHtml(leg?.source || "estimate")}</small></span></div>`
              : "";
          return card + hop;
        })
        .join("")
    : '<div class="empty-state">No verified stops returned.</div>';
  byId("caveats").hidden = false;
  byId("caveats").textContent = valid
    ? `${live ? "Live listings and extracted website facts" : "Annotated fixture data"}; fixed arrival intervals and straight-line travel. Current availability and party capacity are not independently verified.`
    : "The planning budget was exhausted or evidence was insufficient. Last candidates are not recommendations.";
  if (!valid) {
    const failed = Object.entries(result.report?.checks || {})
      .filter(([, passed]) => !passed)
      .map(([name]) => labels[name] || name);
    byId("caveats").textContent =
      `Could not verify: ${failed.join(", ") || "a complete plan"}. Missing evidence or failed constraints prevented approval. Last candidates are not recommendations.`;
  }
  if (provisional)
    byId("caveats").textContent =
      "Provisional plan: price guidance fits the maximum, but the exact meal bill is not verified. Tax, tip, selected dishes and availability may change the total.";
  document.querySelector(".source-note span").textContent = live
    ? "Live provider listings; website facts may be incomplete"
    : "Bundled annotated venue snapshot";
  if (result.candidates)
    renderCatalog({
      venues: result.candidates,
      provider: result.restricted_content ? "google" : undefined,
      source: live ? result.candidates[0]?.source || "Live provider" : "Fixture catalog",
      area: result.scenario?.constraints?.area,
      returned_count: result.candidates.length,
      coverage_note: live
        ? "Bounded discovery results; not exhaustive."
        : "Archived annotations, not verified live data.",
    });
  const conditions = result.weather || {};
  byId("weather").innerHTML =
    `${icon(conditions.condition === "rain" ? "cloud-rain" : "sun")}<span>${conditions.temp_c ?? "?"} C / ${escapeHtml(conditions.condition || "Unknown")}<br><small>Bundled weather sample</small></span>`;
  byId("event-count").textContent = (result.trace || []).length;
  byId("activity-output").className = "";
  byId("activity-output").innerHTML = (result.trace || [])
    .map(
      (event, index) =>
        `<details class="activity-event"><summary><span class="event-index">${String(index + 1).padStart(2, "0")}</span><strong>${escapeHtml(event.node[0].toUpperCase() + event.node.slice(1))}</strong><span class="event-description">${escapeHtml(eventDescription(event))}</span></summary><pre>${escapeHtml(JSON.stringify(event.observation, null, 2))}</pre></details>`,
    )
    .join("");
  byId("json-output").textContent = JSON.stringify(
    result.restricted_content
      ? {
          status: result.status,
          metrics: result.metrics,
          checks: result.report?.checks,
          note: "Raw Google Maps content is excluded from JSON export.",
        }
      : result,
    null,
    2,
  );
  byId("download").disabled = result.restricted_content === true;
  byId("map").hidden = result.restricted_content === true;
  byId("google-locations").hidden = result.restricted_content !== true;
  if (result.restricted_content)
    byId("google-locations").innerHTML =
      googleAttribution +
      stops
        .map((stop) => {
          const venue = facts[stop.venue_id];
          return venue
            ? `<div class="google-location"><strong>${escapeHtml(venue.name)}</strong><p>${escapeHtml(venue.address)}</p><a href="${escapeHtml(venue.source_url)}" target="_blank" rel="noopener noreferrer">Open in Google Maps ${icon("external-link")}</a></div>`
            : "";
        })
        .join("");
  if (map && mapLayer && !result.restricted_content) {
    mapLayer.clearLayers();
    const coordinates = [];
    stops.forEach((stop, index) => {
      const venue = facts[stop.venue_id];
      if (!venue || venue.lat == null || venue.lon == null) return;
      const coordinate = [venue.lat, venue.lon];
      coordinates.push(coordinate);
      L.marker(coordinate, {
        icon: L.divIcon({
          className: "",
          html: `<div class="map-marker">${index + 1}</div>`,
          iconSize: [26, 26],
        }),
      })
        .bindPopup(escapeHtml(venue.name))
        .addTo(mapLayer);
    });
    if (coordinates.length > 1) {
      L.polyline(coordinates, { color: "#b65b3d", weight: 3, dashArray: "5,7" }).addTo(mapLayer);
      map.fitBounds(coordinates, { padding: [50, 50], maxZoom: 16 });
    } else if (coordinates.length) map.setView(coordinates[0], 15);
  }
  icons();
}

byId("plan-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (running) return;
  running = true;
  const payload = formPayload();
  const fields = [
    ...document.querySelectorAll(
      "#plan-form input, #plan-form select, #plan-form textarea, #plan-form button",
    ),
  ];
  fields.forEach((field) => {
    field.dataset.wasDisabled = field.disabled ? "true" : "false";
    field.disabled = true;
  });
  byId("loading").hidden = false;
  byId("stage-title").textContent = "Starting the planner";
  byId("error-banner").hidden = true;
  byId("run-status").textContent = "Running";
  byId("run-status").className = "run-status";
  byId("run-button").querySelector("span").textContent = "Planning...";
  const started = Date.now();
  const controller = new AbortController();
  const requestTimeout = setTimeout(() => controller.abort(), 180000);
  byId("elapsed").textContent = "0 seconds elapsed";
  const timer = setInterval(() => {
    byId("elapsed").textContent = `${Math.floor((Date.now() - started) / 1000)} seconds elapsed`;
  }, 1000);
  try {
    const response = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/x-ndjson" },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    const result = await readRunResponse(response);
    renderResult(result);
    showView("plan");
    if (window.innerWidth < 720)
      byId("result-title").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    byId("error-banner").textContent =
      error.name === "AbortError"
        ? "No completed response within three minutes. Try a narrower search or fewer stops."
        : error.message;
    byId("error-banner").hidden = false;
    byId("run-status").textContent = "Run failed";
  } finally {
    clearInterval(timer);
    clearTimeout(requestTimeout);
    byId("loading").hidden = true;
    fields.forEach((field) => {
      field.disabled = field.dataset.wasDisabled === "true";
    });
    byId("run-button").querySelector("span").textContent = "Plan evening";
    running = false;
  }
});
byId("download").addEventListener("click", () => {
  const exported = byId("view-venues").hidden ? currentResult : currentCatalog;
  if (!exported || exported.restricted_content || restrictedCatalog(exported)) return;
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(exported, null, 2)], { type: "application/json" }),
  );
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "night-out-result.json";
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

async function boot() {
  renderStopInputs();
  initMap();
  icons();
  try {
    const config = await (await fetch("/api/config")).json();
    byId("model-name").textContent = config.model.includes("haiku")
      ? `Haiku 4.5 / ${config.region}`
      : `${config.provider} / ${config.region}`;
    byId("venue-provider").value =
      config.discovery_provider === "Google Maps" ? "google" : "geoapify";
    const sample = await (await fetch("/api/sample")).json();
    if (sample.status !== "empty") renderResult(sample);
  } catch {
    byId("run-status").textContent = "Server unavailable";
  }
}
boot();
