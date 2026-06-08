// Global app state & UI handlers & Currency settings
let currentCurrency = localStorage.getItem("app_currency") || "USD";
const LKR_CONVERSION_RATE = 300.00;
let activeBookingPath = "ticket";


// Helper to format price based on selected currency
function formatPrice(usdAmount) {
    usdAmount = parseFloat(usdAmount);
    if (isNaN(usdAmount)) return "$0.00";
    if (currentCurrency === "LKR") {
        const lkrAmount = usdAmount * LKR_CONVERSION_RATE;
        return `Rs ${lkrAmount.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    }
    return `$${usdAmount.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}

// Function to handle global currency changes
function changeGlobalCurrency(currencyCode) {
    currentCurrency = currencyCode;
    localStorage.setItem("app_currency", currencyCode);
    
    // Refresh agent UI components that render pricing
    if (document.getElementById("topbar-credit")) {
        // Set selector UI dropdown if not matching
        const curSelect = document.getElementById("currency-select");
        if (curSelect) {
            curSelect.value = currencyCode;
        }
        
        // Sync twin-pill visual styles
        const pillUSD = document.getElementById("currency-pill-usd");
        const pillLKR = document.getElementById("currency-pill-lkr");
        if (pillUSD && pillLKR) {
            if (currencyCode === "USD") {
                pillUSD.classList.add("active");
                pillUSD.style.background = "var(--primary-gradient)";
                pillUSD.style.color = "#fff";
                
                pillLKR.classList.remove("active");
                pillLKR.style.background = "none";
                pillLKR.style.color = "var(--text-muted)";
            } else {
                pillLKR.classList.add("active");
                pillLKR.style.background = "var(--primary-gradient)";
                pillLKR.style.color = "#fff";
                
                pillUSD.classList.remove("active");
                pillUSD.style.background = "none";
                pillUSD.style.color = "var(--text-muted)";
            }
        }
        
        updateAgentUI();
        loadAgentDashboardFares();
        loadBookings();
        if (typeof currentSelectedFlight !== 'undefined' && currentSelectedFlight) {
            renderStepperSummary();
        }

        
        // Re-render flight search results instantly if search is performed
        const searchResults = document.getElementById("flight-results-container");
        if (searchResults && searchResults.innerHTML && !searchResults.innerHTML.includes("Interrogating") && !searchResults.innerHTML.includes("triangle-exclamation")) {
            if (lastSearchedFlights && lastSearchedFlights.length > 0) {
                const filterBar = document.getElementById("flight-results-filter-bar");
                if (filterBar) filterBar.style.display = "flex";
                applyFlightFilters();
            }
        }
        
        // Re-render hotel search results instantly if search is performed
        const hotelResults = document.getElementById("hotel-results-container");
        if (hotelResults && hotelResults.innerHTML && !hotelResults.innerHTML.includes("Interrogating") && !hotelResults.innerHTML.includes("triangle-exclamation")) {
            if (lastSearchedHotels && lastSearchedHotels.length > 0) {
                renderHotelSearchResults(lastSearchedHotels);
            }
        }
        
        loadCancellations();
        loadAgentReports();
    }
}

// Toggles the currency between USD and LKR instantly
function toggleCurrencyInstant() {
    const nextCurrency = (currentCurrency === "USD") ? "LKR" : "USD";
    changeGlobalCurrency(nextCurrency);
    
    // Play a tiny subtle rotation micro-animation on the swap icon
    const icon = document.querySelector(".credit-details .fa-retweet");
    if (icon) {
        icon.style.transition = "transform 0.4s ease";
        const currentRotation = icon.style.transform || "rotate(0deg)";
        const currentDegrees = parseInt(currentRotation.replace(/[^0-9]/g, '')) || 0;
        const nextDegrees = currentDegrees + 180;
        icon.style.transform = `rotate(${nextDegrees}deg)`;
    }
    
    showNotification("Currency Swapped", `Display currency set to ${nextCurrency} successfully!`, "info");
}

document.addEventListener("DOMContentLoaded", function () {
    // Detect role and initialize appropriate components
    if (document.getElementById("topbar-credit")) {
        // Set dropdown value to cached currency
        const curSelect = document.getElementById("currency-select");
        if (curSelect) {
            curSelect.value = currentCurrency;
        }
        
        // Sync twin-pill visual styles
        const pillUSD = document.getElementById("currency-pill-usd");
        const pillLKR = document.getElementById("currency-pill-lkr");
        if (pillUSD && pillLKR) {
            if (currentCurrency === "USD") {
                pillUSD.classList.add("active");
                pillUSD.style.background = "var(--primary-gradient)";
                pillUSD.style.color = "#fff";
                
                pillLKR.classList.remove("active");
                pillLKR.style.background = "none";
                pillLKR.style.color = "var(--text-muted)";
            } else {
                pillLKR.classList.add("active");
                pillLKR.style.background = "var(--primary-gradient)";
                pillLKR.style.color = "#fff";
                
                pillUSD.classList.remove("active");
                pillUSD.style.background = "none";
                pillUSD.style.color = "var(--text-muted)";
            }
        }
        
        // Agent initialization
        updateAgentUI();
        loadAgentDashboardFares();
        loadBookings();
        loadSupportTickets();
        loadTimaticLogs();
        initAutocompleteSearch();
    } else if (document.getElementById("admin-total-turnover")) {
        // Admin initialization
        updateAdminUI();
        loadAdminAgents();
        loadAdminFees();
        loadAdminReports();
        loadAdminTickets();
    }
});

// Helper for displaying beautiful dynamic notification alerts
function showNotification(title, message, type = "success") {
    const toast = document.createElement("div");
    toast.className = `popup-toast ${type}`;
    
    let iconClass = "fa-circle-check";
    if (type === "danger") iconClass = "fa-triangle-exclamation";
    if (type === "warning") iconClass = "fa-circle-exclamation";
    if (type === "info") iconClass = "fa-circle-info";

    toast.innerHTML = `
        <div class="popup-toast-icon"><i class="fa-solid ${iconClass}"></i></div>
        <div class="popup-toast-content">
            <div class="popup-toast-title">${title}</div>
            <div class="popup-toast-desc">${message}</div>
        </div>
        <div class="popup-toast-close" onclick="this.parentElement.remove()"><i class="fa-solid fa-xmark"></i></div>
    `;
    document.body.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 5500);
}

// Modal control helpers
function openModal(id) {
    document.getElementById(id).classList.add("active");
}

function closeModal(id) {
    document.getElementById(id).classList.remove("active");
}

// =========================================================================
// B2B AGENT CLIENT SIDE LOGIC
// =========================================================================

// Switch between agent dashboard tabs
function switchTab(tabId) {
    // Deactivate current tabs
    document.querySelectorAll(".menu-item").forEach(item => item.classList.remove("active"));
    document.querySelectorAll(".tab-content-panel").forEach(panel => panel.classList.remove("active"));
    
    // Activate target
    event.currentTarget.classList.add("active");
    document.getElementById(`tab-${tabId}`).classList.add("active");
    
    // Close mobile menu if open
    const sidebar = document.querySelector('.app-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (sidebar && sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
    }
    
    // Load fresh data if needed
    if (tabId === "dashboard") {
        updateAgentUI();
        loadAgentDashboardFares();
    } else if (tabId === "bookings") {
        loadBookings();
    } else if (tabId === "reports") {
        loadAgentReports();
    } else if (tabId === "support") {
        loadSupportTickets();
    } else if (tabId === "timatic") {
        loadTimaticLogs();
    } else if (tabId === "cancellations") {
        loadCancellations();
    }
}

// Refresh Agent Credit & Stats
function updateAgentUI() {
    fetch("/api/agent/info")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                document.getElementById("topbar-credit").innerText = formatPrice(data.agent.credit_balance);
                document.getElementById("dashboard-reward-points").innerText = `${data.agent.reward_points} PTS`;
                
                // If on zero-credit agent page, show insufficient warning toast once
                if (data.agent.credit_balance <= 0 && data.agent.username === "zero_agent") {
                    showNotification("Insufficient Credit Warning", "Your agency credit balance is " + formatPrice(0) + ". Please top up before ticketing flights or booking hotels.", "warning");
                }
            }
        });
}

// Load daily lowest fares (ATL Flyers)
function loadAgentDashboardFares() {
    fetch("/api/flights/lowest-fares")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const tbody = document.getElementById("lowest-fares-table");
                tbody.innerHTML = "";
                
                if (data.fares.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted);">No promotional fares available for today.</td></tr>`;
                    return;
                }
                
                data.fares.forEach(f => {
                    tbody.innerHTML += `
                        <tr>
                            <td><strong>${f.origin} <i class="fa-solid fa-arrow-right" style="font-size:10px; margin:0 5px; color:var(--primary);"></i> ${f.destination}</strong></td>
                            <td>${f.airline} (${f.flight_number})</td>
                            <td><span class="badge-type">${f.flight_type}</span></td>
                            <td style="color:var(--primary); font-weight:700;">${formatPrice(f.lowest_fare)}</td>
                            <td>
                                <button class="btn-action" onclick="bookPromotionalFlight('${f.origin}', '${f.destination}', '${f.flight_type}')">
                                    <i class="fa-solid fa-plane-departure"></i> Book Now
                                </button>
                            </td>
                        </tr>
                    `;
                });
            }
        });
}

// Direct book from ATL Flyers
function bookPromotionalFlight(origin, dest, type) {
    switchTab('flights');
    document.getElementById("flight-origin").value = origin;
    document.getElementById("flight-dest").value = dest;
    document.getElementById("flight-channel").value = type;
    searchFlights();
}

// Submit Top-Up Wallet form
function openTopupModal() {
    openModal("topup-modal");
    document.getElementById("topup-amount").value = "";
}

function submitTopup() {
    const amount = document.getElementById("topup-amount").value;
    if (!amount || parseFloat(amount) <= 0) {
        showNotification("Invalid Entry", "Please enter a valid credit top-up value greater than 0.", "danger");
        return;
    }
    
    fetch("/api/agent/topup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ amount: parseFloat(amount) })
    })
    .then(res => res.json())
    .then(data => {
        closeModal("topup-modal");
        if (data.success) {
            showNotification("Instant Deposit Complete", data.message, "success");
            updateAgentUI();
        } else {
            showNotification("Transaction Denied", data.error, "danger");
        }
    });
}

// Autocomplete search integration
function initAutocompleteSearch() {
    const originInput = document.getElementById("flight-origin");
    const destInput = document.getElementById("flight-dest");
    
    if (!originInput || !destInput) return;
    
    setupAutocompleteForInput(originInput, "flight-origin-dropdown");
    setupAutocompleteForInput(destInput, "flight-dest-dropdown");
}

function setupAutocompleteForInput(input, dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    if (!dropdown) return;
    
    let debounceTimer = null;
    
    function fetchAndShowSuggestions(forcedQuery) {
        const query = typeof forcedQuery === "string" ? forcedQuery : input.value.trim();
        
        fetch(`/api/locations/search?q=${encodeURIComponent(query)}`)
            .then(res => res.json())
            .then(data => {
                if (data.success && data.groups.length > 0) {
                    dropdown.innerHTML = "";
                    
                    data.groups.forEach(group => {
                        // Create country header
                        const header = document.createElement("div");
                        header.className = "autocomplete-country-header";
                        header.innerHTML = `
                            <span>${group.country}</span>
                            <span class="autocomplete-country-flag">${group.flag}</span>
                        `;
                        dropdown.appendChild(header);
                        
                        // Create items for locations in this country
                        group.locations.forEach(loc => {
                            const item = document.createElement("div");
                            item.className = "autocomplete-item";
                            item.innerHTML = `
                                <div class="autocomplete-item-details">
                                    <div class="autocomplete-item-city">${loc.city}</div>
                                    <div class="autocomplete-item-airport">${loc.name}</div>
                                </div>
                                <div class="autocomplete-item-code">${loc.code}</div>
                            `;
                            
                            item.addEventListener("click", function(e) {
                                e.stopPropagation();
                                const formattedCountry = group.country.toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
                                input.value = `${loc.city}, ${formattedCountry} (${loc.code})`;
                                dropdown.style.display = "none";
                                
                                // Auto-focus next logical date field
                                if (input.id === "flight-dest") {
                                    const dateInput = document.getElementById("flight-date");
                                    if (dateInput && dateInput._flatpickr) {
                                        setTimeout(() => dateInput._flatpickr.open(), 50);
                                    }
                                } else if (input.id.startsWith("mc-dest-")) {
                                    const legId = input.id.split("-")[2];
                                    const dateInput = document.getElementById(`mc-date-${legId}`);
                                    if (dateInput && dateInput._flatpickr) {
                                        setTimeout(() => dateInput._flatpickr.open(), 50);
                                    }
                                }
                            });
                            
                            dropdown.appendChild(item);
                        });
                    });
                    
                    dropdown.style.display = "block";
                } else {
                    dropdown.style.display = "none";
                }
            })
            .catch(err => {
                console.error("Autocomplete search error:", err);
                dropdown.style.display = "none";
            });
    }
    
    // Focus listener
    input.addEventListener("focus", function() {
        input.select();
        const val = input.value.trim();
        if (!val || val.length === 3 || /\([A-Z]{3}\)$/i.test(val)) {
            fetchAndShowSuggestions("");
        } else {
            fetchAndShowSuggestions();
        }
    });
    
    // Input listener with debounce
    input.addEventListener("input", function() {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            fetchAndShowSuggestions();
        }, 150);
    });
    
    // Stop propagation on clicks inside the dropdown/input to prevent document listener from closing it
    dropdown.addEventListener("click", function(e) {
        e.stopPropagation();
    });
    
    input.addEventListener("click", function(e) {
        e.stopPropagation();
        input.select();
        const val = input.value.trim();
        if (!val || val.length === 3 || /\([A-Z]{3}\)$/i.test(val)) {
            fetchAndShowSuggestions("");
        } else {
            fetchAndShowSuggestions();
        }
    });
}

