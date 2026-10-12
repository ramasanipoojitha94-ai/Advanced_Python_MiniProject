document.addEventListener("DOMContentLoaded", () => {
  const mapRoot = document.querySelector("#world-map");
  const list = document.querySelector("#world-place-list");
  const filter = document.querySelector("#world-filter");
  const status = document.querySelector("#location-status");
  const count = document.querySelector("#world-result-count");
  const selectedPoint = document.querySelector("#selected-point");
  const selectedLabel = document.querySelector("#selected-point-label");
  const planSelectedLink = document.querySelector("#plan-selected-point");
  const savedOnly = filter?.elements.namedItem("saved");
  if (!mapRoot || !list || !filter) return;

  const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[character]);
  const initialPlaces = window.yatraGoMapPlaces || [];
  let places = initialPlaces;
  let map;
  let markers;
  let selectedCoordinates = null;
  let localCurrency = false;

  const placeUrl = (place) => `/planner?place_id=${encodeURIComponent(place.id)}`;
  const directionsUrl = (place) => {
    const origin = selectedCoordinates || [place.lat, place.lon];
    const route = `${origin[0]},${origin[1]};${place.lat},${place.lon}`;
    return `https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route=${encodeURIComponent(route)}`;
  };
  const popupHtml = (place) => {
    const price = localCurrency && place.local_price !== null
      ? `${escapeHtml(place.local_currency)} ${escapeHtml(place.local_price)} · illustrative local sample`
      : (place.price_inr === null ? "Price not supplied" : `₹${Number(place.price_inr).toLocaleString("en-IN")} · sample`);
    const distance = place.distance_km === null
      ? "" : `<small>About ${escapeHtml(place.distance_km)} km straight-line from the selected location.</small>`;
    const save = window.yatraGoSignedIn
      ? `<form method="post" action="/world-map/places/${place.id}/save"><input type="hidden" name="csrf_token" value="${escapeHtml(window.yatraGoCsrfToken)}"><button type="submit">${place.saved ? "♥ Remove saved place" : "♡ Save place"}</button></form>`
      : "";
    const rating = place.rating
      ? `★ ${escapeHtml(place.rating)} · ${escapeHtml(place.rating_kind)}${place.rating_count ? ` (${escapeHtml(place.rating_count)} review(s))` : ""}`
      : "No verified rating";
    return `<article class="map-popup"><img src="${escapeHtml(place.image)}" alt=""><span>${escapeHtml(place.type)} · sample</span><strong>${escapeHtml(place.name)}</strong><small>${escapeHtml(place.address)}, ${escapeHtml(place.city)}, ${escapeHtml(place.country)}</small><span>${price}</span><small>${rating} · hours ${escapeHtml(place.opening_hours)}</small>${distance}<div><a href="${placeUrl(place)}">Add to trip</a><a href="${directionsUrl(place)}" target="_blank" rel="noopener noreferrer">Directions ↗</a></div>${save}</article>`;
  };
  const renderCards = () => {
    list.replaceChildren();
    count.textContent = String(places.length);
    if (!places.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.innerHTML = "<h2>No sample places match</h2><p>Try another city, country or filter. Global place search is limited to the curated demo catalog.</p>";
      list.append(empty);
      return;
    }
    places.forEach((place) => {
      const article = document.createElement("article");
      article.className = "world-place-card";
      const image = document.createElement("img");
      image.src = place.image;
      image.alt = `${place.name} sample ${place.type} in ${place.city}, ${place.country}`;
      image.loading = "lazy";
      const details = document.createElement("div");
      details.className = "world-place-details";
      const label = document.createElement("span");
      label.className = "eyebrow";
      label.textContent = `${place.type} · ${place.category} · SAMPLE`;
      const title = document.createElement("h2");
      title.textContent = place.name;
      const description = document.createElement("p");
      description.textContent = place.description;
      const address = document.createElement("small");
      address.textContent = `${place.address} · ${place.city}, ${place.country}`;
      const facts = document.createElement("div");
      facts.className = "world-place-facts";
      const rating = document.createElement("span");
      rating.textContent = place.rating
        ? `★ ${place.rating} · ${place.rating_kind}${place.rating_count ? ` · ${place.rating_count} review(s)` : ""}`
        : "No verified rating";
      facts.append(rating);
      if (place.price_inr !== null) {
        const price = document.createElement("strong");
        price.dataset.currency = "inr";
        price.textContent = `₹${Number(place.price_inr).toLocaleString("en-IN")} · sample`;
        price.hidden = localCurrency && place.local_price !== null;
        facts.append(price);
      }
      if (place.local_price !== null && place.local_currency !== "INR") {
        const price = document.createElement("strong");
        price.dataset.currency = "local";
        price.textContent = `${place.local_currency} ${place.local_price} · illustrative local amount`;
        price.hidden = !localCurrency;
        facts.append(price);
      }
      if (place.distance_km !== null) {
        const distance = document.createElement("span");
        distance.textContent = `~${place.distance_km} km straight-line · approximate`;
        facts.append(distance);
      }
      const meta = document.createElement("p");
      meta.className = "world-place-meta";
      meta.textContent = [place.amenities, place.cuisine, place.dietary, `Hours: ${place.opening_hours}`].filter(Boolean).join(" · ");
      const actions = document.createElement("div");
      actions.className = "world-place-actions";
      const mapLink = document.createElement("a");
      mapLink.className = "text-link";
      mapLink.href = `https://www.openstreetmap.org/?mlat=${encodeURIComponent(place.lat)}&mlon=${encodeURIComponent(place.lon)}#map=15/${place.lat}/${place.lon}`;
      mapLink.target = "_blank";
      mapLink.rel = "noopener noreferrer";
      mapLink.textContent = "View on OpenStreetMap ↗";
      const planLink = document.createElement("a");
      planLink.className = "text-link";
      planLink.href = placeUrl(place);
      planLink.textContent = "Add to trip plan →";
      actions.append(mapLink, planLink);
      if (window.yatraGoSignedIn) {
        const form = document.createElement("form");
        form.method = "post";
        form.action = `/world-map/places/${place.id}/save`;
        const token = document.createElement("input");
        token.type = "hidden";
        token.name = "csrf_token";
        token.value = window.yatraGoCsrfToken;
        const saveButton = document.createElement("button");
        saveButton.className = `save-place${place.saved ? " is-saved" : ""}`;
        saveButton.setAttribute("aria-label", place.saved ? "Remove saved place" : "Save place");
        saveButton.textContent = place.saved ? "♥" : "♡";
        form.append(token, saveButton);
        actions.append(form);
      }
      details.append(label, title, description, address, facts, meta, actions);
      if (window.yatraGoSignedIn) {
        const reviewDetails = document.createElement("details");
        reviewDetails.className = "place-review-form";
        const summary = document.createElement("summary");
        summary.textContent = "Write a traveller review";
        const reviewForm = document.createElement("form");
        reviewForm.method = "post";
        reviewForm.action = `/world-map/places/${place.id}/reviews`;
        const token = document.createElement("input");
        token.type = "hidden";
        token.name = "csrf_token";
        token.value = window.yatraGoCsrfToken;
        const ratingLabel = document.createElement("label");
        ratingLabel.textContent = "Rating";
        const rating = document.createElement("select");
        rating.name = "rating";
        rating.required = true;
        const placeholder = document.createElement("option");
        placeholder.value = "";
        placeholder.textContent = "Select rating";
        rating.append(placeholder);
        for (let score = 1; score <= 5; score += 1) {
          const option = document.createElement("option");
          option.value = String(score);
          option.textContent = `${score} / 5`;
          rating.append(option);
        }
        ratingLabel.append(rating);
        const reviewLabel = document.createElement("label");
        reviewLabel.textContent = "Review";
        const textarea = document.createElement("textarea");
        textarea.name = "body";
        textarea.maxLength = 1000;
        textarea.required = true;
        textarea.rows = 2;
        textarea.placeholder = "Share your experience";
        reviewLabel.append(textarea);
        const submit = document.createElement("button");
        submit.className = "button button-small";
        submit.textContent = "Save unverified review";
        reviewForm.append(token, ratingLabel, reviewLabel, submit);
        reviewDetails.append(summary, reviewForm);
        details.append(reviewDetails);
      }
      article.append(image, details);
      list.append(article);
    });
  };
  const rebuildMarkers = () => {
    if (!map || !markers) return;
    markers.clearLayers();
    places.forEach((place) => {
      const markerColors = {
        hotel: "#c8343b",
        restaurant: "#d28a35",
        attraction: "#397b61",
        transport: "#477c9e",
        destination: "#745b9b",
      };
      const marker = window.L.circleMarker([place.lat, place.lon], {
        radius: 8,
        color: "#fff",
        weight: 2,
        fillColor: markerColors[place.type] || "#c8343b",
        fillOpacity: 0.95,
      }).addTo(markers);
      marker.bindPopup(() => popupHtml(place), { maxWidth: 280 });
    });
    if (places.length && filter.elements.namedItem("q").value.trim()) {
      map.fitBounds(markers.getBounds().pad(0.14), { maxZoom: 12 });
    }
  };
  const loadPlaces = async () => {
    const values = new FormData(filter);
    const radius = values.get("radius");
    if (radius && !selectedCoordinates) {
      status.textContent = "Choose a location on the map or use the location button before filtering by radius.";
      values.delete("radius");
    }
    if (selectedCoordinates) {
      values.set("lat", selectedCoordinates[0]);
      values.set("lon", selectedCoordinates[1]);
    }
    const parameters = new URLSearchParams();
    values.forEach((value, key) => {
      if (value !== "" && key !== "csrf_token") parameters.set(key, value);
    });
    if (savedOnly && !savedOnly.checked) parameters.delete("saved");
    if (savedOnly && savedOnly.checked) parameters.set("saved", "1");
    status.textContent = "Searching curated sample places…";
    try {
      const response = await fetch(`/api/world-places?${parameters.toString()}`, {
        headers: { Accept: "application/json" },
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "Could not load map places.");
      places = payload.places;
      renderCards();
      rebuildMarkers();
      status.textContent = `${places.length} curated sample places · no live provider connected.`;
    } catch (error) {
      status.textContent = error.message || "Map search failed. The sample list remains available.";
    }
  };
  const markSelectedPoint = (latitude, longitude, label) => {
    selectedCoordinates = [latitude, longitude];
    selectedPoint.hidden = false;
    selectedLabel.textContent = `${label} · ${latitude.toFixed(4)}, ${longitude.toFixed(4)}`;
    const parameters = new URLSearchParams({
      lat: latitude,
      lon: longitude,
      location_name: label,
    });
    planSelectedLink.href = `/planner?${parameters.toString()}`;
    loadPlaces();
  };

  renderCards();
  if (window.L) {
    map = window.L.map(mapRoot, { scrollWheelZoom: false }).setView([22, 18], 2);
    window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap contributors</a>',
    }).addTo(map);
    markers = window.L.layerGroup().addTo(map);
    rebuildMarkers();
    map.on("click", (event) => {
      markSelectedPoint(event.latlng.lat, event.latlng.lng, "Selected map point");
    });
    window.setTimeout(() => map.invalidateSize(), 200);
  } else {
    mapRoot.innerHTML = '<div class="map-unavailable">Interactive map tiles need an internet connection. Search and sample list browsing still work.</div>';
  }

  filter.addEventListener("submit", (event) => {
    event.preventDefault();
    loadPlaces();
  });
  savedOnly?.addEventListener("change", loadPlaces);
  document.querySelectorAll("[data-recent-search]").forEach((button) => {
    button.addEventListener("click", () => {
      filter.elements.namedItem("q").value = button.dataset.recentSearch;
      loadPlaces();
    });
  });
  document.querySelectorAll("[data-map-view]").forEach((button) => button.addEventListener("click", () => {
    const listView = button.dataset.mapView === "list";
    document.querySelectorAll("[data-map-view]").forEach((item) => item.classList.toggle("active", item === button));
    document.querySelector(".world-layout").classList.toggle("world-list-only", listView);
    if (!listView && map) window.setTimeout(() => map.invalidateSize(), 100);
  }));
  document.querySelector("#locate-me")?.addEventListener("click", () => {
    if (!navigator.geolocation) {
      status.textContent = "This browser does not provide location services. Search for a city or choose a map point.";
      return;
    }
    status.textContent = "Waiting for your one-time location permission…";
    navigator.geolocation.getCurrentPosition((position) => {
      const latitude = position.coords.latitude;
      const longitude = position.coords.longitude;
      markSelectedPoint(latitude, longitude, "Your current location");
      if (map) map.setView([latitude, longitude], 11);
      status.textContent = "Using your current location for this session only; it is not saved.";
    }, () => {
      status.textContent = "Location unavailable or permission denied. You can search for a city or select a point on the map.";
    }, { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 });
  });
  document.querySelector("#currency-toggle")?.addEventListener("click", (event) => {
    localCurrency = !localCurrency;
    event.currentTarget.setAttribute("aria-pressed", String(localCurrency));
    event.currentTarget.textContent = localCurrency
      ? "Show INR sample prices" : "Show local sample prices";
    renderCards();
    rebuildMarkers();
  });
});
