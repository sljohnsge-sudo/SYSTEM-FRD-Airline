// Global app state & UI handlers

document.addEventListener("DOMContentLoaded", function () {
    // Detect role and initialize appropriate components
    if (document.getElementById("topbar-credit")) {
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
    }
}

// Refresh Agent Credit & Stats
function updateAgentUI() {
    fetch("/api/agent/info")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const creditStr = `$${data.agent.credit_balance.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                document.getElementById("topbar-credit").innerText = creditStr;
                document.getElementById("dashboard-reward-points").innerText = `${data.agent.reward_points} PTS`;
                
                // If on zero-credit agent page, show insufficient warning toast once
                if (data.agent.credit_balance <= 0 && data.agent.username === "zero_agent") {
                    showNotification("Insufficient Credit Warning", "Your agency credit balance is $0.00. Please top up before ticketing flights or booking hotels.", "warning");
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
                            <td>${f.airline}</td>
                            <td><span class="badge-type">${f.flight_type}</span></td>
                            <td style="color:var(--primary); font-weight:700;">$${f.lowest_fare.toFixed(2)}</td>
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

// Flight Search Logic
function searchFlights() {
    const origin = document.getElementById("flight-origin").value;
    const dest = document.getElementById("flight-dest").value;
    const type = document.getElementById("flight-channel").value;
    const date = document.getElementById("flight-date") ? document.getElementById("flight-date").value : "";
    
    const container = document.getElementById("flight-results-container");
    container.innerHTML = `<div style="text-align:center; padding:40px;"><i class="fa-solid fa-circle-notch fa-spin" style="font-size:32px; color:var(--primary);"></i><p style="margin-top:10px;">Interrogating GDS, LCC and NDC API databases...</p></div>`;
    
    fetch(`/api/flights/search?origin=${origin}&destination=${dest}&flight_type=${type}&date=${date}`)
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                container.innerHTML = "";
                
                if (data.flights.length === 0) {
                    container.innerHTML = `
                        <div style="text-align: center; color: var(--text-muted); padding: 40px 0;">
                            <i class="fa-solid fa-triangle-exclamation" style="font-size: 32px; margin-bottom: 15px; color: var(--warning);"></i>
                            <p>No flights matching the routing found. Try CMB to MLE, DOH to LHR, or CMB to SIN.</p>
                        </div>
                    `;
                    return;
                }
                
                data.flights.forEach(f => {
                    const depDate = new Date(f.departure_time);
                    const arrDate = new Date(f.arrival_time);
                    const hours = Math.abs(arrDate - depDate) / 36e5;
                    const durationStr = `${Math.floor(hours)}h ${Math.round((hours % 1) * 60)}m`;
                    
                    container.innerHTML += `
                        <div class="flight-ticket-card">
                            <div class="airline-info">
                                <div class="airline-logo-placeholder"><i class="fa-solid fa-plane"></i></div>
                                <div>
                                    <div class="airline-name">${f.airline}</div>
                                    <div class="flight-number">${f.flight_number} • <span class="badge-type">${f.flight_type}</span></div>
                                </div>
                            </div>
                            
                            <div class="flight-route-flow">
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
                            
                            <div class="flight-fare-booking">
                                <div class="flight-fare-value">$${(f.price + 15.00).toFixed(2)}</div>
                                <div style="font-size: 10px; color: var(--text-muted); margin-bottom: 8px;">Includes $15.00 agency markup</div>
                                <button class="btn-book-action" onclick="openFlightBookModal(${f.id}, '${f.flight_number}', '${f.airline}', ${(f.price + 15.00).toFixed(2)})">
                                    <i class="fa-solid fa-circle-check"></i> Book Seat
                                </button>
                            </div>
                        </div>
                    `;
                });
            }
        });
}

// Open booking details modal & Generate Seat Selection Grid
let selectedSeat = null;

function openFlightBookModal(flightId, flNum, airline, totalAmt) {
    document.getElementById("modal-flight-id").value = flightId;
    document.getElementById("flight-modal-title").innerText = `Book Flight ${flNum} - ${airline} ($${totalAmt})`;
    document.getElementById("modal-passenger-name").value = "";
    
    // Select seat map container
    const seatMap = document.getElementById("modal-seat-map");
    seatMap.innerHTML = "";
    selectedSeat = null;
    document.getElementById("modal-selected-seat-text").innerText = "None";
    
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
                        document.getElementById("modal-selected-seat-text").innerText = seatName;
                    };
                }
            }
            rowDiv.appendChild(seat);
        });
        seatMap.appendChild(rowDiv);
    }
    
    openModal("flight-book-modal");
}

// Process booking flight
function processFlightBooking(ticketNow) {
    const flightId = document.getElementById("modal-flight-id").value;
    const passengerName = document.getElementById("modal-passenger-name").value.trim();
    
    if (!passengerName) {
        showNotification("Missing Passenger", "Please enter the passenger legal name to proceed.", "danger");
        return;
    }
    if (!selectedSeat) {
        showNotification("Missing Seat Selection", "Please select a seat from the interactive seat map.", "danger");
        return;
    }
    
    fetch("/api/flights/book", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            flight_id: parseInt(flightId),
            passenger_name: passengerName,
            seat_number: selectedSeat,
            ticket_now: ticketNow
        })
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
                container.innerHTML = "";
                
                if (data.hotels.length === 0) {
                    container.innerHTML = `
                        <div style="text-align: center; color: var(--text-muted); padding: 40px 0; grid-column: span 3;">
                            <i class="fa-solid fa-triangle-exclamation" style="font-size: 32px; margin-bottom: 15px; color: var(--warning);"></i>
                            <p>No hotels found in the selected location. Try 'London', 'Dubai' or 'Maldives'.</p>
                        </div>
                    `;
                    return;
                }
                
                data.hotels.forEach(h => {
                    let starIcons = "";
                    for(let i=0; i<h.rating; i++) starIcons += `<i class="fa-solid fa-star"></i>`;
                    
                    let roomsList = "";
                    if (h.rooms.length === 0) {
                        roomsList = `<p style="color:var(--danger); font-size:11.5px;">All rooms occupied for these dates</p>`;
                    } else {
                        h.rooms.forEach(r => {
                            roomsList += `
                                <div class="room-type-item">
                                    <span>${r.room_type}</span>
                                    <div style="display:flex; align-items:center; gap:10px;">
                                        <span class="room-price">$${(r.price_per_night + 25.00).toFixed(2)}/n</span>
                                        <button class="btn-book-action" style="padding:4px 8px; font-size:11px;" onclick="bookHotelRoom(${r.id}, '${r.room_type}', '${h.name}', ${(r.price_per_night + 25.00).toFixed(2)})">
                                            Book
                                        </button>
                                    </div>
                                </div>
                            `;
                        });
                    }
                    
                    container.innerHTML += `
                        <div class="hotel-card">
                            <div class="hotel-image">
                                <i class="fa-solid fa-hotel"></i>
                                <span class="hotel-stars">${starIcons}</span>
                            </div>
                            <div class="hotel-body">
                                <div class="hotel-name">${h.name}</div>
                                <div class="hotel-location"><i class="fa-solid fa-location-dot" style="color:var(--primary);"></i> ${h.location}</div>
                                <p class="hotel-desc">${h.description}</p>
                                <div class="hotel-rooms-list">
                                    <h5 style="font-size:12px; font-weight:600; color:var(--text-muted); margin-bottom:8px; text-transform:uppercase;">Room Selection:</h5>
                                    ${roomsList}
                                </div>
                            </div>
                        </div>
                    `;
                });
            }
        });
}

// Book hotel room (Instant execution)
function bookHotelRoom(roomId, roomType, hotelName, totalRate) {
    const guestName = prompt(`Enter Guest Full Name for room booking at ${hotelName}:`);
    if (!guestName) return;
    
    const checkin = document.getElementById("hotel-checkin").value;
    const checkout = document.getElementById("hotel-checkout").value;
    
    fetch("/api/hotels/book", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            room_id: roomId,
            guest_name: guestName,
            check_in: checkin,
            check_out: checkout
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showNotification("Hotel Booked!", data.message, "success");
            updateAgentUI();
            switchTab("bookings");
        } else {
            showNotification("Booking Failed", data.error, "danger");
        }
    });
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
                        detailsHTML = `
                            <strong>Flight ${d.flight_number}</strong> (${d.gds_type})<br>
                            ${d.origin} <i class="fa-solid fa-plane" style="font-size:10px; color:var(--primary);"></i> ${d.destination}<br>
                            Seat: ${d.seat_number}
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
                            <td style="font-weight:700; color:var(--primary);">$${b.total_price.toFixed(2)}</td>
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
            const message = `Net Credit Refunded: $${d.net_refund_credited.toFixed(2)}. GDS penalty: $${d.amadeus_cancellation_penalty.toFixed(2)}. Agency refund fee: $${d.refund_service_markup.toFixed(2)}.`;
            alert("TRF REFUND PROCESSED BY FLIGHT HUB:\n\n" + message);
            showNotification("TRF Refund Processed", "Net refund balance credited to wallet.", "success");
            updateAgentUI();
            loadBookings();
        } else {
            showNotification("Refund Failed", data.error, "danger");
        }
    });
}