// Global click listener to close dropdowns when clicking outside
document.addEventListener("click", function() {
    const originDropdown = document.getElementById("flight-origin-dropdown");
    const destDropdown = document.getElementById("flight-dest-dropdown");
    if (originDropdown) originDropdown.style.display = "none";
    if (destDropdown) destDropdown.style.display = "none";
});

// Global variables for Flight Stepper Booking Wizard
let currentBookingStep = 1;
let currentSelectedFlight = null;
let lastSearchedFlights = [];
let lastSearchedHotels = [];
let selectedSeat = null;

// Flight Search Logic
function searchFlights() {
    const isMultiCity = document.getElementById("pill-multicity") && document.getElementById("pill-multicity").classList.contains("active");
    
    let adults = "1";
    const adultsInput = document.getElementById("flight-adults");
    const paxBtn = document.getElementById("passenger-btn");
    const paxSummary = document.getElementById("passenger-summary-text");
    
    if (adultsInput) {
        adults = adultsInput.value;
    } else if (paxSummary) {
        const match = paxSummary.innerText.match(/(\d+)/);
        if (match) adults = match[1];
    } else if (paxBtn) {
        const match = paxBtn.innerText.match(/(\d+)/);
        if (match) adults = match[1];
    }
    
    const children = document.getElementById("flight-children") ? document.getElementById("flight-children").value : "0";
    const infants = document.getElementById("flight-infants") ? document.getElementById("flight-infants").value : "0";
    const isModifying = window.isModifyingBooking ? "true" : "false";
    
    if (isMultiCity) {
        const o = document.getElementById(`mc-origin-1`) ? document.getElementById(`mc-origin-1`).value : '';
        const d = document.getElementById(`mc-dest-1`) ? document.getElementById(`mc-dest-1`).value : '';
        const dt = document.getElementById(`mc-date-1`) ? document.getElementById(`mc-date-1`).value : '';
        
        if (o && d && dt) {
            let mcUrl = `/flight-results?origin=${encodeURIComponent(o)}&dest=${encodeURIComponent(d)}&date=${encodeURIComponent(dt)}&adults=${adults}&children=${children}&infants=${infants}`;
            if (isModifying === "true" || window.location.search.includes('action=change')) {
                mcUrl += `&modifying=true`;
            }
            if (window.location.pathname.includes('/b2c')) {
                mcUrl = mcUrl.replace('/flight-results', '/b2c-flight-results');
            }
            window.open(mcUrl, '_blank');
        } else {
            alert("Please fill in the first leg of your multi-city journey.");
        }
        return;
    }

    const origin = document.getElementById("flight-origin").value;
    const dest = document.getElementById("flight-dest").value;
    const date = document.getElementById("flight-date") ? document.getElementById("flight-date").value : "";
    
    const isRoundTrip = document.getElementById("pill-roundtrip") && document.getElementById("pill-roundtrip").classList.contains("active");
    const returnDateInput = document.getElementById("flight-return-date");
    const returnDate = returnDateInput ? returnDateInput.value : "";
    const returnDateError = document.getElementById("return-date-error");
    
    if (returnDateError) returnDateError.style.display = "none";
    if (returnDateInput) returnDateInput.style.borderColor = "";
    
    if (isRoundTrip && !returnDate) {
        if (returnDateError) returnDateError.style.display = "block";
        if (returnDateInput) returnDateInput.style.borderColor = "var(--danger)";
        return;
    }
    
    if (!origin || !dest || !date) {
        alert("Please select Origin, Destination, and Departure Date.");
        return;
    }
    
    let url = `/flight-results?origin=${encodeURIComponent(origin)}&dest=${encodeURIComponent(dest)}&date=${encodeURIComponent(date)}&adults=${adults}&children=${children}&infants=${infants}`;
    if (isRoundTrip) {
        url += `&returnDate=${encodeURIComponent(returnDate)}`;
    }
    
    if (isModifying === "true" || window.location.search.includes('action=change')) {
        url += `&modifying=true`;
    }
    
    if (window.location.pathname.includes('/b2c')) {
        url = url.replace('/flight-results', '/b2c-flight-results');
    }
    
    window.open(url, '_blank');
}

