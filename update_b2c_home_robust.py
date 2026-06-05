import urllib.parse
path = r'd:\GS\SYSTEM-FRD-Airline\templates\b2c_home.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

start_idx = content.find('function renderB2CHotelResults(hotels) {')
end_idx = content.find('function bookB2CHotelRoom(', start_idx)

new_func = '''function renderB2CHotelResults(hotels) {
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

'''

new_content = content[:start_idx] + new_func + content[end_idx:]
with open(path, 'w', encoding='utf-8') as f:
    f.write(new_content)
print('b2c_home.html robustified successfully!')
