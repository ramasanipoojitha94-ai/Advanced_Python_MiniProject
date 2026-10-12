document.addEventListener("DOMContentLoaded", () => {
  document.addEventListener("error", (event) => {
    const image = event.target;
    if (image instanceof HTMLImageElement
      && !image.classList.contains("leaflet-tile")
      && !image.dataset.fallbackApplied) {
      image.dataset.fallbackApplied = "true";
      image.src = image.dataset.fallback || "/static/images/travel-fallback.svg";
    }
  }, true);

  const toggle = document.querySelector(".nav-toggle");
  const navigation = document.querySelector(".main-nav");
  if (toggle && navigation) {
    const setNavigationOpen = (open) => {
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");
      navigation.classList.toggle("nav-open", open);
    };
    toggle.addEventListener("click", () => {
      const expanded = toggle.getAttribute("aria-expanded") === "true";
      setNavigationOpen(!expanded);
    });
    navigation.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => setNavigationOpen(false));
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") setNavigationOpen(false);
    });
    document.addEventListener("click", (event) => {
      if (!navigation.contains(event.target) && !toggle.contains(event.target)) {
        setNavigationOpen(false);
      }
    });
  }

  const avatarTrigger = document.querySelector(".dashboard-avatar-trigger");
  const photoDialog = document.querySelector("#profile-photo-dialog");
  const photoDialogClose = photoDialog?.querySelector(".profile-photo-close");
  if (avatarTrigger && photoDialog instanceof HTMLDialogElement) {
    avatarTrigger.addEventListener("click", () => photoDialog.showModal());
    photoDialogClose?.addEventListener("click", () => photoDialog.close());
    photoDialog.addEventListener("click", (event) => {
      if (event.target === photoDialog) photoDialog.close();
    });
  }

  const avatarUploadForm = document.querySelector("[data-avatar-upload]");
  const avatarFileInput = avatarUploadForm?.querySelector('input[type="file"]');
  const avatarUploadLabel = avatarUploadForm?.querySelector(".avatar-upload-label span");
  avatarFileInput?.addEventListener("change", () => {
    if (!avatarFileInput.files?.length) return;
    if (avatarUploadLabel) avatarUploadLabel.textContent = "Uploading…";
    avatarUploadForm.requestSubmit();
  });

  document.querySelectorAll(".swap-button").forEach((button) => {
    button.addEventListener("click", () => {
      const form = button.closest("form");
      const source = form?.elements.namedItem("source");
      const destination = form?.elements.namedItem("destination");
      if (!source || !destination) return;
      [source.value, destination.value] = [destination.value, source.value];
    });
  });

  const dashboardBookingForm = document.querySelector(".dashboard-booking-form");
  if (dashboardBookingForm) {
    const modeInput = dashboardBookingForm.querySelector("#dashboard-transport-mode");
    const modeButtons = [...dashboardBookingForm.querySelectorAll("[data-dashboard-mode]")];
    modeButtons.forEach((button) => button.addEventListener("click", () => {
      modeInput.value = button.dataset.dashboardMode;
      modeButtons.forEach((item) => {
        const active = item === button;
        item.classList.toggle("active", active);
        item.setAttribute("aria-pressed", String(active));
      });
    }));
  }

  document.querySelectorAll(".flight-swap").forEach((button) => {
    button.addEventListener("click", () => {
      const form = button.closest("form");
      const origin = form?.elements.namedItem("origin");
      const destination = form?.elements.namedItem("destination");
      if (origin && destination) [origin.value, destination.value] = [destination.value, origin.value];
    });
  });

  const transportForm = document.querySelector(".transport-search-form");
  if (transportForm) {
    const modeInput = transportForm.querySelector("#transport-mode");
    const modeTabs = [...transportForm.querySelectorAll("[data-transport-mode]")];
    const tripType = transportForm.querySelector("#transport-trip-type");
    const returnField = transportForm.querySelector(".transport-return-field");
    const tripField = transportForm.querySelector(".transport-trip-field");
    const destinationInput = transportForm.elements.namedItem("destination");
    const submit = transportForm.querySelector(".transport-submit");
    const departureDate = transportForm.elements.namedItem("date");
    const swapButton = transportForm.querySelector(".location-swap");
    const updateTransportFields = () => {
      const mode = modeInput.value;
      const selectedTrip = tripType?.value || "oneway";
      const isRental = mode === "car" || mode === "bike";
      const needsReturn = isRental || (["cab", "flight"].includes(mode) && selectedTrip === "roundtrip");
      if (returnField) {
        returnField.hidden = !needsReturn;
        const returnInput = returnField.querySelector("input");
        returnInput.required = needsReturn;
        returnInput.disabled = !needsReturn;
        returnInput.min = departureDate.value;
      }
      if (tripField) tripField.hidden = mode === "bus" || mode === "metro" || mode === "ferry" || mode === "auto" || mode === "shared";
      destinationInput.required = !isRental;
      const serviceField = transportForm.querySelector(".service-type-field");
      if (serviceField) serviceField.hidden = mode === "bus" || mode === "flight";
      const busField = transportForm.querySelector(".bus-type-field");
      if (busField) busField.hidden = mode !== "bus";
      const cabinField = transportForm.querySelector(".flight-class-field");
      if (cabinField) cabinField.hidden = mode !== "flight";
      const passengerSelect = transportForm.elements.namedItem("passengers");
      if (passengerSelect instanceof HTMLSelectElement) {
        [...passengerSelect.options].forEach((option) => {
          option.disabled = ["bus", "flight"].includes(mode) && Number(option.value) > 6;
        });
        if (["bus", "flight"].includes(mode) && Number(passengerSelect.value) > 6) passengerSelect.value = "6";
      }
      submit.innerHTML = `Find ${modeTabs.find((tab) => tab.dataset.transportMode === mode)?.querySelector("strong")?.textContent.toLowerCase() || "transport"} <span>→</span>`;
      if (tripType && isRental) {
        tripType.value = "rental";
      } else if (tripType && (selectedTrip === "rental" || (selectedTrip === "roundtrip" && !["cab", "flight"].includes(mode)))) {
        tripType.value = "oneway";
      }
      if (tripType && mode === "flight") {
        tripField.hidden = false;
        tripType.querySelector('option[value="roundtrip"]').hidden = false;
        tripType.querySelector('option[value="rental"]').hidden = true;
      } else if (tripType && mode === "cab") {
        tripType.querySelector('option[value="roundtrip"]').hidden = false;
        tripType.querySelector('option[value="rental"]').hidden = true;
      } else if (tripType && isRental) {
        tripField.hidden = false;
        tripType.querySelector('option[value="roundtrip"]').hidden = true;
        tripType.querySelector('option[value="rental"]').hidden = false;
      } else if (tripType) {
        tripType.querySelector('option[value="roundtrip"]').hidden = true;
        tripType.querySelector('option[value="rental"]').hidden = true;
      }
      modeTabs.forEach((tab) => {
        const active = tab.dataset.transportMode === mode;
        tab.classList.toggle("active", active);
        tab.setAttribute("aria-selected", String(active));
      });
    };
    modeTabs.forEach((tab) => tab.addEventListener("click", () => {
      modeInput.value = tab.dataset.transportMode;
      if (tripType && (modeInput.value === "car" || modeInput.value === "bike")) tripType.value = "rental";
      else if (tripType?.value === "rental") tripType.value = "oneway";
      updateTransportFields();
    }));
    tripType?.addEventListener("change", updateTransportFields);
    departureDate.addEventListener("change", updateTransportFields);
    swapButton?.addEventListener("click", () => {
      const origin = transportForm.elements.namedItem("origin");
      [origin.value, destinationInput.value] = [destinationInput.value, origin.value];
    });
    updateTransportFields();
  }

  const destinationGrid = document.querySelector("#india-destination-grid");
  if (destinationGrid) {
    const cards = [...destinationGrid.querySelectorAll("[data-destination-card]")];
    const categoryButtons = [...document.querySelectorAll("[data-destination-category]")];
    const searchInput = document.querySelector("#india-destination-search");
    const emptyState = document.querySelector("#india-discovery-empty");
    let selectedCategory = "all";
    const updateDestinations = () => {
      const term = searchInput.value.trim().toLocaleLowerCase();
      let visible = 0;
      cards.forEach((card) => {
        const categories = card.dataset.collections.split("|");
        const categoryMatches = selectedCategory === "all" || categories.includes(selectedCategory);
        const searchMatches = !term || card.dataset.search.includes(term);
        card.hidden = !(categoryMatches && searchMatches);
        if (!card.hidden) visible += 1;
      });
      emptyState.hidden = visible > 0;
    };
    categoryButtons.forEach((button) => button.addEventListener("click", () => {
      selectedCategory = button.dataset.destinationCategory.toLocaleLowerCase();
      categoryButtons.forEach((item) => {
        const active = item === button;
        item.classList.toggle("active", active);
        item.setAttribute("aria-pressed", String(active));
      });
      updateDestinations();
    }));
    searchInput.addEventListener("input", updateDestinations);
    updateDestinations();
  }

  const budgetCalculator = document.querySelector("#budget-calculator");
  if (budgetCalculator) {
    const inputs = [...budgetCalculator.querySelectorAll("[data-budget-input]")];
    const total = document.querySelector("#budget-total-value");
    const formatINR = new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    });
    const updateBudget = () => {
      const amount = inputs.reduce((sum, input) => sum + Math.max(0, Number(input.value) || 0), 0);
      total.textContent = formatINR.format(amount);
    };
    inputs.forEach((input) => input.addEventListener("input", updateBudget));
    updateBudget();
  }

  const trainBookingForm = document.querySelector(".transport-book-form[data-mode='train']");
  if (trainBookingForm) {
    const seats = [...trainBookingForm.querySelectorAll('input[name="seat_ids"]')];
    const expected = Number(trainBookingForm.dataset.passengers);
    const message = trainBookingForm.querySelector("#train-seat-count");
    const submit = trainBookingForm.querySelector(".transport-confirm-button");
    const updateTrainSeats = () => {
      const selected = seats.filter((seat) => seat.checked);
      trainBookingForm.querySelectorAll(".train-seat-assignment").forEach((label, index) => {
        label.textContent = selected[index] ? `Seat ${selected[index].dataset.seat}` : "";
      });
      message.textContent = selected.length === expected
        ? `${selected.length} sample seat${selected.length === 1 ? "" : "s"} selected.`
        : `Select exactly ${expected} sample seat${expected === 1 ? "" : "s"}. ${selected.length} selected.`;
      submit.disabled = selected.length !== expected;
      submit.classList.toggle("button-disabled", selected.length !== expected);
    };
    seats.forEach((seat) => seat.addEventListener("change", updateTrainSeats));
    trainBookingForm.addEventListener("submit", (event) => {
      if (seats.filter((seat) => seat.checked).length !== expected) {
        event.preventDefault();
        updateTrainSeats();
      }
    });
    updateTrainSeats();
  }

  const flightTypeRadios = document.querySelectorAll('input[name="trip_type"]');
  const returnDateField = document.querySelector(".return-date-field input");
  const updateReturnDate = () => {
    if (!returnDateField) return;
    const isRoundTrip = document.querySelector('input[name="trip_type"]:checked')?.value === "roundtrip";
    returnDateField.required = isRoundTrip;
    returnDateField.disabled = !isRoundTrip;
    returnDateField.closest("label")?.classList.toggle("return-date-hidden", !isRoundTrip);
  };
  flightTypeRadios.forEach((radio) => radio.addEventListener("change", updateReturnDate));
  updateReturnDate();

  const stayGuestCount = document.querySelector("#stay-guest-count");
  if (stayGuestCount) {
    const guestFields = [...document.querySelectorAll(".stay-guest-field")];
    const updateGuests = () => {
      const count = Number(stayGuestCount.value);
      guestFields.forEach((field, index) => {
        const active = index < count;
        field.hidden = !active;
        const input = field.querySelector("input");
        input.disabled = !active;
        input.required = active;
      });
    };
    stayGuestCount.addEventListener("change", updateGuests);
    updateGuests();
  }

  document.querySelectorAll('input[name="check_in"]').forEach((checkIn) => {
    const checkOut = checkIn.form?.elements.namedItem("check_out");
    checkIn.addEventListener("change", () => {
      if (checkOut) {
        checkOut.min = checkIn.value;
        if (checkOut.value && checkOut.value <= checkIn.value) checkOut.value = "";
      }
    });
  });

  const bookingForm = document.querySelector("#booking-form");
  if (bookingForm) {
    const checks = [...bookingForm.querySelectorAll('input[name="seat_ids"]')];
    const passengerCards = [...bookingForm.querySelectorAll(".passenger-card")];
    const requiredPassengerCount = Number(bookingForm.elements.namedItem("passenger_count")?.value || 1);
    const fare = Number(bookingForm.dataset.fare);
    const total = document.querySelector("#total-fare");
    const countLabel = document.querySelector("#selection-count");
    const updateSelection = () => {
      const selected = checks.filter((check) => check.checked);
      selected.forEach((check) => check.closest(".seat")?.classList.add("seat-selected"));
      checks.filter((check) => !check.checked).forEach((check) => check.closest(".seat")?.classList.remove("seat-selected"));
      passengerCards.forEach((card, index) => {
        const active = index < selected.length;
        card.hidden = !active;
        card.querySelector(".seat-assignment").textContent = active ? `· Seat ${selected[index].dataset.seat}` : "";
        card.querySelectorAll("input, select").forEach((field) => {
          field.disabled = !active;
          field.required = active;
        });
      });
      total.textContent = `₹${fare * selected.length}`;
      countLabel.textContent = selected.length
        ? `${selected.length} of ${requiredPassengerCount} seats selected`
        : `Select ${requiredPassengerCount} seat${requiredPassengerCount === 1 ? "" : "s"} for your travellers`;
    };
    checks.forEach((check) => check.addEventListener("change", updateSelection));
    bookingForm.addEventListener("submit", (event) => {
      if (checks.filter((check) => check.checked).length !== requiredPassengerCount) {
        event.preventDefault();
        countLabel.textContent = `Choose exactly ${requiredPassengerCount} available seat${requiredPassengerCount === 1 ? "" : "s"}.`;
      }
    });
    updateSelection();
  }

  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!window.confirm(form.dataset.confirm)) event.preventDefault();
    });
  });
});