function renderFlightSearchResults(flights) {
    const container = document.getElementById("flight-results-container");
    
    container.innerHTML = `
        <div style="text-align: center; color: var(--primary-color); padding: 40px 0;">
            <i class="fa-solid fa-plane-departure fa-bounce" style="font-size: 32px; margin-bottom: 15px;"></i>
            <p>Interrogating Global Distribution Systems...</p>
        </div>
    `;
    
    if (flights.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; color: var(--text-muted); padding: 40px 0;">
                <i class="fa-solid fa-triangle-exclamation" style="font-size: 32px; margin-bottom: 15px; color: var(--warning);"></i>
                <p>No flights matching the routing and filters found.</p>
            </div>
        `;
        return;
    }
    
    flights.forEach(f => {
        if (f.is_multicity) {
            let legsHTML = '';
            f.legs.forEach((leg, index) => {
                const depDate = new Date(leg.departure_time);
                const arrDate = new Date(leg.arrival_time);
                const hours = Math.abs(arrDate - depDate) / 36e5;
                const durationStr = `${Math.floor(hours)}h ${Math.round((hours % 1) * 60)}m`;
                
                if (index > 0) {
                    legsHTML += `<div style="border-top: 1px dashed rgba(255,255,255,0.1); margin: 15px 0; padding-top: 15px;"></div>`;
                }
                
                legsHTML += `
                    <div style="display: flex; gap: 20px; align-items: center;">
                        <div class="airline-info" style="min-width: 150px; flex-shrink: 0;">
                            <div class="airline-logo-placeholder"><i class="fa-solid fa-plane"></i></div>
                            <div>
                                <div class="airline-name">${leg.airline} (Flight ${index+1})</div>
                                <div class="flight-number">${leg.flight_number} • <span class="badge-type">Fare: ${leg.flight_type}</span></div>
                            </div>
                        </div>
                        <div class="flight-route-flow" style="flex-grow: 1;">
                            <div class="route-stop">
                                <div class="route-time">${depDate.toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'})}</div>
                                <div class="route-airport">${leg.origin}</div>
                            </div>
                            <div class="route-path-line">
                                <span class="route-duration">${durationStr} (${leg.segment_count} Segment)</span>
                            </div>
                            <div class="route-stop">
                                <div class="route-time">${arrDate.toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'})}</div>
                                <div class="route-airport">${leg.destination}</div>
                            </div>
                        </div>
                    </div>
                `;
            });
            
            const adults = document.getElementById("flight-adults") ? parseInt(document.getElementById("flight-adults").value) : 1;
            const children = document.getElementById("flight-children") ? parseInt(document.getElementById("flight-children").value) : 0;
            const infants = document.getElementById("flight-infants") ? parseInt(document.getElementById("flight-infants").value) : 0;
            const passengers = adults + children + infants;
            const markupTotal = 15.00 * f.legs.length * passengers;
            const totalPrice = (f.price * passengers) + markupTotal;
            
            container.innerHTML += `
                <div class="flight-ticket-card">
                    <div style="flex-grow: 1;">
                        ${legsHTML}
                    </div>
                    <div class="flight-fare-booking" style="margin-left: 20px; border-left: 1px solid rgba(255,255,255,0.08); padding-left: 20px;">
                        <div class="flight-fare-value">${formatPrice(totalPrice)}</div>
                        <div style="font-size: 10px; color: var(--text-muted); margin-bottom: 8px;">Includes ${formatPrice(markupTotal)} markup (${passengers} pax)</div>
                        <button class="btn-book-action" onclick="openFlightBookModal('${f.id}', 'Multi-City', '${f.airline}', ${totalPrice.toFixed(2)})">
                            <i class="fa-solid fa-circle-check"></i> Book Seat
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        const depDate = new Date(f.departure_time);
        const arrDate = new Date(f.arrival_time);
        const hours = Math.abs(arrDate - depDate) / 36e5;
        const durationStr = `${Math.floor(hours)}h ${Math.round((hours % 1) * 60)}m`;
        
        const adults = document.getElementById("flight-adults") ? parseInt(document.getElementById("flight-adults").value) : 1;
        const children = document.getElementById("flight-children") ? parseInt(document.getElementById("flight-children").value) : 0;
        const infants = document.getElementById("flight-infants") ? parseInt(document.getElementById("flight-infants").value) : 0;
        const passengers = adults + children + infants;
        const markupTotal = (f.return_flight ? 30.00 : 15.00) * passengers;
        const totalPrice = (f.price * passengers) + markupTotal;
        
        let returnHTML = '';
        if (f.return_flight) {
            const ret = f.return_flight;
            const retDepDate = new Date(ret.departure_time);
            const retArrDate = new Date(ret.arrival_time);
            const retHours = Math.abs(retArrDate - retDepDate) / 36e5;
            const retDurationStr = `${Math.floor(retHours)}h ${Math.round((retHours % 1) * 60)}m`;
            
            returnHTML = `
                <div style="border-top: 1px dashed rgba(255,255,255,0.1); margin: 15px 0; padding-top: 15px;"></div>
                <div style="display: flex; gap: 20px; align-items: center;">
                    <div class="airline-info" style="min-width: 150px; flex-shrink: 0;">
                        <div class="airline-logo-placeholder" style="background: rgba(0, 242, 254, 0.1);"><i class="fa-solid fa-plane" style="transform: rotate(180deg);"></i></div>
                        <div>
                            <div class="airline-name">${ret.airline} (Return)</div>
                            <div class="flight-number">${ret.flight_number} • <span class="badge-type">Fare: ${ret.flight_type}</span></div>
                        </div>
                    </div>
                    <div class="flight-route-flow" style="flex-grow: 1;">
                        <div class="route-stop">
                            <div class="route-time">${retDepDate.toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'})}</div>
                            <div class="route-airport">${ret.origin}</div>
                        </div>
                        <div class="route-path-line">
                            <span class="route-duration">${retDurationStr} (${ret.segment_count} Segment)</span>
                        </div>
                        <div class="route-stop">
                            <div class="route-time">${retArrDate.toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'})}</div>
                            <div class="route-airport">${ret.destination}</div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        container.innerHTML += `
            <div class="flight-ticket-card">
                <div style="flex-grow: 1;">
                    <div style="display: flex; gap: 20px; align-items: center;">
                        <div class="airline-info" style="min-width: 150px; flex-shrink: 0;">
                            <div class="airline-logo-placeholder"><i class="fa-solid fa-plane"></i></div>
                            <div>
                                <div class="airline-name">${f.airline} ${f.return_flight ? '(Outbound)' : ''}</div>
                                <div class="flight-number">${f.flight_number} • <span class="badge-type" style="background: rgba(0, 242, 254, 0.2); padding: 2px 6px; border-radius: 4px; font-weight: 600;">Fare: ${f.flight_type}</span></div>
                            </div>
                        </div>
                        <div class="flight-route-flow" style="flex-grow: 1;">
                            <div class="route-stop">
                                <div class="route-time">${depDate.toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'})}</div>
                                <div class="route-airport">${f.origin}</div>
                            </div>
                            <div class="route-path-line">
                                <span class="route-duration">${durationStr} (${f.segment_count} Segment)</span>
                            </div>
                            <div class="route-stop">
                                <div class="route-time">${arrDate.toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'})}</div>
                                <div class="route-airport">${f.destination}</div>
                            </div>
                        </div>
                    </div>
                    ${returnHTML}
                </div>
                
                <div class="flight-fare-booking" style="margin-left: 20px; border-left: 1px solid rgba(255,255,255,0.08); padding-left: 20px;">
                    <div class="flight-fare-value">${formatPrice(totalPrice)}</div>
                    <div style="font-size: 10px; color: var(--text-muted); margin-bottom: 8px;">Includes ${formatPrice(markupTotal)} markup (${passengers} pax)</div>
                    <button class="btn-book-action" onclick="openFlightBookModal(${f.id}, '${f.flight_number}', '${f.airline}', ${totalPrice.toFixed(2)})">
                        <i class="fa-solid fa-circle-check"></i> Book Seat
                    </button>
                </div>
            </div>
        `;
    });
}

function applyFlightFilters() {
    if (!lastSearchedFlights) return;

    const typeFilter = document.getElementById("filter-flight-type").value;
    const timeMode = document.getElementById("flight-time-mode") ? document.getElementById("flight-time-mode").value : "ALL";
    const timeBeforeStr = document.getElementById("flight-time-before") ? document.getElementById("flight-time-before").value : "";

    let filteredFlights = lastSearchedFlights.filter(f => {
        // Filter by Type
        if (typeFilter === "DIRECT" && f.segment_count > 1) return false;
        if (typeFilter === "TRANSIT" && f.segment_count === 1) return false;

        // Filter by Time
        if (timeMode === "BEFORE" && timeBeforeStr) {
            // timeBeforeStr is format HH:mm
            const parts = timeBeforeStr.split(":");
            if (parts.length === 2) {
                const maxHour = parseInt(parts[0], 10);
                const maxMin = parseInt(parts[1], 10);
                const depDate = new Date(f.departure_time);
                
                if (depDate.getHours() > maxHour) return false;
                if (depDate.getHours() === maxHour && depDate.getMinutes() > maxMin) return false;
            }
        }

        return true;
    });

    // Sort by price
    filteredFlights.sort((a, b) => {
        const pA = a.price + (a.return_flight ? 30 : 15);
        const pB = b.price + (b.return_flight ? 30 : 15);
        return pA - pB;
    });

    document.getElementById("filtered-results-count").innerText = filteredFlights.length;
    renderFlightSearchResults(filteredFlights);
}

// Trip Type Selector Controller (One-way vs Round-trip)
function setTripType(type) {
    const pillRoundtrip = document.getElementById("pill-roundtrip");
    const pillOneway = document.getElementById("pill-oneway");
    const pillMulticity = document.getElementById("pill-multicity");
    const returnDateContainer = document.getElementById("return-date-container");
    const returnDateInput = document.getElementById("flight-return-date");
    const standardFlightSearch = document.getElementById("standard-flight-search");
    const multiCityContainer = document.getElementById("multi-city-container");
    
    if (!pillRoundtrip || !pillOneway || !pillMulticity) return;
    
    // Reset all pills
    const allPills = [pillRoundtrip, pillOneway, pillMulticity];
    allPills.forEach(p => {
        p.classList.remove("active");
        p.style.background = "none";
        p.style.color = "var(--text-muted)";
    });

    if (type === "multicity") {
        pillMulticity.classList.add("active");
        pillMulticity.style.background = "var(--primary-gradient)";
        pillMulticity.style.color = "#fff";
        
        if (standardFlightSearch) standardFlightSearch.style.display = "none";
        if (multiCityContainer) multiCityContainer.style.display = "block";

        // Initialize multi-city legs if empty
        const legsWrapper = document.getElementById("multi-city-legs-wrapper");
        if (legsWrapper && legsWrapper.children.length === 0) {
            addMultiCityLeg(); // Flight 1
            addMultiCityLeg(); // Flight 2
        }
    } else {
        if (standardFlightSearch) standardFlightSearch.style.display = "contents";
        if (multiCityContainer) multiCityContainer.style.display = "none";

        if (type === "oneway") {
            pillOneway.classList.add("active");
            pillOneway.style.background = "var(--primary-gradient)";
            pillOneway.style.color = "#fff";
            
            if (returnDateContainer) returnDateContainer.style.display = "none";
            if (returnDateInput) {
                returnDateInput.value = "";
                returnDateInput.style.borderColor = "";
            }
            const returnDateError = document.getElementById("return-date-error");
            if (returnDateError) returnDateError.style.display = "none";
        } else {
            pillRoundtrip.classList.add("active");
            pillRoundtrip.style.background = "var(--primary-gradient)";
            pillRoundtrip.style.color = "#fff";
            
            if (returnDateContainer) returnDateContainer.style.display = "flex";
        }
    }
}

let multiCityLegCount = 0;
function addMultiCityLeg() {
    multiCityLegCount++;
    const legId = multiCityLegCount;
    const wrapper = document.getElementById("multi-city-legs-wrapper");
    
    const div = document.createElement("div");
    div.className = "multi-city-leg";
    div.id = `multi-city-leg-${legId}`;
    div.style.marginBottom = "15px";
    
    div.innerHTML = `
        <div style="font-weight: 600; font-size: 14px; margin-bottom: 8px; color: var(--text-color);">Flight ${legId}</div>
        <div style="display: flex; gap: 15px; align-items: center; flex-wrap: wrap;">
            <div class="search-input-group" style="flex: 1; margin: 0; position: relative;">
                <label>Leaving from</label>
                <input type="text" id="mc-origin-${legId}" class="form-control" placeholder="Add city, airport" autocomplete="off">
                <div class="autocomplete-dropdown" id="mc-origin-dropdown-${legId}"></div>
            </div>
            <div style="cursor: pointer; color: var(--text-muted); font-size: 18px; display: flex; align-items: center; justify-content: center; width: 30px; height: 30px; border-radius: 50%; background: rgba(255,255,255,0.05); margin-top: 15px;" onclick="swapMultiCityLocations(${legId})">
                <i class="fa-solid fa-right-left"></i>
            </div>
            <div class="search-input-group" style="flex: 1; margin: 0; position: relative;">
                <label>Going to</label>
                <input type="text" id="mc-dest-${legId}" class="form-control" placeholder="Add city, airport" autocomplete="off">
                <div class="autocomplete-dropdown" id="mc-dest-dropdown-${legId}"></div>
            </div>
            <div class="search-input-group" style="flex: 1; margin: 0;">
                <label>Date</label>
                <input type="text" id="mc-date-${legId}" class="form-control date-picker" placeholder="Add date">
            </div>
            ${legId > 2 ? `<div style="cursor: pointer; color: var(--danger); font-size: 16px; margin-top: 15px;" onclick="removeMultiCityLeg(${legId})"><i class="fa-solid fa-trash"></i></div>` : ''}
        </div>
    `;
    
    wrapper.appendChild(div);
    
    // Initialize flatpickr for the new input
    flatpickr(`#mc-date-${legId}`, {
        dateFormat: "Y-m-d",
        minDate: "today",
        altInput: true,
        altFormat: "F j, Y",
    });
    
    // Initialize autocomplete for origin and destination
    const originInput = document.getElementById(`mc-origin-${legId}`);
    const destInput = document.getElementById(`mc-dest-${legId}`);
    if (originInput) setupAutocompleteForInput(originInput, `mc-origin-dropdown-${legId}`);
    if (destInput) setupAutocompleteForInput(destInput, `mc-dest-dropdown-${legId}`);
}

function removeMultiCityLeg(legId) {
    const leg = document.getElementById(`multi-city-leg-${legId}`);
    if (leg) {
        leg.remove();
        // Recalculate labels for remaining legs
        const wrapper = document.getElementById("multi-city-legs-wrapper");
        Array.from(wrapper.children).forEach((child, index) => {
            child.querySelector("div").innerText = `Flight ${index + 1}`;
        });
    }
}

function swapMultiCityLocations(legId) {
    const o = document.getElementById(`mc-origin-${legId}`);
    const d = document.getElementById(`mc-dest-${legId}`);
    if (o && d) {
        const temp = o.value;
        o.value = d.value;
        d.value = temp;
    }
}

// Open booking details modal & Generate Seat Selection Grid
function openFlightBookModal(flightId, flNum, airline, totalAmt) {
    document.getElementById("modal-flight-id").value = flightId;
    document.getElementById("flight-modal-title").innerText = `Book Flight ${flNum} - ${airline}`;
    
    // Clear and reset Step 1 passenger details inputs
    document.getElementById("modal-passenger-name").value = "";
    document.getElementById("modal-passport-number").value = "";
    document.getElementById("modal-passenger-mobile").value = "";
    document.getElementById("modal-passenger-email").value = "";
    
    // Reset Step 3 agreement checkbox and trigger state lock
    const termsCheck = document.getElementById("modal-terms-agreement");
    if (termsCheck) {
        termsCheck.checked = false;
        toggleBookingButtons();
    }
    
    // Resolve selected flight details from cached array, or create local fallback
    currentSelectedFlight = lastSearchedFlights.find(f => f.id === flightId);
    if (!currentSelectedFlight) {
        currentSelectedFlight = {
            id: flightId,
            flight_number: flNum,
            airline: airline,
            price: parseFloat(totalAmt) - 15.00,
            origin: "CMB",
            destination: "DXB",
            departure_time: new Date().toISOString(),
            arrival_time: new Date().toISOString(),
            flight_type: "GDS"
        };
    }

    // Render Selected Flight Card preview at the top of Step 1 Traveler Info
    const previewContainer = document.getElementById("step-1-flight-card-container");
    if (previewContainer) {
        const depDate = new Date(currentSelectedFlight.departure_time);
        const arrDate = new Date(currentSelectedFlight.arrival_time);
        const hours = Math.abs(arrDate - depDate) / 36e5;
        const durationStr = `${Math.floor(hours)}h ${Math.round((hours % 1) * 60)}m`;
        const isRoundTrip = !!currentSelectedFlight.return_flight;
        const markupTotal = isRoundTrip ? 30.00 : 15.00;
        const totalPrice = currentSelectedFlight.price + markupTotal;

        let returnHTML = '';
        if (isRoundTrip) {
            const ret = currentSelectedFlight.return_flight;
            const retDepDate = new Date(ret.departure_time);
            const retArrDate = new Date(ret.arrival_time);
            const retHours = Math.abs(retArrDate - retDepDate) / 36e5;
            const retDurationStr = `${Math.floor(retHours)}h ${Math.round((retHours % 1) * 60)}m`;
            
            returnHTML = `
                <div style="border-top: 1px dashed rgba(255,255,255,0.1); margin: 10px 0; padding-top: 10px;"></div>
                <div style="display: flex; gap: 20px; align-items: center; font-size: 13px;">
                    <div class="airline-info" style="min-width: 140px; flex-shrink: 0; display: flex; gap: 8px; align-items: center;">
                        <div class="airline-logo-placeholder" style="background: rgba(0, 242, 254, 0.1); width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center;"><i class="fa-solid fa-plane" style="transform: rotate(180deg); font-size: 12px;"></i></div>
                        <div>
                            <div class="airline-name" style="font-weight: 600; color: #fff;">${ret.airline}</div>
                            <div class="flight-number" style="font-size: 11px; color: var(--text-muted);">${ret.flight_number} • <span class="badge-type" style="padding: 1px 4px; font-size: 9px;">${ret.flight_type}</span></div>
                        </div>
                    </div>
                    <div class="flight-route-flow" style="flex-grow: 1; display: flex; align-items: center; gap: 10px; justify-content: space-between;">
                        <div class="route-stop">
                            <div class="route-time" style="font-weight: 600; color: #fff;">${retDepDate.toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'})}</div>
                            <div class="route-airport" style="font-size: 11px; color: var(--text-muted); text-align: center;">${ret.origin}</div>
                        </div>
                        <div class="route-path-line" style="flex-grow: 1; height: 2px; background: rgba(255,255,255,0.1); position: relative; text-align: center; margin: 0 10px;">
                            <span class="route-duration" style="position: absolute; top: -14px; left: 50%; transform: translateX(-50%); font-size: 10px; color: var(--text-muted); white-space: nowrap;">${retDurationStr}</span>
                        </div>
                        <div class="route-stop">
                            <div class="route-time" style="font-weight: 600; color: #fff;">${retArrDate.toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'})}</div>
                            <div class="route-airport" style="font-size: 11px; color: var(--text-muted); text-align: center;">${ret.destination}</div>
                        </div>
                    </div>
                </div>
            `;
        }

        previewContainer.innerHTML = `
            <div class="flight-ticket-card" style="margin-bottom: 15px; padding: 15px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; display: flex; flex-direction: column; gap: 10px;">
                <div style="font-size: 11px; text-transform: uppercase; color: var(--primary); font-weight: 600; letter-spacing: 0.5px;">Selected Flight Details</div>
                <div style="display: flex; gap: 20px; align-items: center; font-size: 13px;">
                    <div class="airline-info" style="min-width: 140px; flex-shrink: 0; display: flex; gap: 8px; align-items: center;">
                        <div class="airline-logo-placeholder" style="background: rgba(0, 242, 254, 0.15); width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center;"><i class="fa-solid fa-plane" style="font-size: 12px;"></i></div>
                        <div>
                            <div class="airline-name" style="font-weight: 600; color: #fff;">${currentSelectedFlight.airline} ${isRoundTrip ? '(Outbound)' : ''}</div>
                            <div class="flight-number" style="font-size: 11px; color: var(--text-muted);">${currentSelectedFlight.flight_number} • <span class="badge-type" style="padding: 1px 4px; font-size: 9px;">${currentSelectedFlight.flight_type}</span></div>
                        </div>
                    </div>
                    <div class="flight-route-flow" style="flex-grow: 1; display: flex; align-items: center; gap: 10px; justify-content: space-between;">
                        <div class="route-stop">
                            <div class="route-time" style="font-weight: 600; color: #fff;">${depDate.toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'})}</div>
                            <div class="route-airport" style="font-size: 11px; color: var(--text-muted); text-align: center;">${currentSelectedFlight.origin}</div>
                        </div>
                        <div class="route-path-line" style="flex-grow: 1; height: 2px; background: rgba(255,255,255,0.1); position: relative; text-align: center; margin: 0 10px;">
                            <span class="route-duration" style="position: absolute; top: -14px; left: 50%; transform: translateX(-50%); font-size: 10px; color: var(--text-muted); white-space: nowrap;">${durationStr}</span>
                        </div>
                        <div class="route-stop">
                            <div class="route-time" style="font-weight: 600; color: #fff;">${arrDate.toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'})}</div>
                            <div class="route-airport" style="font-size: 11px; color: var(--text-muted); text-align: center;">${currentSelectedFlight.destination}</div>
                        </div>
                    </div>
                </div>
                ${returnHTML}
                <div style="border-top: 1px solid rgba(255,255,255,0.06); padding-top: 8px; display: flex; justify-content: space-between; align-items: center; font-size: 12.5px;">
                    <span style="color: var(--text-muted);">Consolidated Price (with markup):</span>
                    <strong style="color: var(--success); font-size: 15px;">${formatPrice(totalPrice)}</strong>
                </div>
            </div>
        `;
    }

    // Select seat map container
    const seatMap = document.getElementById("modal-seat-map");
    seatMap.innerHTML = "";
    selectedSeat = null;
    document.getElementById("modal-selected-seat-text").innerText = "None";
    
    const isRoundTrip = !!(currentSelectedFlight && currentSelectedFlight.return_flight);
    const markupTextEl = document.getElementById("modal-seat-markup-text");
    if (markupTextEl) {
        markupTextEl.innerText = isRoundTrip ? `+${formatPrice(30.00)}` : `+${formatPrice(15.00)}`;
    }
    
    // Generate simulated seats: 8 rows of A-B-C-D-E-F (C/D aisle)
    const rows = 8;
    const cols = ['A', 'B', 'C', 'aisle', 'D', 'E', 'F'];
    
    for (let r = 1; r <= rows; r++) {
        const rowDiv = document.createElement("div");
        rowDiv.className = "seat-map-row seat-row";
        
        cols.forEach(c => {
            const seat = document.createElement("div");
            if (c === "aisle") {
                seat.className = "seat aisle";
                seat.innerText = "";
            } else {
                const seatName = `${r}${c}`;
                // Randomize occupancy
                const isOccupied = Math.random() < 0.25;
                
                seat.className = `seat ${isOccupied ? 'occupied' : ''}`;
                seat.innerText = seatName;
                
                if (!isOccupied) {
                    seat.onclick = function() {
                        // De-select previous
                        const current = seatMap.querySelector(".seat.selected");
                        if (current) current.classList.remove("selected");
                        
                        // Select current
                        seat.classList.add("selected");
                        selectedSeat = seatName;
                        
                        if (isRoundTrip) {
                            const rowNum = parseInt(seatName);
                            const colLetter = seatName.replace(rowNum, "");
                            let returnCol = "F";
                            if (colLetter === "A") returnCol = "F";
                            else if (colLetter === "B") returnCol = "E";
                            else if (colLetter === "C") returnCol = "D";
                            else if (colLetter === "D") returnCol = "C";
                            else if (colLetter === "E") returnCol = "B";
                            else if (colLetter === "F") returnCol = "A";
                            const returnSeat = `${rowNum}${returnCol}`;
                            document.getElementById("modal-selected-seat-text").innerText = `${seatName} (Outbound) / ${returnSeat} (Return)`;
                        } else {
                            document.getElementById("modal-selected-seat-text").innerText = seatName;
                        }
                    };
                }
            }
            rowDiv.appendChild(seat);
        });
        seatMap.appendChild(rowDiv);
    }
    
    // Set stepper state to Step 1 (Passenger Details)
    currentBookingStep = 1;
    updateStepperUI();
    
    openModal("flight-book-modal");
}

// Stepper Navigation Controller
function navigateStepper(direction) {
    if (direction === 1) {
        // Step 1 traveler profile validation
        if (currentBookingStep === 1) {
            const passengerName = document.getElementById("modal-passenger-name").value.trim();
            const passportNumber = document.getElementById("modal-passport-number").value.trim();
            const mobile = document.getElementById("modal-passenger-mobile").value.trim();
            const email = document.getElementById("modal-passenger-email").value.trim();
            
            if (!passengerName) {
                showNotification("Field Required", "Please enter the passenger full legal name.", "danger");
                return;
            }
            if (!passportNumber) {
                showNotification("Field Required", "Please enter the traveler passport number.", "danger");
                return;
            }
            if (!mobile) {
                showNotification("Field Required", "Please enter the contact mobile number.", "danger");
                return;
            }
            if (!email) {
                showNotification("Field Required", "Please enter the email address for communications.", "danger");
                return;
            }
            
            // Basic email pattern matching check
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                showNotification("Invalid Entry", "Please enter a valid passenger email address.", "danger");
                return;
            }
        }
        // Step 2 seat selector validation
        else if (currentBookingStep === 2) {
            if (!selectedSeat) {
                showNotification("Seat Required", "Please select a seat from the interactive seat map layout.", "danger");
                return;
            }
        }
    }
    
    currentBookingStep += direction;
    if (currentBookingStep < 1) currentBookingStep = 1;
    if (currentBookingStep > 3) currentBookingStep = 3;
    
    updateStepperUI();
}

// Stepper UI visibility and indicator updates
function updateStepperUI() {
    // 1. Update stepper header progress tracker nodes
    document.querySelectorAll(".stepper-step").forEach((node, idx) => {
        const stepNum = idx + 1;
        node.classList.remove("active", "completed");
        if (stepNum === currentBookingStep) {
            node.classList.add("active");
        } else if (stepNum < currentBookingStep) {
            node.classList.add("completed");
        }
    });
    
    // 2. Toggle active layout screens
    document.querySelectorAll(".stepper-content-view").forEach((view, idx) => {
        const stepNum = idx + 1;
        if (stepNum === currentBookingStep) {
            view.classList.add("active");
        } else {
            view.classList.remove("active");
        }
    });
    
    // 3. Toggle stepper footer navigation action buttons
    const btnBack = document.getElementById("btn-stepper-back");
    const btnNext = document.getElementById("btn-stepper-next");
    const btnSave = document.getElementById("btn-stepper-save");
    const btnTicket = document.getElementById("btn-stepper-ticket");
    const btnPayment = document.getElementById("btn-stepper-payment");
    
    if (btnSave) btnSave.style.display = "none";
    if (btnTicket) btnTicket.style.display = "none";
    
    if (currentBookingStep === 1) {
        btnBack.style.display = "none";
        btnNext.style.display = "inline-flex";
        if (btnPayment) btnPayment.style.display = "none";
    } else if (currentBookingStep === 2) {
        btnBack.style.display = "inline-flex";
        btnNext.style.display = "inline-flex";
        if (btnPayment) btnPayment.style.display = "none";
    } else if (currentBookingStep === 3) {
        btnBack.style.display = "inline-flex";
        btnNext.style.display = "none";
        if (btnPayment) btnPayment.style.display = "inline-flex";
        
        // Dynamic formatting of confirmation details
        renderStepperSummary();
    }

}

// Format and render Step 3 checkout summary list
function renderStepperSummary() {
    if (!currentSelectedFlight) return;
    
    const f = currentSelectedFlight;
    
    // Extract Traveler Inputs
    const passName = document.getElementById("modal-passenger-name").value.trim();
    const passPassport = document.getElementById("modal-passport-number").value.trim();
    const passMobile = document.getElementById("modal-passenger-mobile").value.trim();
    const passEmail = document.getElementById("modal-passenger-email").value.trim();
    
    // Populate Profile Fields
    document.getElementById("summary-pass-name").innerText = passName || "N/A";
    document.getElementById("summary-pass-passport").innerText = passPassport || "N/A";
    document.getElementById("summary-pass-mobile").innerText = passMobile || "N/A";
    document.getElementById("summary-pass-email").innerText = passEmail || "N/A";
    
    // Populate Sector details & dynamic return mapping
    let routeHTML = `${f.origin} <i class="fa-solid fa-arrow-right" style="color:var(--primary); font-size:11px;"></i> ${f.destination}`;
    let airlineText = `${f.airline} (${f.flight_number})`;
    
    const depDate = new Date(f.departure_time);
    const arrDate = new Date(f.arrival_time);
    let timeText = `${depDate.toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'})} - ${arrDate.toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'})}`;
    
    let seatText = selectedSeat || "None Selected";
    let markupTotal = 15.00;
    
    if (f.return_flight) {
        const ret = f.return_flight;
        routeHTML += ` <span style="margin: 0 8px; color: var(--text-muted);">|</span> ${ret.origin} <i class="fa-solid fa-arrow-right" style="color:var(--primary); font-size:11px;"></i> ${ret.destination}`;
        airlineText += ` / ${ret.airline} (${ret.flight_number})`;
        
        const retDepDate = new Date(ret.departure_time);
        const retArrDate = new Date(ret.arrival_time);
        timeText += ` | Return: ${retDepDate.toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'})} - ${retArrDate.toLocaleTimeString(undefined, {hour: '2-digit', minute:'2-digit'})}`;
        
        // Calculate return seat number dynamically
        let returnSeat = "14F";
        if (selectedSeat) {
            const row = parseInt(selectedSeat);
            const col = selectedSeat.replace(row, "");
            let returnCol = "F";
            if (col === "A") returnCol = "F";
            else if (col === "B") returnCol = "E";
            else if (col === "C") returnCol = "D";
            else if (col === "D") returnCol = "C";
            else if (col === "E") returnCol = "B";
            else if (col === "F") returnCol = "A";
            returnSeat = `${row}${returnCol}`;
        }
        seatText += ` (Outbound) / ${returnSeat} (Return)`;
        markupTotal = 30.00;
    }
    
    document.getElementById("summary-flight-route").innerHTML = routeHTML;
    document.getElementById("summary-flight-airline").innerText = airlineText;
    document.getElementById("summary-flight-type").innerText = f.flight_type;
    document.getElementById("summary-flight-time").innerText = timeText;
    document.getElementById("summary-pass-seat").innerText = seatText;
    
    // Display payable consolidated price markup
    let totalAmt;
    if (activeBookingPath === "hold") {
        totalAmt = 2.00; // Hold charge is 2 USD / 600 LKR
    } else {
        totalAmt = f.price + markupTotal;
    }
    document.getElementById("summary-total-fare").innerText = formatPrice(totalAmt);
    
    // Dynamically update Hold description to reflect currency charge
    const holdDesc = document.querySelector("#opt-hold-booking .opt-card-desc");
    if (holdDesc) {
        holdDesc.innerHTML = `Secure seats and fare for 24 hours. Hold charge: <strong>${formatPrice(2.00)}</strong> will be charged immediately.`;
    }
}

// Selects the booking path (Hold vs Ticket) and updates the UI
function selectBookingPath(path) {
    activeBookingPath = path;
    const holdCard = document.getElementById("opt-hold-booking");
    const ticketCard = document.getElementById("opt-book-ticket");
    
    if (holdCard && ticketCard) {
        if (path === "hold") {
            holdCard.classList.add("active");
            ticketCard.classList.remove("active");
        } else {
            ticketCard.classList.add("active");
            holdCard.classList.remove("active");
        }
    }
    
    // Refresh stepper summary to update prices
    renderStepperSummary();
}


// Terms Agreement checkbox change listener
function toggleBookingButtons() {
    const agreedCheckbox = document.getElementById("modal-terms-agreement");
    const agreed = agreedCheckbox ? agreedCheckbox.checked : false;
    
    const btnSave = document.getElementById("btn-stepper-save");
    const btnTicket = document.getElementById("btn-stepper-ticket");
    const btnPayment = document.getElementById("btn-stepper-payment");
    
    if (agreed) {
        if (btnSave) btnSave.removeAttribute("disabled");
        if (btnTicket) btnTicket.removeAttribute("disabled");
        if (btnPayment) btnPayment.removeAttribute("disabled");
    } else {
        if (btnSave) btnSave.setAttribute("disabled", "true");
        if (btnTicket) btnTicket.setAttribute("disabled", "true");
        if (btnPayment) btnPayment.setAttribute("disabled", "true");
    }
}

// Process B2B checkout flight booking (Reservation Hold or Immediate Ticketing)
function processFlightBooking(ticketNow, paymentMethod = 'credit') {
    const flightId = document.getElementById("modal-flight-id").value;
    const passengerName = document.getElementById("modal-passenger-name").value.trim();
    const passportNumber = document.getElementById("modal-passport-number").value.trim();
    const mobile = document.getElementById("modal-passenger-mobile").value.trim();
    const email = document.getElementById("modal-passenger-email").value.trim();
    
    if (!passengerName) {
        showNotification("Missing Passenger", "Please enter the passenger legal name to proceed.", "danger");
        return;
    }
    if (!passportNumber) {
        showNotification("Missing Passport", "Please enter the passport number.", "danger");
        return;
    }
    if (!mobile) {
        showNotification("Missing Mobile", "Please enter the contact mobile number.", "danger");
        return;
    }
    if (!email) {
        showNotification("Missing Email", "Please enter the passenger email address.", "danger");
        return;
    }
    if (!selectedSeat) {
        showNotification("Missing Seat Selection", "Please select a seat from the interactive seat map.", "danger");
        return;
    }
    
    // Lock agreement validation client-side
    const agreedCheckbox = document.getElementById("modal-terms-agreement");
    if (!agreedCheckbox || !agreedCheckbox.checked) {
        showNotification("Agreement Required", "You must agree to the airline fare rules and terms and conditions.", "danger");
        return;
    }
    
    const payload = {
        flight_id: parseInt(flightId),
        passenger_name: passengerName,
        passport_number: passportNumber,
        mobile: mobile,
        email: email,
        seat_number: selectedSeat,
        ticket_now: ticketNow,
        payment_method: paymentMethod,
        active_booking_path: activeBookingPath
    };

    
    if (currentSelectedFlight && currentSelectedFlight.return_flight) {
        payload.return_flight_id = parseInt(currentSelectedFlight.return_flight.id);
        
        let returnSeat = "14F";
        if (selectedSeat) {
            const row = parseInt(selectedSeat);
            const col = selectedSeat.replace(row, "");
            let returnCol = "F";
            if (col === "A") returnCol = "F";
            else if (col === "B") returnCol = "E";
            else if (col === "C") returnCol = "D";
            else if (col === "D") returnCol = "C";
            else if (col === "E") returnCol = "B";
            else if (col === "F") returnCol = "A";
            returnSeat = `${row}${returnCol}`;
        }
        payload.return_seat_number = returnSeat;
    }

    fetch("/api/flights/book", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => {
        closeModal("flight-book-modal");
        if (data.success) {
            showNotification(ticketNow ? "Ticket Issued!" : "Reservation Saved!", data.message, "success");
            updateAgentUI();
            switchTab("bookings");
        } else {
            if (data.code === "INSUFFICIENT_CREDIT") {
                showNotification("Insufficient Credit Error", "Your credit balance is insufficient. The ticket was not issued. Please top up.", "danger");
            } else {
                showNotification("Booking Failed", data.error, "danger");
            }
        }
    });
}


// Hotel Search Logic
function searchHotels() {
    const location = document.getElementById("hotel-location").value;
    const container = document.getElementById("hotel-results-container");
    container.innerHTML = `<div style="text-align:center; padding:40px; grid-column: span 3;"><i class="fa-solid fa-circle-notch fa-spin" style="font-size:32px; color:var(--primary);"></i><p style="margin-top:10px;">Interrogating wholesale hotel API channels...</p></div>`;
    
    fetch(`/api/hotels/search?location=${location}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                lastSearchedHotels = data.hotels; // Cache in global state
                renderHotelSearchResults(lastSearchedHotels);
            }
        });
}

function renderHotelSearchResults(hotels) {
    window.b2bHotelResults = hotels; // Save globally to avoid string escaping issues
    const container = document.getElementById("hotel-results-container");
    container.innerHTML = "";
    
    // Change layout of container to support grid
    container.style.display = 'grid';
    container.style.gridTemplateColumns = 'repeat(auto-fill, minmax(300px, 1fr))';
    container.style.gap = '25px';
    
    if (!hotels || hotels.length === 0) {
        container.innerHTML = "<div style='background: white; padding: 40px; text-align: center; border-radius: 12px; grid-column: 1/-1;'><i class='fa-solid fa-hotel' style='font-size: 40px; color: #cbd5e1; margin-bottom: 15px;'></i><h3 style='margin:0; color:#475569;'>No hotels found</h3><p style='color:#94a3b8;'>Try a different destination or dates.</p></div>";
        return;
    }
    
    hotels.forEach(h => {
        let starIcons = "";
        for (let i = 0; i < h.rating; i++) {
            starIcons += `<i class="fa-solid fa-star"></i>`;
        }
        
        let checkin = document.getElementById("hotel-checkin") ? document.getElementById("hotel-checkin").value : "2026-06-15";
        let checkout = document.getElementById("hotel-checkout") ? document.getElementById("hotel-checkout").value : "2026-06-18";
        
        // Calculate nights
        const checkinDate = new Date(checkin);
        const checkoutDate = new Date(checkout);
        let nights = Math.ceil(Math.abs(checkoutDate - checkinDate) / (1000 * 3600 * 24));
        if (isNaN(nights) || nights === 0) nights = 1;
        
        let lowestPrice = Infinity;
        if (h.rooms && h.rooms.length > 0) {
            h.rooms.forEach(r => { if(r.price_per_night < lowestPrice) lowestPrice = r.price_per_night; });
        }
        if (lowestPrice === Infinity) lowestPrice = 0;
        
        let hotelImage = `/static/img/${h.image_url}`;
        const localImages = ['hotel_london.jpg', 'hotel_dubai.jpg', 'hotel_maldives.jpg', 'hotel_singapore.jpg'];
        if (!h.image_url || !localImages.includes(h.image_url)) {
            const loc = (h.location || "").toLowerCase();
            if (loc.includes('maldives') || loc.includes('mle')) hotelImage = 'https://images.unsplash.com/photo-1506929562872-bb421503ef21?auto=format&fit=crop&w=800';
            else if (loc.includes('london') || loc.includes('uk')) hotelImage = 'https://images.unsplash.com/photo-1517841905240-472988babdf9?auto=format&fit=crop&w=800';
            else if (loc.includes('dubai') || loc.includes('uae')) hotelImage = 'https://images.unsplash.com/photo-1582719508461-905c673771fd?auto=format&fit=crop&w=800';
            else if (loc.includes('singapore')) hotelImage = 'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=800';
            else if (loc.includes('colombo') || loc.includes('sri lanka') || loc.includes('cmb')) hotelImage = 'https://images.unsplash.com/photo-1546548970-71785318a17b?auto=format&fit=crop&w=800';
            else hotelImage = 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800';
        }
        
        h.resolved_image = hotelImage; // save for later
        
        container.innerHTML += `
            <div style="background: white; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; display: flex; flex-direction: column; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); transition: transform 0.2s, box-shadow 0.2s;" onmouseover="this.style.transform='translateY(-4px)'; this.style.boxShadow='0 10px 15px -3px rgba(0, 0, 0, 0.1)';" onmouseout="this.style.transform='none'; this.style.boxShadow='0 4px 6px -1px rgba(0, 0, 0, 0.05)';">
                <div style="position: relative; height: 200px;">
                    <img src="${hotelImage}" alt="${h.name}" style="width: 100%; height: 100%; object-fit: cover;" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800';">
                    <div style="position: absolute; top: 15px; left: 15px; background: #0f172a; color: white; padding: 4px 10px; font-size: 11px; font-weight: 700; border-radius: 4px; letter-spacing: 0.5px;">B2B RATE</div>
                </div>
                <div style="padding: 20px; display: flex; flex-direction: column; flex-grow: 1;">
                    <div style="flex-grow: 1;">
                        <div style="color: #fbbf24; font-size: 13px; margin-bottom: 5px;">${starIcons}</div>
                        <h3 style="margin: 0 0 5px 0; font-size: 18px; color: #0f172a; font-weight: 700;">${h.name}</h3>
                        <div style="font-size: 13px; color: #64748b; margin-bottom: 12px; display: flex; align-items: center; gap: 5px;"><i class="fa-solid fa-location-dot" style="color: #c3122e;"></i> ${h.location}</div>
                        <p style="font-size: 14px; color: #475569; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${h.description}</p>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 20px; border-top: 1px solid #f1f5f9; padding-top: 15px;">
                        <div>
                            <div style="font-size: 12px; color: #64748b; font-weight: 600;">Starting from</div>
                            <div style="font-size: 22px; font-weight: 800; color: #0f172a;">LKR ${lowestPrice.toLocaleString()}<span style="font-size: 12px; color: #64748b; font-weight: normal;">/night</span></div>
                        </div>
                        <button style="background: #2563eb; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 700; font-size: 15px; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='#1d4ed8';" onmouseout="this.style.background='#2563eb';" onclick="viewB2BHotelDetails(${h.id}, '${checkin}', '${checkout}', ${nights})">See Availability <i class="fa-solid fa-chevron-right" style="font-size: 12px; margin-left: 5px;"></i></button>
                    </div>
                </div>
            </div>
        `;
    });
}

function viewB2BHotelDetails(hotelId, checkin, checkout, nights) {
    if (!window.b2bHotelResults) return;
    const h = window.b2bHotelResults.find(x => x.id === hotelId);
    if (!h) return;
    
    const roomsDataRaw = JSON.stringify(h.rooms || []);
    const params = new URLSearchParams({
        hotel_name: h.name || 'Hotel',
        hotel_loc: h.location || 'Location',
        hotel_desc: h.description || '',
        room_img: h.resolved_image || '',
        rooms_data: roomsDataRaw,
        checkin: checkin,
        checkout: checkout,
        nights: nights
    });
    window.open(`/hotel-details?${params.toString()}`, '_blank');
}

// Load Agent Bookings list
function loadBookings() {
    fetch("/api/bookings/list")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const tbody = document.getElementById("bookings-list-table");
                tbody.innerHTML = "";
                
                let ticketed = 0;
                let pending = 0;
                
                if (data.bookings.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--text-muted); padding:30px 0;">No active bookings found.</td></tr>`;
                    return;
                }
                
                data.bookings.forEach(b => {
                    let statusClass = "badge-reservation";
                    if (b.status === "ticketed") { statusClass = "badge-ticketed"; ticketed++; }
                    else if (b.status === "refunded") { statusClass = "badge-refunded"; }
                    else if (b.status === "voided") { statusClass = "badge-voided"; }
                    else { pending++; }
                    
                    let detailsHTML = "";
                    let actionHTML = "";
                    
                    if (b.booking_type === "flight" && b.details) {
                        const d = b.details;
                        let pnrHTML = d.pnr_reference ? `<br>Ref: <strong style="color:var(--warning); font-family:monospace; font-size:12px;">${d.pnr_reference}</strong>` : '';
                        let ticketHTML = d.ticket_number ? `<br>Tkt: <strong style="color:var(--success); font-family:monospace; font-size:12px;">${d.ticket_number}</strong>` : (b.status === "non-ticketed" ? `<br><span style="color:var(--text-muted); font-size:11.5px;">Tkt: Not Ticketed</span>` : '');
                        
                        let returnSegmentHTML = "";
                        if (d.return_segment) {
                            const r = d.return_segment;
                            let rPnrHTML = r.pnr_reference ? `<br>Ref: <strong style="color:var(--warning); font-family:monospace; font-size:12px;">${r.pnr_reference}</strong>` : '';
                            let rTicketHTML = r.ticket_number ? `<br>Tkt: <strong style="color:var(--success); font-family:monospace; font-size:12px;">${r.ticket_number}</strong>` : (b.status === "non-ticketed" ? `<br><span style="color:var(--text-muted); font-size:11.5px;">Tkt: Not Ticketed</span>` : '');
                            returnSegmentHTML = `
                                <div style="border-top: 1px dashed rgba(255,255,255,0.1); margin: 8px 0; padding-top: 8px;">
                                    <strong>${r.airline} (${r.flight_number})</strong> (${r.gds_type}) (Return)<br>
                                    ${r.origin} <i class="fa-solid fa-plane" style="font-size:10px; color:var(--primary); transform: rotate(180deg);"></i> ${r.destination}<br>
                                    Seat: ${r.seat_number}${rPnrHTML}${rTicketHTML}
                                </div>
                            `;
                        }
                        
                        detailsHTML = `
                            <strong>${d.airline} (${d.flight_number})</strong> (${d.gds_type})<br>
                            ${d.origin} <i class="fa-solid fa-plane" style="font-size:10px; color:var(--primary);"></i> ${d.destination}<br>
                            Seat: ${d.seat_number}${pnrHTML}${ticketHTML}
                            ${returnSegmentHTML}
                        `;
                        
                        if (b.status === "non-ticketed") {
                            actionHTML = `
                                <div class="btn-action-group">
                                    <button class="btn-action btn-ticket" onclick="ticketReservation(${b.id})">Ticket Now</button>
                                    <button class="btn-action btn-danger" onclick="voidReservation(${b.id})">Void</button>
                                </div>
                            `;
                        } else if (b.status === "ticketed") {
                            actionHTML = `
                                <div class="btn-action-group">
                                    <button class="btn-action" onclick="openReissueModal(${b.id}, ${d.flight_id}, ${d.original_price})">ATC Re-Issue</button>
                                    <button class="btn-action btn-danger" onclick="refundBooking(${b.id})">TRF Refund</button>
                                </div>
                            `;
                        }
                    } else if (b.booking_type === "hotel" && b.details) {
                        const d = b.details;
                        detailsHTML = `
                            <strong>${d.hotel_name}</strong><br>
                            Room: ${d.room_type}<br>
                            Check In: ${d.check_in.split('T')[0]}
                        `;
                        
                        if (b.status === "ticketed") {
                            actionHTML = `
                                <button class="btn-action btn-danger" onclick="refundBooking(${b.id})">Cancel & Refund</button>
                            `;
                        }
                    }
                    
                    tbody.innerHTML += `
                        <tr>
                            <td><strong style="color:#fff;">${b.invoice_number}</strong></td>
                            <td><span class="badge-type">${b.booking_type.toUpperCase()}</span></td>
                            <td>${b.booking_type === 'flight' ? b.details.passenger_name : b.details.guest_name}</td>
                            <td>${detailsHTML}</td>
                            <td style="font-weight:700; color:var(--primary);">${formatPrice(b.total_price)}</td>
                            <td style="font-size:12px;">${b.created_at.split('T')[0]}</td>
                            <td><span class="badge ${statusClass}">${b.status}</span></td>
                            <td>${actionHTML}</td>
                        </tr>
                    `;
                });
                
                // Update dash stats
                if (document.getElementById("dashboard-ticketed-count")) {
                    document.getElementById("dashboard-ticketed-count").innerText = ticketed;
                    document.getElementById("dashboard-pending-count").innerText = pending;
                }
            }
        });
}

