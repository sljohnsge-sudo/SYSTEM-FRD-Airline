
        window.isModifyingBooking = {% if session.get('modifying_booking_id') %}true{% else %}false{% endif %};
        document.addEventListener("DOMContentLoaded", function() {
            let retPicker = flatpickr("#flight-return-date", {
                dateFormat: "Y-m-d",
                minDate: "today",
                altInput: true,
                altFormat: "F j, Y"
            });
            
            let depPicker = flatpickr("#flight-date", {
                dateFormat: "Y-m-d",
                minDate: "today",
                altInput: true,
                altFormat: "F j, Y",
                onChange: function(selectedDates, dateStr, instance) {
                    // When departure date is selected, optionally set min return date
                    if (selectedDates.length > 0) {
                        retPicker.set('minDate', selectedDates[0]);
                    }
                    
                    // If round-trip is selected, automatically open the return date picker
                    const isRoundTrip = document.getElementById('pill-roundtrip') && document.getElementById('pill-roundtrip').classList.contains('active');
                    if (isRoundTrip) {
                        setTimeout(() => {
                            if (retPicker) retPicker.open();
                        }, 150);
                    }
                }
            });

            // Automatically open departure date picker when destination is changed/selected
            const destInput = document.getElementById('flight-dest');
            if (destInput) {
                destInput.addEventListener('change', function() {
                    if (this.value.trim() !== '') {
                        setTimeout(() => {
                            if (depPicker) depPicker.open();
                        }, 150);
                    }
                });
            }

            // Initialize Hotel Date Range Picker
            hotelDatePicker = flatpickr("#b2c-hotel-dates", {
                mode: "range",
                dateFormat: "Y-m-d",
                minDate: "today",
                altInput: true,
                altFormat: "M j, Y",
                defaultDate: [new Date(), new Date(Date.now() + 3 * 24 * 60 * 60 * 1000)] // 3 nights default
            });

            // Handle URL tab parameter on load
            const urlParams = new URLSearchParams(window.location.search);
            const tabParam = urlParams.get('tab');
            if (tabParam === 'hotels') {
                switchB2CTab('hotels');
            }
        });

        // B2C Hotels Tab Switching
        function switchB2CTab(tabName, event) {
            if (event) event.preventDefault();
            
            const btnFlights = document.getElementById("b2c-tab-btn-flights");
            const btnHotels = document.getElementById("b2c-tab-btn-hotels");
            const panelFlights = document.getElementById("b2c-flights-panel");
            const panelHotels = document.getElementById("b2c-hotels-panel");
            
            if (tabName === 'flights') {
                btnFlights.classList.add("active");
                btnHotels.classList.remove("active");
                btnFlights.style.borderBottomColor = "#c3122e";
                btnFlights.style.color = "#c3122e";
                btnFlights.style.fontWeight = "700";
                
                btnHotels.style.borderBottomColor = "transparent";
                btnHotels.style.color = "#64748b";
                btnHotels.style.fontWeight = "600";
                
                panelFlights.style.display = "block";
                panelHotels.style.display = "none";
            } else {
                btnHotels.classList.add("active");
                btnFlights.classList.remove("active");
                btnHotels.style.borderBottomColor = "#c3122e";
                btnHotels.style.color = "#c3122e";
                btnHotels.style.fontWeight = "700";
                
                btnFlights.style.borderBottomColor = "transparent";
                btnFlights.style.color = "#64748b";
                btnFlights.style.fontWeight = "600";
                
                panelFlights.style.display = "none";
                panelHotels.style.display = "block";
            }
        }

        // B2C Hotels Guest Dropdown popover controls
        let hotelRooms = 1;
        let hotelAdults = 2;
        let hotelChildren = 0;
        
        function toggleHotelGuestsPopover() {
            const popover = document.getElementById("b2c-hotel-guests-popover");
            popover.style.display = popover.style.display === "none" ? "block" : "none";
        }
        
        function updateHotelGuests(type, change) {
            if (type === 'rooms') {
                hotelRooms += change;
                if (hotelRooms < 1) hotelRooms = 1;
                if (hotelRooms > 4) hotelRooms = 4;
                document.getElementById("b2c-hotel-rooms-display").innerText = hotelRooms;
            } else if (type === 'adults') {
                hotelAdults += change;
                if (hotelAdults < 1) hotelAdults = 1;
                if (hotelAdults > 10) hotelAdults = 10;
                document.getElementById("b2c-hotel-adults-display").innerText = hotelAdults;
            } else if (type === 'children') {
                hotelChildren += change;
                if (hotelChildren < 0) hotelChildren = 0;
                if (hotelChildren > 6) hotelChildren = 6;
                document.getElementById("b2c-hotel-children-display").innerText = hotelChildren;
            }
            
            // Update summary
            document.getElementById("b2c-hotel-guests-summary").innerHTML = 
                `${hotelAdults} adult${hotelAdults > 1 ? 's' : ''} &middot; ${hotelChildren} child${hotelChildren !== 1 ? 'ren' : ''} &middot; ${hotelRooms} room${hotelRooms > 1 ? 's' : ''}`;
        }

        document.addEventListener("click", function(event) {
            const popover = document.getElementById("b2c-hotel-guests-popover");
            const btn = document.getElementById("b2c-hotel-guests-btn");
            if (popover && btn && !btn.contains(event.target) && !popover.contains(event.target)) {
                popover.style.display = "none";
            }
        });

        // Search B2C Hotels calling GDS
        let hotelDatePicker = null;
        let lastB2CSearchedHotels = [];

        function searchB2CHotels() {
            const location = document.getElementById("b2c-hotel-location").value.trim();
            const container = document.getElementById("b2c-hotel-results-container");
            
            if (!location) {
                alert("Please enter a destination to search.");
                return;
            }
            
            container.innerHTML = `
                <div style="text-align: center; color: #64748b; padding: 60px 0; grid-column: span 3;">
                    <i class="fa-solid fa-circle-notch fa-spin" style="font-size: 32px; color: #c3122e; margin-bottom: 15px;"></i>
                    <p style="font-size: 16px; font-weight: 600;">Interrogating GDS hotel channels...</p>
                </div>
            `;
            container.style.display = "grid";
            
            // Scroll to results
            container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            
            fetch(`/api/hotels/search?location=${location}`)
                .then(res => res.json())
                .then(data => {
                    if (data.success && data.hotels.length > 0) {
                        lastB2CSearchedHotels = data.hotels;
                        renderB2CHotelResults(data.hotels);
                    } else {
                        container.innerHTML = `
                            <div style="text-align: center; color: #64748b; padding: 60px 0; grid-column: span 3;">
                                <i class="fa-solid fa-triangle-exclamation" style="font-size: 32px; color: #c3122e; margin-bottom: 15px;"></i>
                                <p style="font-size: 16px; font-weight: 600;">No hotels found in "${location}".</p>
                                <p style="font-size: 14px; margin-top: 5px; color: #94a3b8;">Try searching for 'London', 'Dubai' or 'Maldives'.</p>
                            </div>
                        `;
                    }
                })
                .catch(err => {
                    console.error("Hotel search error:", err);
                    container.innerHTML = `
                        <div style="text-align: center; color: #64748b; padding: 60px 0; grid-column: span 3;">
                            <i class="fa-solid fa-triangle-exclamation" style="font-size: 32px; color: #ef4444; margin-bottom: 15px;"></i>
                            <p style="font-size: 16px; font-weight: 600;">An error occurred while connecting to GDS channels.</p>
                        </div>
                    `;
                });
        }

        function renderB2CHotelResults(hotels) {
            window.b2cHotelResults = hotels; // Save globally to avoid string escaping issues
            const container = document.getElementById("b2c-hotel-results");
            container.innerHTML = "";
            
            if (!hotels || hotels.length === 0) {
                container.innerHTML = "<div style='background: white; padding: 40px; text-align: center; border-radius: 12px;'><i class='fa-solid fa-hotel' style='font-size: 40px; color: #cbd5e1; margin-bottom: 15px;'></i><h3 style='margin:0; color:#475569;'>No hotels found</h3><p style='color:#94a3b8;'>Try a different destination or dates.</p></div>";
                return;
            }
            
            hotels.forEach(h => {
                let starIcons = "";
                for (let i = 0; i < h.rating; i++) {
                    starIcons += `<i class="fa-solid fa-star"></i>`;
                }
                
                let checkin = "2026-06-15";
                let checkout = "2026-06-18";
                let nights = 3;
                
                if (typeof hotelDatePicker !== 'undefined' && hotelDatePicker && hotelDatePicker.selectedDates && hotelDatePicker.selectedDates.length === 2) {
                    const pad = (num) => num.toString().padStart(2, '0');
                    const formatDate = (date) => `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
                    checkin = formatDate(hotelDatePicker.selectedDates[0]);
                    checkout = formatDate(hotelDatePicker.selectedDates[1]);
                    const timeDiff = Math.abs(hotelDatePicker.selectedDates[1].getTime() - hotelDatePicker.selectedDates[0].getTime());
                    nights = Math.ceil(timeDiff / (1000 * 3600 * 24));
                    if (nights === 0) nights = 1;
                }
                
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
                    <div class="b2c-hotel-card">
                        <img src="${hotelImage}" class="b2c-hotel-img" alt="${h.name}" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=800';">
                        <div class="b2c-hotel-badge">CONSOLIDATED RATE</div>
                        <div class="b2c-hotel-info" style="display:flex; flex-direction:column;">
                            <div style="flex-grow:1;">
                                <div class="b2c-hotel-rating">${starIcons}</div>
                                <h3 class="b2c-hotel-name">${h.name}</h3>
                                <div class="b2c-hotel-loc"><i class="fa-solid fa-location-dot" style="color:#c3122e;"></i> ${h.location}</div>
                                <p class="b2c-hotel-description">${h.description}</p>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 20px; border-top: 1px solid #f1f5f9; padding-top: 15px;">
                                <div>
                                    <div style="font-size: 12px; color: #64748b; font-weight: 600;">Starting from</div>
                                    <div style="font-size: 22px; font-weight: 800; color: #0f172a;">LKR ${lowestPrice.toLocaleString()}<span style="font-size: 12px; color: #64748b; font-weight: normal;">/night</span></div>
                                </div>
                                <button class="btn-book-room" style="background: #2563eb; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-weight: 700; font-size: 15px; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='#1d4ed8';" onmouseout="this.style.background='#2563eb';" onclick="viewHotelDetails(${h.id}, '${checkin}', '${checkout}', ${nights})">See Availability <i class="fa-solid fa-chevron-right" style="font-size: 12px; margin-left: 5px;"></i></button>
                            </div>
                        </div>
                    </div>
                `;
            });
        }
        
        function viewHotelDetails(hotelId, checkin, checkout, nights) {
            if (!window.b2cHotelResults) return;
            const h = window.b2cHotelResults.find(x => x.id === hotelId);
            if (!h) return;
            
            const roomsDataRaw = encodeURIComponent(JSON.stringify(h.rooms || []));
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
            window.open(`/b2c/hotel-details?${params.toString()}`, '_blank');
        }

function bookB2CHotelRoom(roomId, roomType, hotelName, pricePerNight, nights, roomImg) {
            let checkin = "2026-06-15";
            let checkout = "2026-06-18";
            
            if (typeof hotelDatePicker !== 'undefined' && hotelDatePicker && hotelDatePicker.selectedDates.length === 2) {
                const pad = (num) => num.toString().padStart(2, '0');
                const formatDate = (date) => `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
                checkin = formatDate(hotelDatePicker.selectedDates[0]);
                checkout = formatDate(hotelDatePicker.selectedDates[1]);
            }
            
            const params = new URLSearchParams({
                room_id: roomId,
                room_type: roomType,
                hotel_name: hotelName,
                price_per_night: pricePerNight,
                nights: nights,
                checkin: checkin,
                checkout: checkout,
                room_img: roomImg
            });
            // Open in a new tab/window as requested
            window.open(`/b2c/hotel-booking?${params.toString()}`, '_blank');
        }
        

        
        function submitB2CHotelBooking(event) {
            event.preventDefault();
            
            const roomId = document.getElementById("b2c-modal-room-id").value;
            const guestName = document.getElementById("b2c-modal-guest-name").value.trim();
            const email = document.getElementById("b2c-modal-email").value.trim();
            const mobile = document.getElementById("b2c-modal-mobile").value.trim();
            const checkIn = document.getElementById("b2c-modal-checkin").innerText;
            const checkOut = document.getElementById("b2c-modal-checkout").innerText;
            
            const payload = {
                room_id: parseInt(roomId),
                guest_name: guestName,
                email: email,
                mobile: mobile,
                check_in: checkIn,
                check_out: checkOut
            };
            
            fetch("/api/b2c/hotels/book", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    alert("Hotel booked successfully!\nInvoice: " + data.invoice_number);
                    window.location.href = "/b2c/my-bookings";
                } else {
                    alert("Booking failed: " + data.error);
                }
            })
            .catch(err => {
                console.error("Hotel book error:", err);
                alert("An error occurred. Please try again.");
            });
        }
    