// Re-issue Simulated GDS ATC
let currentReissueOriginalFare = 0;

function openReissueModal(bookingId, currentFlightId, originalFare) {
    document.getElementById("reissue-booking-id").value = bookingId;
    currentReissueOriginalFare = originalFare;
    document.getElementById("reissue-old-fare").innerText = `$${originalFare.toFixed(2)}`;
    
    // Fetch all active flights to populate re-issue options
    fetch("/api/flights/search")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const select = document.getElementById("reissue-new-flight-id");
                select.innerHTML = "";
                
                data.flights.forEach(f => {
                    if (f.id !== currentFlightId) {
                        select.innerHTML += `<option value="${f.id}" data-price="${f.price}">${f.flight_number} - ${f.airline} (${f.origin} to ${f.destination}) - Base fare: $${f.price.toFixed(2)}</option>`;
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
    
    document.getElementById("reissue-new-fare").innerText = `$${newPrice.toFixed(2)}`;
    
    const fareDiff = Math.max(0, newPrice - currentReissueOriginalFare);
    document.getElementById("reissue-fare-diff").innerText = `$${fareDiff.toFixed(2)}`;
    
    const penalty = 50.00;
    const agencyFee = 25.00;
    const total = fareDiff + penalty + agencyFee;
    
    document.getElementById("reissue-total-cost").innerText = `$${total.toFixed(2)}`;
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
            const message = `Auto Re-issue complete!\nGDS Penalty: $${d.amadeus_penalty.toFixed(2)}\nFare Difference Collected: $${d.fare_difference.toFixed(2)}\nAgency markup: $${d.service_markup.toFixed(2)}\n\nTotal charged: $${d.total_charged.toFixed(2)}`;
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
                            <td style="color:#fff; font-weight:600;">$${d.turnover.toFixed(2)}</td>
                            <td>$${cost.toFixed(2)}</td>
                            <td style="color:var(--success); font-weight:700;">$${d.gp.toFixed(2)}</td>
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