// Ticket non-ticketed reservation
function ticketReservation(bookingId) {
    if (!confirm("Are you sure you want to issue ticket? This will deduct from your credit balance instantly.")) return;
    
    fetch("/api/bookings/ticket", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ booking_id: bookingId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showNotification("Ticket Issued", data.message, "success");
            updateAgentUI();
            loadBookings();
        } else {
            showNotification("Ticketing Failed", data.error, "danger");
        }
    });
}

// Void non-ticketed reservation
function voidReservation(bookingId) {
    if (!confirm("Void this reservation? It will release the seats immediately without penalty.")) return;
    
    fetch("/api/bookings/void", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ booking_id: bookingId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showNotification("Reservation Cancelled", data.message, "success");
            loadBookings();
            if (typeof loadCancellations === "function") {
                loadCancellations();
            }
        } else {
            showNotification("Void Failed", data.error, "danger");
        }
    });
}

// Refund simulated GDS TRF
function refundBooking(bookingId) {
    if (!confirm("WARNING: Trigger Ticket Refund Functionality (TRF)? Flight Hub penalty rules will calculate cancellation penalty and credit refund back instantly.")) return;
    
    fetch("/api/bookings/refund", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ booking_id: bookingId })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const d = data.details;
            const message = `Net Credit Refunded: ${formatPrice(d.net_refund_credited)}. GDS penalty: ${formatPrice(d.amadeus_cancellation_penalty)}. Agency refund fee: ${formatPrice(d.refund_service_markup)}.`;
            alert("TRF REFUND PROCESSED BY FLIGHT HUB:\n\n" + message);
            showNotification("TRF Refund Processed", "Net refund balance credited to wallet.", "success");
            updateAgentUI();
            loadBookings();
            if (typeof loadCancellations === "function") {
                loadCancellations();
            }
        } else {
            showNotification("Refund Failed", data.error, "danger");
        }
    });
}

// Load bookings list and render under cancellations tab
function loadCancellations() {
    fetch("/api/bookings/list")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const tbody = document.getElementById("cancellations-list-table");
                tbody.innerHTML = "";
                
                if (data.bookings.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:var(--text-muted); padding:30px 0;">No bookings found.</td></tr>`;
                    return;
                }
                
                data.bookings.forEach(b => {
                    let statusClass = "badge-reservation";
                    if (b.status === "ticketed") { statusClass = "badge-ticketed"; }
                    else if (b.status === "refunded") { statusClass = "badge-refunded"; }
                    else if (b.status === "voided") { statusClass = "badge-voided"; }
                    
                    let detailsHTML = "";
                    let actionHTML = "";
                    
                    if (b.booking_type === "flight" && b.details) {
                        const d = b.details;
                        let pnrHTML = d.pnr_reference ? `<br>Ref: <strong style="color:var(--warning); font-family:monospace; font-size:12px;">${d.pnr_reference}</strong>` : '';
                        let ticketHTML = d.ticket_number ? `<br>Tkt: <strong style="color:var(--success); font-family:monospace; font-size:12px;">${d.ticket_number}</strong>` : (b.status === "non-ticketed" ? `<br><span style="color:var(--text-muted); font-size:11.5px;">Tkt: Not Ticketed</span>` : '');
                        
                        let returnSegmentHTML = "";
                        if (d.return_segment) {
                            const r = d.return_segment;
                            let rPnrHTML = r.pnr_reference ? `<br>Ref: <strong style="color:var(--warning); font-family:monospace; font-size:12px;">${r.pnr_reference}</strong>` : '';
                            let rTicketHTML = r.ticket_number ? `<br>Tkt: <strong style="color:var(--success); font-family:monospace; font-size:12px;">${r.ticket_number}</strong>` : (b.status === "non-ticketed" ? `<br><span style="color:var(--text-muted); font-size:11.5px;">Tkt: Not Ticketed</span>` : '');
                            returnSegmentHTML = `
                                <div style="border-top: 1px dashed rgba(255,255,255,0.1); margin: 8px 0; padding-top: 8px;">
                                    <strong>${r.airline} (${r.flight_number})</strong> (${r.gds_type}) (Return)<br>
                                    ${r.origin} <i class="fa-solid fa-plane" style="font-size:10px; color:var(--primary); transform: rotate(180deg);"></i> ${r.destination}<br>
                                    Seat: ${r.seat_number}${rPnrHTML}${rTicketHTML}
                                </div>
                            `;
                        }
                        
                        detailsHTML = `
                            <strong>${d.airline} (${d.flight_number})</strong> (${d.gds_type})<br>
                            ${d.origin} <i class="fa-solid fa-plane" style="font-size:10px; color:var(--primary);"></i> ${d.destination}<br>
                            Seat: ${d.seat_number}${pnrHTML}${ticketHTML}
                            ${returnSegmentHTML}
                        `;
                        
                        if (b.status === "non-ticketed") {
                            actionHTML = `
                                <button class="btn-action btn-danger" onclick="voidReservation(${b.id})">
                                    <i class="fa-solid fa-ban"></i> Void (No Penalty)
                                </button>
                            `;
                        } else if (b.status === "ticketed") {
                            actionHTML = `
                                <button class="btn-action btn-danger" onclick="refundBooking(${b.id})">
                                    <i class="fa-solid fa-receipt"></i> TRF Refund
                                </button>
                            `;
                        } else {
                            actionHTML = `<span class="badge ${statusClass}">${b.status.toUpperCase()}</span>`;
                        }
                    } else if (b.booking_type === "hotel" && b.details) {
                        const d = b.details;
                        detailsHTML = `
                            <strong>${d.hotel_name}</strong><br>
                            Room: ${d.room_type}<br>
                            Check In: ${d.check_in.split('T')[0]}
                        `;
                        
                        if (b.status === "ticketed") {
                            actionHTML = `
                                <button class="btn-action btn-danger" onclick="refundBooking(${b.id})">
                                    <i class="fa-solid fa-receipt"></i> Cancel & Refund
                                </button>
                            `;
                        } else {
                            actionHTML = `<span class="badge ${statusClass}">${b.status.toUpperCase()}</span>`;
                        }
                    } else {
                        detailsHTML = `N/A`;
                        if (b.status === "ticketed") {
                            actionHTML = `<button class="btn-action btn-danger" onclick="refundBooking(${b.id})">Refund</button>`;
                        } else if (b.status === "non-ticketed") {
                            actionHTML = `<button class="btn-action btn-danger" onclick="voidReservation(${b.id})">Void</button>`;
                        } else {
                            actionHTML = `<span class="badge ${statusClass}">${b.status.toUpperCase()}</span>`;
                        }
                    }
                    
                    const passengerName = b.booking_type === 'flight' ? (b.details ? b.details.passenger_name : 'N/A') : (b.details ? b.details.guest_name : 'N/A');
                    
                    tbody.innerHTML += `
                        <tr>
                            <td><strong style="color:#fff;">${b.invoice_number}</strong></td>
                            <td><span class="badge-type">${b.booking_type.toUpperCase()}</span></td>
                            <td>${passengerName}</td>
                            <td>${detailsHTML}</td>
                            <td style="font-weight:700; color:var(--primary);">${formatPrice(b.total_price)}</td>
                            <td style="font-size:12px;">${b.created_at.split('T')[0]}</td>
                            <td><span class="badge ${statusClass}">${b.status}</span></td>
                            <td>${actionHTML}</td>
                        </tr>
                    `;
                });
            }
        });
}

// Re-issue Simulated GDS ATC
let currentReissueOriginalFare = 0;

function openReissueModal(bookingId, currentFlightId, originalFare) {
    document.getElementById("reissue-booking-id").value = bookingId;
    currentReissueOriginalFare = originalFare;
    document.getElementById("reissue-old-fare").innerText = formatPrice(originalFare);
    
    const penaltyAlert = document.getElementById("reissue-penalty-text");
    if (penaltyAlert) {
        penaltyAlert.innerHTML = `Flight cancellation penalty applied: <strong>${formatPrice(50.00)}</strong>. Service fee markup applied: <strong>${formatPrice(25.00)}</strong>.`;
    }
    
    // Fetch all active flights to populate re-issue options
    fetch("/api/flights/search")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const select = document.getElementById("reissue-new-flight-id");
                select.innerHTML = "";
                
                data.flights.forEach(f => {
                    if (f.id !== currentFlightId) {
                        select.innerHTML += `<option value="${f.id}" data-price="${f.price}">${f.flight_number} - ${f.airline} (${f.origin} to ${f.destination}) - Base fare: ${formatPrice(f.price)}</option>`;
                    }
                });
                
                calculateReissueFareDiff();
                openModal("reissue-modal");
            }
        });
}

function calculateReissueFareDiff() {
    const select = document.getElementById("reissue-new-flight-id");
    if (select.options.length === 0) return;
    
    const selectedOption = select.options[select.selectedIndex];
    const newPrice = parseFloat(selectedOption.getAttribute("data-price"));
    
    document.getElementById("reissue-new-fare").innerText = formatPrice(newPrice);
    
    const fareDiff = Math.max(0, newPrice - currentReissueOriginalFare);
    document.getElementById("reissue-fare-diff").innerText = formatPrice(fareDiff);
    
    const penalty = 50.00;
    const agencyFee = 25.00;
    const total = fareDiff + penalty + agencyFee;
    
    const penaltyEl = document.getElementById("reissue-gds-penalty");
    if (penaltyEl) penaltyEl.innerText = formatPrice(penalty);
    
    const markupEl = document.getElementById("reissue-agency-markup");
    if (markupEl) markupEl.innerText = formatPrice(agencyFee);
    
    document.getElementById("reissue-total-cost").innerText = formatPrice(total);
}

function submitReissueChange() {
    const bookingId = document.getElementById("reissue-booking-id").value;
    const select = document.getElementById("reissue-new-flight-id");
    if (select.options.length === 0) return;
    const newFlightId = select.value;
    
    fetch("/api/bookings/reissue", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            booking_id: parseInt(bookingId),
            new_flight_id: parseInt(newFlightId)
        })
    })
    .then(res => res.json())
    .then(data => {
        closeModal("reissue-modal");
        if (data.success) {
            const d = data.details;
            const message = `Auto Re-issue complete!\nGDS Penalty: ${formatPrice(d.amadeus_penalty)}\nFare Difference Collected: ${formatPrice(d.fare_difference)}\nAgency markup: ${formatPrice(d.service_markup)}\n\nTotal charged: ${formatPrice(d.total_charged)}`;
            alert(message);
            showNotification("Auto Re-Issue Completed", "Seat reassigned, ticket updated.", "success");
            updateAgentUI();
            loadBookings();
        } else {
            showNotification("Re-Issue Failed", data.error, "danger");
        }
    });
}

// Timatic Visa Check Simulator
function checkTimatic() {
    const passport = document.getElementById("timatic-passport").value;
    const dest = document.getElementById("timatic-dest").value;
    
    fetch("/api/timatic/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ passport: passport, destination: dest })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            const resultBox = document.getElementById("timatic-result-box");
            document.getElementById("timatic-result-header-text").innerText = `TIMATIC VISA ANSWER FOR TRAVEL TO: ${data.destination.toUpperCase()}`;
            document.getElementById("timatic-result-text-body").innerHTML = `
                <strong>Citizenship / Passport:</strong> ${data.passport}<br>
                <strong>Destination:</strong> ${data.destination}<br><br>
                <div style="padding:10px; background: rgba(0,0,0,0.15); border-radius:6px; border-left: 3px solid var(--primary); font-family:monospace; font-size:12.5px;">
                    ${data.result}
                </div>
            `;
            resultBox.style.display = "block";
            
            showNotification("Timatic Query Response", "Visa intelligence details fetched successfully.", "info");
            loadTimaticLogs();
            
            // Add 1 to Timatic stat card if viewing dashboard later
            const statVal = document.getElementById("dashboard-timatic-count");
            if (statVal) {
                statVal.innerText = parseInt(statVal.innerText) + 1;
            }
        }
    });
}

function loadTimaticLogs() {
    fetch("/api/timatic/logs")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const tbody = document.getElementById("timatic-logs-table");
                tbody.innerHTML = "";
                
                if (data.logs.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted);">No queries made yet.</td></tr>`;
                    return;
                }
                
                data.logs.forEach(l => {
                    tbody.innerHTML += `
                        <tr>
                            <td>${l.checked_at.split('T')[0]}</td>
                            <td><strong>${l.passport_country}</strong></td>
                            <td><strong>${l.destination_country}</strong></td>
                            <td style="color:var(--text-muted); font-size:12px;">${l.result.substring(0, 75)}...</td>
                        </tr>
                    `;
                });
                
                // Load count in stat card
                const statVal = document.getElementById("dashboard-timatic-count");
                if (statVal) {
                    statVal.innerText = data.logs.length;
                }
            }
        });
}

// Helpdesk ticket Submission
function submitSupportTicket() {
    const subject = document.getElementById("support-subject").value.trim();
    const message = document.getElementById("support-message").value.trim();
    
    if (!subject || !message) {
        showNotification("Blank Fields", "Subject and description inquiry are required.", "danger");
        return;
    }
    
    fetch("/api/support/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subject: subject, message: message })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showNotification("Ticket Created", data.message, "success");
            document.getElementById("support-subject").value = "";
            document.getElementById("support-message").value = "";
            loadSupportTickets();
        } else {
            showNotification("Creation Failed", data.error, "danger");
        }
    });
}

function loadSupportTickets() {
    fetch("/api/support/list")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const tbody = document.getElementById("support-tickets-table");
                tbody.innerHTML = "";
                
                if (data.tickets.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="3" style="text-align:center; color:var(--text-muted); padding:30px 0;">No active helpdesk tickets.</td></tr>`;
                    return;
                }
                
                data.tickets.forEach(t => {
                    const statusClass = t.status === 'open' ? 'badge-reservation' : 'badge-ticketed';
                    tbody.innerHTML += `
                        <tr>
                            <td>${t.created_at.split('T')[0]}</td>
                            <td><strong>${t.subject}</strong><br><span style="color:var(--text-muted); font-size:11.5px;">${t.message.substring(0, 50)}...</span></td>
                            <td><span class="badge ${statusClass}">${t.status}</span></td>
                        </tr>
                    `;
                });
            }
        });
}

// Reports Dynamic calculations & Chart.js rendering
let chartTO = null;
let chartGP = null;

function loadAgentReports() {
    fetch("/api/reports/togp")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const tbody = document.getElementById("reports-daily-table");
                tbody.innerHTML = "";
                
                if (data.daily.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted); padding:20px 0;">No historical financial records to display.</td></tr>`;
                    return;
                }
                
                data.daily.forEach(d => {
                    const cost = d.turnover - d.gp;
                    const margin = d.turnover > 0 ? ((d.gp / d.turnover) * 100) : 0;
                    tbody.innerHTML += `
                        <tr>
                            <td><strong>${d.day_label}</strong></td>
                            <td style="color:#fff; font-weight:600;">${formatPrice(d.turnover)}</td>
                            <td>${formatPrice(cost)}</td>
                            <td style="color:var(--success); font-weight:700;">${formatPrice(d.gp)}</td>
                            <td style="font-weight:600; color:var(--primary);">${margin.toFixed(1)}%</td>
                        </tr>
                    `;
                });
                
                // Chart lists
                const months = data.monthly.map(m => m.month_label);
                const turnovers = data.monthly.map(m => m.turnover);
                const gps = data.monthly.map(m => m.gp);
                
                // Render charts
                renderAgentCharts(months, turnovers, gps);
            }
        });
}

function renderAgentCharts(labels, turnovers, gps) {
    if (chartTO) chartTO.destroy();
    if (chartGP) chartGP.destroy();
    
    const ctxTO = document.getElementById("agent-chart-turnover").getContext("2d");
    chartTO = new Chart(ctxTO, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Monthly Turnover (Gross Revenue)',
                data: turnovers,
                backgroundColor: 'rgba(0, 242, 254, 0.4)',
                borderColor: '#00f2fe',
                borderWidth: 2,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
            },
            plugins: { legend: { labels: { color: '#f1f5f9' } } }
        }
    });

    const ctxGP = document.getElementById("agent-chart-gp").getContext("2d");
    chartGP = new Chart(ctxGP, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Monthly Gross Profit (Agency Markup)',
                data: gps,
                borderColor: '#2ecc71',
                backgroundColor: 'rgba(46, 204, 113, 0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
            },
            plugins: { legend: { labels: { color: '#f1f5f9' } } }
        }
    });
}


// =========================================================================
// ATL ADMIN CLIENT SIDE LOGIC
// =========================================================================

function switchAdminTab(tabId) {
    // Deactivate current tabs
    document.querySelectorAll(".menu-item").forEach(item => item.classList.remove("active"));
    document.querySelectorAll(".tab-content-panel").forEach(panel => panel.classList.remove("active"));
    
    // Activate target
    event.currentTarget.classList.add("active");
    document.getElementById(`tab-${tabId}`).classList.add("active");
    
    // Load fresh data if needed
    if (tabId === "dashboard") {
        updateAdminUI();
    } else if (tabId === "agents") {
        loadAdminAgents();
    } else if (tabId === "fees") {
        loadAdminFees();
    } else if (tabId === "reports") {
        loadAdminReports();
    } else if (tabId === "tickets") {
        loadAdminTickets();
    }
}

// Refresh admin cumulative stats
let adminSegmentChart = null;

function updateAdminUI() {
    fetch("/api/admin/stats")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                document.getElementById("admin-total-turnover").innerText = `$${data.total_turnover.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                document.getElementById("admin-total-gp").innerText = `$${data.total_gp.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                document.getElementById("admin-total-agents").innerText = data.total_agents;
                document.getElementById("admin-open-tickets").innerText = data.open_tickets;
                
                // Seed top performing agents
                const tbody = document.getElementById("admin-top-agents-table");
                tbody.innerHTML = "";
                
                data.top_agents.forEach(ag => {
                    tbody.innerHTML += `
                        <tr>
                            <td><strong style="color:#fff;">${ag.username}</strong></td>
                            <td>${ag.company_name}</td>
                            <td style="color:var(--success);">$${ag.credit_balance.toFixed(2)}</td>
                            <td style="color:var(--primary); font-weight:700;">$${ag.turnover.toFixed(2)}</td>
                        </tr>
                    `;
                });
                
                // Render circular doughnut GDS counts share
                const segments = data.gds_segments.map(s => s.segments);
                const gdsTypes = data.gds_segments.map(s => s.gds_type);
                renderAdminSegmentsDoughnut(gdsTypes, segments);
            }
        });
}

function renderAdminSegmentsDoughnut(labels, data) {
    if (adminSegmentChart) adminSegmentChart.destroy();
    
    const ctx = document.getElementById("admin-segment-chart").getContext("2d");
    adminSegmentChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: ['#00f2fe', '#4facfe', '#a259ff', '#f857a6'],
                borderColor: '#0f1624',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'right', labels: { color: '#94a3b8', boxWidth: 12 } }
            }
        }
    });
}

// Load agents list in Manage panel
function loadAdminAgents() {
    fetch("/api/admin/agents/list")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const tbody = document.getElementById("admin-agents-table");
                tbody.innerHTML = "";
                
                // Also populate Agent Filter dropdown in Admin Reports
                const selectFilter = document.getElementById("reports-agent-filter");
                if (selectFilter) {
                    selectFilter.innerHTML = `<option value="all">All Agents Consolidated</option>`;
                }
                
                data.agents.forEach(ag => {
                    tbody.innerHTML += `
                        <tr>
                            <td><strong style="color:#fff;">${ag.username}</strong><br><span style="font-size:11px; color:var(--text-muted);">${ag.email}</span></td>
                            <td>${ag.company_name}<br><span style="font-size:11px; color:var(--text-muted);">${ag.phone}</span></td>
                            <td style="color:var(--success); font-weight:700;">$${ag.credit_balance.toFixed(2)}</td>
                            <td>${ag.onboarded_at.split('T')[0]}</td>
                            <td>
                                <button class="btn-action" onclick="openAdjustCreditModal(${ag.id}, '${ag.company_name}', ${ag.credit_balance})">
                                    <i class="fa-solid fa-pen-to-square"></i> Adjust Credit
                                </button>
                            </td>
                        </tr>
                    `;
                    
                    if (selectFilter) {
                        selectFilter.innerHTML += `<option value="${ag.id}">${ag.company_name} (${ag.username})</option>`;
                    }
                });
            }
        });
}

// Onboard Registration Agent
function submitOnboardAgent() {
    const username = document.getElementById("onboard-username").value.trim();
    const password = document.getElementById("onboard-password").value.trim();
    const email = document.getElementById("onboard-email").value.trim();
    const company = document.getElementById("onboard-company").value.trim();
    const phone = document.getElementById("onboard-phone").value.trim();
    const credit = document.getElementById("onboard-credit").value;
    
    if (!username || !password || !email || !company) {
        showNotification("Required Fields", "Please complete all mandatory credentials to onboard.", "danger");
        return;
    }
    
    fetch("/api/admin/agents/onboard", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            username: username,
            password: password,
            email: email,
            company_name: company,
            phone: phone,
            credit_balance: parseFloat(credit) || 0.0
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showNotification("Agent Registered", data.message, "success");
            // Clear inputs
            document.getElementById("onboard-username").value = "";
            document.getElementById("onboard-email").value = "";
            document.getElementById("onboard-company").value = "";
            document.getElementById("onboard-phone").value = "";
            document.getElementById("onboard-credit").value = "5000";
            loadAdminAgents();
        } else {
            showNotification("Onboarding Denied", data.error, "danger");
        }
    });
}

// Adjust Agent Credit manual loader modal
function openAdjustCreditModal(agentId, name, balance) {
    document.getElementById("adjust-credit-agent-id").value = agentId;
    document.getElementById("adjust-credit-agent-name").innerText = name;
    document.getElementById("adjust-credit-agent-current").innerText = `$${balance.toFixed(2)}`;
    document.getElementById("adjust-credit-amount").value = "";
    document.getElementById("adjust-credit-reason").value = "";
    openModal("adjust-credit-modal");
}

function submitAdjustCredit() {
    const agentId = document.getElementById("adjust-credit-agent-id").value;
    const amount = document.getElementById("adjust-credit-amount").value;
    const reason = document.getElementById("adjust-credit-reason").value.trim();
    
    if (!amount || parseFloat(amount) === 0) {
        showNotification("Invalid Value", "Please enter a valid credit offset (positive/negative).", "danger");
        return;
    }
    
    fetch("/api/admin/agents/update-credit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            agent_id: parseInt(agentId),
            amount: parseFloat(amount),
            description: reason
        })
    })
    .then(res => res.json())
    .then(data => {
        closeModal("adjust-credit-modal");
        if (data.success) {
            showNotification("Wallet Adjusted", data.message, "success");
            loadAdminAgents();
            updateAdminUI();
        } else {
            showNotification("Adjustment Failed", data.error, "danger");
        }
    });
}

// Load Fee Configuration list
function loadAdminFees() {
    fetch("/api/admin/fees/list")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const tbody = document.getElementById("admin-fees-table");
                tbody.innerHTML = "";
                
                data.fees.forEach(f => {
                    tbody.innerHTML += `
                        <tr>
                            <td><strong style="text-transform:uppercase; color:#fff;">${f.transaction_type}</strong></td>
                            <td><span class="badge badge-ticketed">${f.fee_type}</span></td>
                            <td>
                                <input type="number" id="fee-amt-${f.id}" class="form-control" style="width: 130px;" value="${f.amount.toFixed(2)}" min="0">
                            </td>
                            <td>
                                <button class="btn-action" onclick="updateAdminFee(${f.id})">
                                    <i class="fa-solid fa-floppy-disk"></i> Save Rate
                                </button>
                            </td>
                        </tr>
                    `;
                });
            }
        });
}

function updateAdminFee(id) {
    const val = document.getElementById(`fee-amt-${id}`).value;
    if (!val || parseFloat(val) < 0) {
        showNotification("Invalid Entry", "Markup rate cannot be negative.", "danger");
        return;
    }
    
    fetch("/api/admin/fees/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: id, amount: parseFloat(val) })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showNotification("Markup Rate Applied", data.message, "success");
            loadAdminFees();
        } else {
            showNotification("Update Failed", data.error, "danger");
        }
    });
}

// Broadcast pop-up advisories
function submitBroadcastNotice() {
    const msg = document.getElementById("broadcast-message").value.trim();
    if (!msg) {
        showNotification("Notice Blank", "Type standard alert before broadcasting.", "danger");
        return;
    }
    
    fetch("/api/admin/popups/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message_text: msg })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showNotification("Notice Broadcasted!", data.message, "success");
            document.getElementById("broadcast-message").value = "";
        } else {
            showNotification("Failed to Broadcast", data.error, "danger");
        }
    });
}

// Load admin reports
let chartAdminTO = null;
let chartAdminGP = null;

function loadAdminReports() {
    const filterVal = document.getElementById("reports-agent-filter").value;
    
    fetch(`/api/reports/togp?agent_id=${filterVal}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // Populate Airline splits
                const airlineBody = document.getElementById("reports-airline-table");
                airlineBody.innerHTML = "";
                if (data.airline.length === 0) {
                    airlineBody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted);">No flight bookings matching.</td></tr>`;
                } else {
                    data.airline.forEach(a => {
                        airlineBody.innerHTML += `
                            <tr>
                                <td><strong>${a.airline}</strong></td>
                                <td>${a.tickets_issued}</td>
                                <td>$${a.turnover.toFixed(2)}</td>
                                <td style="color:var(--success); font-weight:600;">$${a.gp.toFixed(2)}</td>
                            </tr>
                        `;
                    });
                }
                
                // Populate Destination splits
                const destBody = document.getElementById("reports-dest-table");
                destBody.innerHTML = "";
                if (data.destination.length === 0) {
                    destBody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted);">No hotel/flight bookings matching.</td></tr>`;
                } else {
                    data.destination.forEach(d => {
                        destBody.innerHTML += `
                            <tr>
                                <td><strong>${d.destination}</strong></td>
                                <td>${d.booking_count}</td>
                                <td>$${d.turnover.toFixed(2)}</td>
                                <td style="color:var(--success); font-weight:600;">$${d.gp.toFixed(2)}</td>
                            </tr>
                        `;
                    });
                }
                
                // Render Charts
                const labels = data.monthly.map(m => m.month_label);
                const turnovers = data.monthly.map(m => m.turnover);
                const gps = data.monthly.map(m => m.gp);
                renderAdminCharts(labels, turnovers, gps);
            }
        });
}

function renderAdminCharts(labels, turnovers, gps) {
    if (chartAdminTO) chartAdminTO.destroy();
    if (chartAdminGP) chartAdminGP.destroy();
    
    const ctxTO = document.getElementById("admin-chart-turnover").getContext("2d");
    chartAdminTO = new Chart(ctxTO, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Turnover (Cumulative Sales Revenue)',
                data: turnovers,
                backgroundColor: 'rgba(79, 172, 254, 0.4)',
                borderColor: '#4facfe',
                borderWidth: 2,
                borderRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
            },
            plugins: { legend: { labels: { color: '#f1f5f9' } } }
        }
    });

    const ctxGP = document.getElementById("admin-chart-gp").getContext("2d");
    chartAdminGP = new Chart(ctxGP, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Cumulative Gross Profit (Net Markup)',
                data: gps,
                borderColor: '#f857a6',
                backgroundColor: 'rgba(248, 87, 166, 0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
                x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
            },
            plugins: { legend: { labels: { color: '#f1f5f9' } } }
        }
    });
}

// Load tickets supports queue
function loadAdminTickets() {
    fetch("/api/support/list")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const tbody = document.getElementById("admin-tickets-table");
                tbody.innerHTML = "";
                
                if (data.tickets.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted); padding:30px 0;">No B2B helpdesk tickets open.</td></tr>`;
                    return;
                }
                
                data.tickets.forEach(t => {
                    const statusClass = t.status === 'open' ? 'badge-reservation' : 'badge-ticketed';
                    let actionHTML = "";
                    if (t.status === 'open') {
                        actionHTML = `
                            <button class="btn-action btn-ticket" onclick="resolveAdminTicket(${t.id})">
                                <i class="fa-solid fa-check"></i> Resolve
                            </button>
                        `;
                    } else {
                        actionHTML = `<span style="color:var(--text-muted); font-size:12px;">No Actions</span>`;
                    }
                    
                    tbody.innerHTML += `
                        <tr>
                            <td>${t.created_at.split('T')[0]}</td>
                            <td><strong>${t.username}</strong><br><span style="font-size:11px; color:var(--text-muted);">${t.company_name}</span></td>
                            <td><strong>${t.subject}</strong></td>
                            <td style="font-size:12.5px; color:var(--text-muted); max-width:300px;">${t.message}</td>
                            <td><span class="badge ${statusClass}">${t.status}</span></td>
                            <td>${actionHTML}</td>
                        </tr>
                    `;
                });
            }
        });
}

function resolveAdminTicket(id) {
    fetch("/api/admin/support/resolve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ticket_id: id })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showNotification("Ticket Resolved", data.message, "success");
            loadAdminTickets();
            updateAdminUI();
        } else {
            showNotification("Resolution Failed", data.error, "danger");
        }
    });
}

// Open payment selection modal
function openPaymentOptionsModal() {
    // Reset active visual cards in selection modal
    const creditOpt = document.getElementById("pay-opt-credit");
    const gatewayOpt = document.getElementById("pay-opt-gateway");
    if (creditOpt) creditOpt.classList.remove("active");
    if (gatewayOpt) gatewayOpt.classList.remove("active");
    
    // Populate credit balance and deduct amount
    const topbarCredit = document.getElementById("topbar-credit");
    const summaryFare = document.getElementById("summary-total-fare");
    
    const availBalanceEl = document.getElementById("modal-opt-avail-balance");
    if (availBalanceEl) availBalanceEl.innerText = topbarCredit ? topbarCredit.innerText : "$0.00";
    
    const deductAmountEl = document.getElementById("modal-opt-deduct-amount");
    if (deductAmountEl) deductAmountEl.innerText = summaryFare ? summaryFare.innerText : "$0.00";
    
    openModal("payment-options-modal");
}

// Handles selecting payment options (Credit Balance vs Payment Gateway)
function selectPaymentMethod(method) {
    // Visually toggle active class briefly
    const creditOpt = document.getElementById("pay-opt-credit");
    const gatewayOpt = document.getElementById("pay-opt-gateway");
    if (method === "credit" && creditOpt) {
        creditOpt.classList.add("active");
        if (gatewayOpt) gatewayOpt.classList.remove("active");
    } else if (method === "gateway" && gatewayOpt) {
        gatewayOpt.classList.add("active");
        if (creditOpt) creditOpt.classList.remove("active");
    }
    
    setTimeout(() => {
        closeModal("payment-options-modal");
        
        if (method === "credit") {
            // Proceed directly with credit balance
            processFlightBooking(activeBookingPath === "ticket", "credit");
        } else if (method === "gateway") {
            // Fetch total fare from step 3 summary
            const fareText = document.getElementById("summary-total-fare").innerText;
            document.getElementById("gateway-payable-amount").innerText = fareText;
            
            // Reset card form fields
            const form = document.getElementById("gateway-payment-form");
            if (form) form.reset();
            
            // Open secure gateway modal
            openModal("payment-gateway-modal");
        }
    }, 200);
}

// Auto formats credit card input with space delimiters: "0000 0000 0000 0000"
function formatCardNumber(input) {
    let value = input.value.replace(/\s+/g, "").replace(/[^0-9]/gi, "");
    let matches = value.match(/\d{4,16}/g);
    let match = (matches && matches[0]) || "";
    let parts = [];

    for (let i = 0, len = match.length; i < len; i += 4) {
        parts.push(match.substring(i, i + 4));
    }

    if (parts.length > 0) {
        input.value = parts.join(" ");
    } else {
        input.value = value;
    }
}

// Auto formats Expiry Date input to: "MM/YY"
function formatCardExpiry(input) {
    let value = input.value.replace(/\s+/g, "").replace(/[^0-9]/gi, "");
    if (value.length >= 2) {
        input.value = value.substring(0, 2) + "/" + value.substring(2, 4);
    } else {
        input.value = value;
    }
}

// Validates card details and executes checkout API call
function submitGatewayPayment(event) {
    event.preventDefault();
    
    const bankName = document.getElementById("gateway-bank-name").value.trim();
    const cardholder = document.getElementById("gateway-cardholder").value.trim();
    const cardnumber = document.getElementById("gateway-cardnumber").value.replace(/\s+/g, "");
    const expiry = document.getElementById("gateway-expiry").value.trim();
    const cvv = document.getElementById("gateway-cvv").value.trim();
    
    // Validations
    if (!bankName || !cardholder || !cardnumber || !expiry || !cvv) {
        showNotification("Validation Failed", "Please fill in all payment details.", "danger");
        return;
    }
    
    if (cardnumber.length < 15 || cardnumber.length > 16) {
        showNotification("Invalid Card Number", "Card number must be 15 or 16 digits long.", "danger");
        return;
    }
    
    const expiryRegex = /^(0[1-9]|1[0-2])\/?([0-9]{2})$/;
    if (!expiryRegex.test(expiry)) {
        showNotification("Invalid Expiry Format", "Expiry date must be in MM/YY format.", "danger");
        return;
    }
    
    if (cvv.length !== 3) {
        showNotification("Invalid CVV", "CVV code must be 3 digits long.", "danger");
        return;
    }
    
    // Simulate premium visual authorization delay
    showNotification("Authorizing Payment", "Communicating securely with the bank gateway...", "info");
    
    setTimeout(() => {
        closeModal("payment-gateway-modal");
        processFlightBooking(activeBookingPath === "ticket", "gateway");
    }, 1500);
}

// Passenger Popover Controller
function togglePassengerPopover() {
    const popover = document.getElementById('passenger-popover');
    if (!popover) return;
    if (popover.style.display === 'none') {
        popover.style.display = 'block';
    } else {
        popover.style.display = 'none';
    }
}

// Close popover when clicking outside
document.addEventListener('click', function(e) {
    const selector = document.querySelector('.passenger-selector');
    const popover = document.getElementById('passenger-popover');
    if (selector && popover && popover.style.display === 'block') {
        if (!selector.contains(e.target)) {
            popover.style.display = 'none';
        }
    }
});

function updatePax(type, delta) {
    const input = document.getElementById(`flight-${type}`);
    const display = document.getElementById(`${type === 'adults' ? 'adult' : type === 'children' ? 'child' : 'infant'}-count-display`);
    if (!input || !display) return;
    
    let val = parseInt(input.value);
    val += delta;
    
    if (type === 'adults' && val < 1) val = 1;
    if (type === 'children' && val < 0) val = 0;
    if (type === 'infants' && val < 0) val = 0;
    
    // Infant restriction
    if (type === 'infants') {
        const adultCount = parseInt(document.getElementById('flight-adults').value);
        if (val > adultCount) {
            val = adultCount;
        }
    }
    
    input.value = val;
    display.innerText = val;
    
    updatePassengerSummary();
}
// Hotel Passenger Popover Controller
function toggleHotelPassengerPopover() {
    const popover = document.getElementById('hotel-passenger-popover');
    if (!popover) return;
    if (popover.style.display === 'none') {
        popover.style.display = 'block';
    } else {
        popover.style.display = 'none';
    }
}

// Close hotel popover when clicking outside
document.addEventListener('click', function(e) {
    const popover = document.getElementById('hotel-passenger-popover');
    if (popover && popover.style.display === 'block') {
        const btn = document.getElementById('hotel-passenger-dropdown-btn');
        if (!popover.contains(e.target) && !btn.contains(e.target)) {
            popover.style.display = 'none';
        }
    }
});

function updateHotelPax(type, delta) {
    const input = document.getElementById(`hotel-${type}`);
    const display = document.getElementById(`hotel-${type === 'adults' ? 'adult' : 'child'}-count-display`);
    if (!input || !display) return;
    
    let val = parseInt(input.value);
    val += delta;
    
    if (type === 'adults' && val < 1) val = 1;
    if (type === 'children' && val < 0) val = 0;
    
    input.value = val;
    display.innerText = val;
    
    updateHotelPassengerSummary();
}

function updateHotelPassengerSummary() {
    const adults = parseInt(document.getElementById('hotel-adults').value);
    const children = parseInt(document.getElementById('hotel-children').value);
    
    const total = adults + children;
    const summary = document.getElementById('hotel-passenger-summary-text');
    
    if (!summary) return;
    
    if (children === 0) {
        summary.innerText = `${adults} Adult${adults > 1 ? 's' : ''}`;
    } else {
        summary.innerText = `${total} Guest${total > 1 ? 's' : ''}`;
    }
}
function updatePassengerSummary() {
    const adults = parseInt(document.getElementById('flight-adults').value);
    const children = parseInt(document.getElementById('flight-children').value);
    const infants = parseInt(document.getElementById('flight-infants').value);
    
    const total = adults + children + infants;
    const summary = document.getElementById('passenger-summary-text');
    
    if (!summary) return;
    
    if (children === 0 && infants === 0) {
        summary.innerText = `${adults} Adult${adults > 1 ? 's' : ''}`;
    } else {
        summary.innerText = `${total} Traveler${total > 1 ? 's' : ''}`;
    }
}
