
        let cachedFlights = [];
        let flightsLoaded = false;
        let currentSort = 'cheapest';
        let activeAirlineFilter = null;
        let activeTimingTab = 'DEPARTURE';

        const CITY_NAME_MAPPING = {
            'CMB': 'Colombo',
            'MEL': 'Melbourne',
            'SIN': 'Singapore',
            'MLE': 'Male (Maldives)',
            'LHR': 'London',
            'JFK': 'New York',
            'DXB': 'Dubai',
            'DOH': 'Doha',
            'DEL': 'Delhi',
            'SYD': 'Sydney'
        };

        function getCityName(code) {
            if (!code) return "";
            return CITY_NAME_MAPPING[code.toUpperCase()] || code;
        }

        function formatDateCompact(dateObj) {
            const day = String(dateObj.getDate()).padStart(2, '0');
            const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            const month = months[dateObj.getMonth()];
            const year = dateObj.getFullYear();
            return `${day}${month}${year}`;
        }

        document.addEventListener('DOMContentLoaded', () => {
            const urlParams = new URLSearchParams(window.location.search);
            const origin = urlParams.get('origin') || 'CMB';
            const dest = urlParams.get('dest') || 'MEL';
            const dateStr = urlParams.get('date') || '2026-05-28';
            const adults = urlParams.get('adults') || '1';
            window.searchAdults = parseInt(adults);
            const returnDateStr = urlParams.get('returnDate') || null;
            
            // Populate Search Summary Card
            document.getElementById('summary-trip-type').innerText = returnDateStr ? 'ROUND-TRIP' : 'ONE-WAY';
            document.getElementById('summary-cities').innerText = `${getCityName(origin)} ⇄ ${getCityName(dest)}`;
            
            const depDate = new Date(dateStr);
            document.getElementById('summary-departure-date').innerText = formatDateCompact(depDate);
            
            const returnDateContainer = document.getElementById('summary-return-date-container');
            if (returnDateStr) {
                const retDate = new Date(returnDateStr);
                document.getElementById('summary-return-date').innerText = formatDateCompact(retDate);
                returnDateContainer.style.display = 'flex';
            } else {
                returnDateContainer.style.display = 'none';
            }
            
            document.getElementById('summary-adults').innerText = adults;
            document.getElementById('summary-children').innerText = '--';
            document.getElementById('summary-infant').innerText = '--';

            fetchFlights(origin, dest, dateStr, returnDateStr);

            // Set timing labels
            switchTimingTab('DEPARTURE');
        });

        function slideCarousel(direction) {
            const inner = document.getElementById('airline-carousel-inner');
            inner.scrollLeft += direction * 250;
        }

        function generateAirlineCarousel(flights) {
            const inner = document.getElementById('airline-carousel-inner');
            inner.innerHTML = '';
            
            // Get unique airlines
            const uniqueAirlines = [...new Set(flights.map(f => f.airline))];
            
            if (uniqueAirlines.length === 0) {
                inner.innerHTML = '<div style="padding: 10px; color: var(--text-muted); font-size: 13px;">No airlines found</div>';
                return;
            }
            
            uniqueAirlines.forEach(airline => {
                const airFlights = flights.filter(f => f.airline === airline);
                const minPrice = Math.min(...airFlights.map(f => parseFloat(f.price) * (window.searchAdults || 1)));
                
                const minDur = Math.min(...airFlights.map(f => {
                    const dur = new Date(f.arrival_time) - new Date(f.departure_time);
                    return dur + (f.return_flight ? (new Date(f.return_flight.arrival_time) - new Date(f.return_flight.departure_time)) : 0);
                }));
                
                const hours = Math.floor(minDur / 36e5);
                const mins = Math.round((minDur % 36e5) / 60000);
                const durStr = `${hours}hr ${String(mins).padStart(2, '0')}min`;
                
                const priceFormatted = "LKR " + Math.round(minPrice).toLocaleString();
                
                const isSelected = activeAirlineFilter === airline;
                
                let logoHtml = `<div class="airline-logo" style="width: 32px; height: 32px; background: #eee; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: var(--primary-blue); font-size: 14px;"><i class="fa-solid fa-plane"></i></div>`;
                if (airline.toLowerCase().includes('etihad')) {
                    logoHtml = `<div class="airline-logo" style="width: 32px; height: 32px; background: #000; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #d4af37; font-weight: bold; font-size: 10px;">EY</div>`;
                } else if (airline.toLowerCase().includes('indigo')) {
                    logoHtml = `<div class="airline-logo" style="width: 32px; height: 32px; background: #003b95; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 10px;">6E</div>`;
                } else if (airline.toLowerCase().includes('malaysia')) {
                    logoHtml = `<div class="airline-logo" style="width: 32px; height: 32px; background: #d71920; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 10px;">MH</div>`;
                } else if (airline.toLowerCase().includes('srilankan')) {
                    logoHtml = `<div class="airline-logo" style="width: 32px; height: 32px; background: #006b54; border-radius: 4px; display: flex; align-items: center; justify-content: center; color: #ffcc00; font-weight: bold; font-size: 10px;">UL</div>`;
                }
                
                inner.innerHTML += `
                    <div class="carousel-tile" onclick="toggleAirlineCarouselFilter('${airline}')" style="display: flex; align-items: center; gap: 12px; padding: 10px 20px; border-right: 1px solid var(--border-color); min-width: 220px; cursor: pointer; border-radius: 6px; background: ${isSelected ? 'rgba(136, 18, 59, 0.08)' : 'white'}; border: ${isSelected ? '1px solid var(--primary-blue)' : '1px solid transparent'}; transition: all 0.2s; box-sizing: border-box; flex-shrink: 0;">
                        ${logoHtml}
                        <div style="text-align: left; line-height: 1.2;">
                            <div style="font-weight: 700; font-size: 11px; color: var(--text-main); text-transform: uppercase;">${airline}</div>
                            <div style="font-size: 11px; color: var(--text-muted); margin-top: 3px;">(${durStr})</div>
                            <div style="font-weight: 700; font-size: 13px; color: var(--success-green); margin-top: 3px;">${priceFormatted}</div>
                        </div>
                    </div>
                `;
            });
        }

        function toggleAirlineCarouselFilter(airline) {
            if (activeAirlineFilter === airline) {
                activeAirlineFilter = null;
            } else {
                activeAirlineFilter = airline;
            }
            generateAirlineCarousel(cachedFlights);
            applyFilters();
        }

        function switchTimingTab(tab) {
            activeTimingTab = tab;
            const depTab = document.getElementById('timing-tab-dep');
            const arrTab = document.getElementById('timing-tab-arr');
            const lblOut = document.getElementById('timing-label-outbound');
            const lblRet = document.getElementById('timing-label-return');
            
            const urlParams = new URLSearchParams(window.location.search);
            const returnDate = urlParams.get('returnDate');
            
            if (tab === 'DEPARTURE') {
                depTab.style.background = '#7b93a4';
                depTab.style.color = 'white';
                arrTab.style.background = 'transparent';
                arrTab.style.color = 'var(--text-main)';
                
                lblOut.innerText = 'OUTBOUND DEPARTURE';
                lblRet.innerText = returnDate ? 'RETURN DEPARTURE' : 'OUTBOUND ARRIVAL';
            } else {
                arrTab.style.background = '#7b93a4';
                arrTab.style.color = 'white';
                depTab.style.background = 'transparent';
                depTab.style.color = 'var(--text-main)';
                
                lblOut.innerText = 'OUTBOUND ARRIVAL';
                lblRet.innerText = returnDate ? 'RETURN ARRIVAL' : 'RETURN ARRIVAL';
            }
            applyFilters();
        }

        function switchSortTab(sortBy) {
            currentSort = sortBy;
            
            // Sidebar sort highlights
            const arCheap = document.getElementById('airline-sort-cheap');
            const arFast = document.getElementById('airline-sort-fast');
            if (arCheap && arFast) {
                if (sortBy === 'cheapest') {
                    arCheap.style.background = '#7b93a4';
                    arCheap.style.color = 'white';
                    arFast.style.background = 'transparent';
                    arFast.style.color = 'var(--text-main)';
                } else if (sortBy === 'fastest') {
                    arFast.style.background = '#7b93a4';
                    arFast.style.color = 'white';
                    arCheap.style.background = 'transparent';
                    arCheap.style.color = 'var(--text-main)';
                }
            }
            
            // Main tabs highlights
            const tabCheap = document.getElementById('sort-tab-cheap');
            const tabQuick = document.getElementById('sort-tab-quick');
            const tabBest = document.getElementById('sort-tab-best');
            
            [tabCheap, tabQuick, tabBest].forEach(t => t.classList.remove('active'));
            
            if (sortBy === 'cheapest') {
                tabCheap.classList.add('active');
            } else if (sortBy === 'fastest') {
                tabQuick.classList.add('active');
            } else if (sortBy === 'best') {
                tabBest.classList.add('active');
            }
            
            applyFilters();
        }

        function fetchFlights(origin, dest, date, returnDate) {
            let url = `/api/flights/search?origin=${encodeURIComponent(origin)}&destination=${encodeURIComponent(dest)}&date=${encodeURIComponent(date)}&flight_type=ALL`;
            if (returnDate) {
                url += `&return_date=${encodeURIComponent(returnDate)}`;
            }
            
            fetch(url)
            .then(res => res.json())
            .then(data => {
                flightsLoaded = true;
                if(data.success && data.flights) {
                    cachedFlights = data.flights;
                    generateAirlineFilters(cachedFlights);
                    
                    // Generate carousel
                    generateAirlineCarousel(cachedFlights);
                    
                    applyFilters();
                } else {
                    document.getElementById('flight-list-container').innerHTML = `<div class="loading-state">Error fetching flights: ${data.message || 'Unknown GDS error'}</div>`;
                }
            })
            .catch(err => {
                flightsLoaded = true;
                document.getElementById('flight-list-container').innerHTML = `<div class="loading-state">Error fetching flights from GDS consolidation servers.</div>`;
            });
        }

        function generateAirlineFilters(flights) {
            const airlinesSet = new Set();
            flights.forEach(f => {
                if (f.airline) airlinesSet.add(f.airline);
                if (f.return_flight && f.return_flight.airline) airlinesSet.add(f.return_flight.airline);
            });
            const airlines = [...airlinesSet];
            const container = document.getElementById('airline-filters-container');
            container.innerHTML = '';
            airlines.forEach(airline => {
                container.innerHTML += `
                    <label class="filter-option" style="display:flex; justify-content:space-between; margin-bottom:8px;">
                        <div><input type="checkbox" checked value="${airline}" class="filter-airline" onchange="applyFilters()"> ${airline}</div>
                    </label>
                `;
            });
        }

        function toggleFilterBtn(el) {
            el.classList.toggle('selected');
            if (el.classList.contains('selected')) {
                el.style.background = 'rgba(136, 18, 59, 0.08)';
                el.style.border = '1px solid var(--primary-blue)';
            } else {
                el.style.background = '#f5f5f5';
                el.style.border = '1px solid transparent';
            }
        }

        function toggleTimingBtn(el) {
            el.classList.toggle('selected');
            if (el.classList.contains('selected')) {
                el.style.background = 'rgba(136, 18, 59, 0.08)';
                el.style.borderBottom = '2px solid var(--primary-blue)';
            } else {
                el.style.background = '#f9f9f9';
                el.style.borderBottom = 'none';
            }
        }

        function resetAllFilters() {
            document.getElementById('filter-price').value = 1000000;
            document.getElementById('price-val-display').innerText = 'LKR 1,000,000';
            
            document.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = true);
            
            document.querySelectorAll('.filter-stop-btn, .filter-conn-btn, .filter-dep-btn, .filter-arr-btn').forEach(btn => {
                if (!btn.classList.contains('selected')) {
                    if (btn.classList.contains('filter-dep-btn') || btn.classList.contains('filter-arr-btn')) {
                        toggleTimingBtn(btn);
                    } else {
                        toggleFilterBtn(btn);
                    }
                }
            });
            
            applyFilters();
        }

        function getLayoverAirport(f) {
            if (f.segment_count <= 1) return null;
            const airline = f.airline.toLowerCase();
            if (airline.includes('etihad') || airline.includes('emirates') || airline.includes('qatar') || airline.includes('flydubai')) {
                return 'AUH';
            }
            if (airline.includes('srilankan') || airline.includes('indigo') || airline.includes('air india') || airline.includes('spicejet')) {
                return 'MAA';
            }
            if (airline.includes('thai') || airline.includes('bangkok')) {
                return 'BKK';
            }
            if (airline.includes('singapore') || airline.includes('scoot')) {
                return 'SIN';
            }
            if (airline.includes('malaysia') || airline.includes('airasia') || airline.includes('malindo') || airline.includes('batik')) {
                return 'KUL';
            }
            // Deterministic hash fallback
            const airportCodes = ['AUH', 'MAA', 'BKK', 'SIN', 'KUL'];
            let hash = 0;
            const fn = f.flight_number || '';
            for (let i = 0; i < fn.length; i++) {
                hash = fn.charCodeAt(i) + ((hash << 5) - hash);
            }
            return airportCodes[Math.abs(hash) % airportCodes.length];
        }

        function applyFilters() {
            // Sidebar filters state reading
            const maxPrice = parseInt(document.getElementById('filter-price').value);
            const fareTypes = Array.from(document.querySelectorAll('.filter-fare:checked')).map(cb => cb.value);
            const stopsVals = Array.from(document.querySelectorAll('.filter-stop-btn.selected')).map(btn => parseInt(btn.getAttribute('data-val')));
            const connBtnList = Array.from(document.querySelectorAll('.filter-conn-btn.selected'));
            const depBtnList = Array.from(document.querySelectorAll('.filter-dep-btn.selected'));
            const arrBtnList = Array.from(document.querySelectorAll('.filter-arr-btn.selected'));
            
            const selectedAirlinesEl = document.querySelectorAll('.filter-airline:checked');
            const selectedAirlines = selectedAirlinesEl ? Array.from(selectedAirlinesEl).map(cb => cb.value) : [];
            const selectedAirports = Array.from(document.querySelectorAll('.filter-airport:checked')).map(cb => cb.value);

            let filtered = cachedFlights.filter(f => {
                // Price Filter
                const fPriceLkr = parseFloat(f.price) * (window.searchAdults || 1);
                if (fPriceLkr > maxPrice) return false;
                
                // Fare Type (GDS=Refundable, LCC=Non Refundable)
                const isRef = f.flight_type !== 'LCC';
                if (isRef && !fareTypes.includes('REFUNDABLE')) return false;
                if (!isRef && !fareTypes.includes('NON_REFUNDABLE')) return false;
                
                // Stops Filter
                let stops = f.segment_count - 1;
                if (stops > 2) stops = 2;
                if (!stopsVals.includes(stops)) return false;
                
                // Connection/Duration Filter
                const depTime = new Date(f.departure_time);
                const arrTime = new Date(f.arrival_time);
                const hoursDuration = Math.floor(Math.abs(arrTime - depTime) / 36e5);
                
                let connMatch = false;
                for (let btn of connBtnList) {
                    const minH = parseInt(btn.getAttribute('data-min'));
                    const maxH = parseInt(btn.getAttribute('data-max'));
                    if (hoursDuration >= minH && hoursDuration < maxH) {
                        connMatch = true;
                        break;
                    }
                }
                if (!connMatch) return false;
                
                // Timing logic using active tab state
                let outTimeVal, retTimeVal;
                if (activeTimingTab === 'DEPARTURE') {
                    outTimeVal = depTime.getHours();
                    if (f.return_flight) {
                        retTimeVal = new Date(f.return_flight.departure_time).getHours();
                    } else {
                        retTimeVal = arrTime.getHours();
                    }
                } else {
                    outTimeVal = arrTime.getHours();
                    if (f.return_flight) {
                        retTimeVal = new Date(f.return_flight.arrival_time).getHours();
                    } else {
                        retTimeVal = arrTime.getHours();
                    }
                }

                // Match outbound timings against depBtnList
                let outMatch = false;
                for (let btn of depBtnList) {
                    const minH = parseInt(btn.getAttribute('data-min'));
                    const maxH = parseInt(btn.getAttribute('data-max'));
                    if (outTimeVal >= minH && outTimeVal < maxH) {
                        outMatch = true;
                        break;
                    }
                }
                if (!outMatch) return false;
                
                // Match return timings against arrBtnList
                let retMatch = false;
                for (let btn of arrBtnList) {
                    const minH = parseInt(btn.getAttribute('data-min'));
                    const maxH = parseInt(btn.getAttribute('data-max'));
                    if (retTimeVal >= minH && retTimeVal < maxH) {
                        retMatch = true;
                        break;
                    }
                }
                if (!retMatch) return false;
                
                // Airline Filter (Sidebar checkboxes)
                if (selectedAirlines.length > 0) {
                    if (!selectedAirlines.includes(f.airline)) return false;
                    if (f.return_flight && !selectedAirlines.includes(f.return_flight.airline)) return false;
                }

                // Airline Filter (Carousel quick filter)
                if (activeAirlineFilter) {
                    if (f.airline !== activeAirlineFilter && (!f.return_flight || f.return_flight.airline !== activeAirlineFilter)) return false;
                }

                // Connecting Airports Filter
                const outLayover = getLayoverAirport(f);
                if (outLayover && !selectedAirports.includes(outLayover)) return false;
                if (f.return_flight) {
                    const retLayover = getLayoverAirport(f.return_flight);
                    if (retLayover && !selectedAirports.includes(retLayover)) return false;
                }
                
                return true;
            });

            // Sorting
            if (currentSort === 'cheapest') {
                filtered.sort((a, b) => parseFloat(a.price) - parseFloat(b.price));
            } else if (currentSort === 'fastest') {
                filtered.sort((a, b) => {
                    const durA = (new Date(a.arrival_time) - new Date(a.departure_time)) + (a.return_flight ? (new Date(a.return_flight.arrival_time) - new Date(a.return_flight.departure_time)) : 0);
                    const durB = (new Date(b.arrival_time) - new Date(b.departure_time)) + (b.return_flight ? (new Date(b.return_flight.arrival_time) - new Date(b.return_flight.departure_time)) : 0);
                    return durA - durB;
                });
            } else if (currentSort === 'best') {
                filtered.sort((a, b) => {
                    const scoreA = parseFloat(a.price) * (window.searchAdults || 1) + (a.segment_count * 20000) + (a.return_flight ? a.return_flight.segment_count * 20000 : 0);
                    const scoreB = parseFloat(b.price) * (window.searchAdults || 1) + (b.segment_count * 20000) + (b.return_flight ? b.return_flight.segment_count * 20000 : 0);
                    return scoreA - scoreB;
                });
            }
            
            renderResults(filtered);
        }

        function formatDateFriendly(dateObj) {
            return dateObj.toLocaleDateString('en-US', { weekday: 'short', day: '2-digit', month: 'short' });
        }
        function formatTimeFriendly(dateObj) {
            return dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
        }

        function renderResults(flights) {
            const container = document.getElementById('flight-list-container');
            container.innerHTML = '';
            if(flights.length === 0) {
                if (!flightsLoaded) {
                    container.innerHTML = `
                        <div class="loading-state">
                            <i class="fa-solid fa-spinner fa-spin fa-2x" style="color: var(--primary-blue); margin-bottom: 15px;"></i>
                            <h3>Interrogating Global Distribution Systems...</h3>
                        </div>
                    `;
                } else {
                    container.innerHTML = `<div class="loading-state">No flights matched your filters.</div>`;
                }
                return;
            }
            
            flights.forEach(f => {
                const dep = new Date(f.departure_time);
                const arr = new Date(f.arrival_time);
                const hours = Math.floor(Math.abs(arr - dep) / 36e5);
                const mins = Math.round((Math.abs(arr - dep) % 36e5) / 60000);
                
                const priceLkr = parseFloat(f.price) * (window.searchAdults || 1);
                const originalPriceLkr = priceLkr * 1.08;
                const priceFormatted = "LKR " + Math.round(priceLkr).toLocaleString();
                const originalPriceFormatted = "LKR " + Math.round(originalPriceLkr).toLocaleString();
                
                const depDateStr = formatDateFriendly(dep);
                const depTimeStr = formatTimeFriendly(dep);
                const arrDateStr = formatDateFriendly(arr);
                const arrTimeStr = formatTimeFriendly(arr);

                let isRoundTrip = !!f.return_flight;
                
                let cardHtml = `
                    <div class="flight-card" style="background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 8px; padding: 20px; display: flex; flex-direction: column; box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: box-shadow 0.2s; margin-bottom: 15px;">
                        <!-- Top Header bar -->
                        <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border-color); padding-bottom: 10px; margin-bottom: 15px; width: 100%;">
                            <div style="display: flex; align-items: center; gap: 8px;">
                                <i class="fa-solid fa-plane" style="color: #ff8c00;"></i>
                                <span style="font-weight: bold; font-size: 14px;">${f.airline}</span>
                                <span style="color: #ccc; margin: 0 5px;">|</span>
                                <span style="color: var(--primary-blue); font-size: 13px; font-weight: bold; display: flex; align-items: center; gap: 4px; cursor: pointer;">
                                    <i class="fa-solid fa-tags"></i> BEST OFFERS <i class="fa-solid fa-angle-down"></i>
                                </span>
                            </div>
                            <div style="font-size: 13px; color: var(--primary-blue); cursor: pointer; display: flex; align-items: center; gap: 4px;">
                                Share <i class="fa-solid fa-share-nodes"></i>
                            </div>
                        </div>
                        
                        <!-- Middle content: Legs and Price -->
                        <div style="display: flex; align-items: stretch; justify-content: space-between; width: 100%;">
                            <!-- Legs column -->
                            <div style="flex: 1; display: flex; flex-direction: column; gap: 15px; justify-content: center;">
                                <!-- Outbound Leg -->
                                <div style="display: flex; align-items: center; justify-content: space-between; gap: 20px;">
                                    <!-- Bullet indicator -->
                                    <div style="display: flex; align-items: center; justify-content: center; width: 24px;">
                                        <div style="width: 14px; height: 14px; border: 4px solid var(--primary-blue); border-radius: 50%; background: white;"></div>
                                    </div>
                                    
                                    <!-- Route points and details -->
                                    <div style="flex: 1; display: flex; align-items: center; justify-content: space-between; gap: 15px;">
                                        <!-- Origin -->
                                        <div style="width: 140px;">
                                            <div style="font-size: 16px; font-weight: 700; color: var(--text-main);">${f.origin}</div>
                                            <div style="font-size: 13px; color: var(--text-muted); margin-top: 2px;">${depDateStr}, ${depTimeStr}</div>
                                        </div>
                                        
                                        <!-- Duration -->
                                        <div style="flex: 1; text-align: center; position: relative;">
                                            <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 4px;">${hours}h ${mins}m</div>
                                            <div style="position: relative; display: flex; align-items: center; justify-content: center;">
                                                <div style="height: 2px; background: #ccc; width: 100%; position: absolute; z-index: 1;"></div>
                                                <i class="fa-solid fa-arrow-right" style="position: absolute; right: 0; background: var(--card-bg); padding-left: 5px; z-index: 2; color: #ccc;"></i>
                                            </div>
                                            <div style="font-size: 11px; color: var(--primary-blue); font-weight: 600; margin-top: 4px;">
                                                ${f.segment_count === 1 ? 'Direct' : (f.segment_count-1) + ' Stop(s)'}
                                            </div>
                                        </div>
                                        
                                        <!-- Destination -->
                                        <div style="width: 140px; padding-left: 20px;">
                                            <div style="font-size: 16px; font-weight: 700; color: var(--text-main);">${f.destination}</div>
                                            <div style="font-size: 13px; color: var(--text-muted); margin-top: 2px;">${arrDateStr}, ${arrTimeStr}</div>
                                        </div>
                                    </div>
                                </div>
                `;

                if (isRoundTrip) {
                    const retDep = new Date(f.return_flight.departure_time);
                    const retArr = new Date(f.return_flight.arrival_time);
                    const retHours = Math.floor(Math.abs(retArr - retDep) / 36e5);
                    const retMins = Math.round((Math.abs(retArr - retDep) % 36e5) / 60000);
                    
                    const retDepDateStr = formatDateFriendly(retDep);
                    const retDepTimeStr = formatTimeFriendly(retDep);
                    const retArrDateStr = formatDateFriendly(retArr);
                    const retArrTimeStr = formatTimeFriendly(retArr);

                    cardHtml += `
                                <!-- Dotted divider -->
                                <div style="border-top: 1px dotted var(--border-color); margin: 10px 0; width: 100%;"></div>
                                
                                <!-- Return Leg -->
                                <div style="display: flex; align-items: center; justify-content: space-between; gap: 20px;">
                                    <!-- Bullet indicator -->
                                    <div style="display: flex; align-items: center; justify-content: center; width: 24px;">
                                        <div style="width: 14px; height: 14px; border: 4px solid var(--primary-blue); border-radius: 50%; background: white;"></div>
                                    </div>
                                    
                                    <!-- Route points and details -->
                                    <div style="flex: 1; display: flex; align-items: center; justify-content: space-between; gap: 15px;">
                                        <!-- Origin -->
                                        <div style="width: 140px;">
                                            <div style="font-size: 16px; font-weight: 700; color: var(--text-main);">${f.return_flight.origin}</div>
                                            <div style="font-size: 13px; color: var(--text-muted); margin-top: 2px;">${retDepDateStr}, ${retDepTimeStr}</div>
                                        </div>
                                        
                                        <!-- Duration -->
                                        <div style="flex: 1; text-align: center; position: relative;">
                                            <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 4px;">${retHours}h ${retMins}m</div>
                                            <div style="position: relative; display: flex; align-items: center; justify-content: center;">
                                                <div style="height: 2px; background: #ccc; width: 100%; position: absolute; z-index: 1;"></div>
                                                <i class="fa-solid fa-arrow-right" style="position: absolute; right: 0; background: var(--card-bg); padding-left: 5px; z-index: 2; color: #ccc;"></i>
                                            </div>
                                            <div style="font-size: 11px; color: var(--primary-blue); font-weight: 600; margin-top: 4px;">
                                                ${f.return_flight.segment_count === 1 ? 'Direct' : (f.return_flight.segment_count-1) + ' Stop(s)'}
                                            </div>
                                        </div>
                                        
                                        <!-- Destination -->
                                        <div style="width: 140px; padding-left: 20px;">
                                            <div style="font-size: 16px; font-weight: 700; color: var(--text-main);">${f.return_flight.destination}</div>
                                            <div style="font-size: 13px; color: var(--text-muted); margin-top: 2px;">${retArrDateStr}, ${retArrTimeStr}</div>
                                        </div>
                                    </div>
                                </div>
                    `;
                }

                cardHtml += `
                            </div>
                            
                            <!-- Price column -->
                            <div style="width: 210px; text-align: right; display: flex; flex-direction: column; align-items: flex-end; justify-content: center; gap: 6px; border-left: 1px solid var(--border-color); padding-left: 20px; margin-left: 20px;">
                                <div style="font-size: 13px; text-decoration: line-through; color: var(--text-muted);">${originalPriceFormatted}</div>
                                <div class="fc-price" style="font-size: 24px; font-weight: 800; color: var(--success-green); line-height: 1.1;">${priceFormatted}</div>
                                <div style="font-size: 11px; color: var(--text-muted); margin-top: -3px; margin-bottom: 5px;">Total for ${window.searchAdults || 1} Traveler(s)</div>
                                
                                <button class="btn-book" onclick="openBookingModal(${f.id}, ${isRoundTrip ? f.return_flight.id : 'null'}, ${priceLkr}, true)" style="background: var(--success-green); color: white; border: none; padding: 10px 24px; border-radius: 4px; font-size: 14px; font-weight: 700; cursor: pointer; width: 100%; transition: background 0.2s;">Book Now</button>
                                
                                <div onclick="openBookingModal(${f.id}, ${isRoundTrip ? f.return_flight.id : 'null'}, ${priceLkr}, false)" style="font-size: 12px; color: #ff8c00; font-weight: bold; display: flex; align-items: center; gap: 4px; cursor: pointer; margin-top: 4px; justify-content: flex-end;">
                                    HOLD for FREE <i class="fa-solid fa-hand-pointer"></i>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Bottom Footer bar -->
                        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-color); padding-top: 10px; margin-top: 15px; width: 100%;">
                            <div style="font-size: 13px; color: var(--primary-blue); display: flex; align-items: center; gap: 6px; cursor: pointer;">
                                <i class="fa-solid fa-calendar-days"></i> Pay monthly ${"LKR " + Math.round(priceLkr / 12).toLocaleString()}
                            </div>
                            <div style="font-size: 13px; color: var(--primary-blue); display: flex; align-items: center; gap: 6px; cursor: pointer;">
                                <i class="fa-solid fa-circle-info"></i> View flight details
                            </div>
                        </div>
                    </div>
                `;
                
                container.innerHTML += cardHtml;
            });
        }

        // Helper: Populate DOB and Expiry date dropdowns
        function populateDobAndExpiryDropdowns() {
            const days = document.querySelectorAll('#book-dob-day, #book-exp-day');
            const months = document.querySelectorAll('#book-dob-month, #book-exp-month');
            const dobYearSelect = document.getElementById('book-dob-year');
            const expYearSelect = document.getElementById('book-exp-year');
            
            // Only populate if they are not already filled
            if (days[0].options.length > 0) return;
            
            days.forEach(sel => {
                sel.innerHTML = '<option value="">Day</option>';
                for (let d = 1; d <= 31; d++) {
                    const dStr = String(d).padStart(2, '0');
                    sel.innerHTML += `<option value="${dStr}">${d}</option>`;
                }
            });
            
            const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            months.forEach(sel => {
                sel.innerHTML = '<option value="">Month</option>';
                monthNames.forEach((m, idx) => {
                    const mVal = String(idx + 1).padStart(2, '0');
                    sel.innerHTML += `<option value="${mVal}">${m}</option>`;
                });
            });
            
            // DOB years (1920 to current year)
            const currentYear = new Date().getFullYear();
            dobYearSelect.innerHTML = '<option value="">Year</option>';
            for (let y = currentYear; y >= 1920; y--) {
                dobYearSelect.innerHTML += `<option value="${y}">${y}</option>`;
            }
            
            // Expiry years (current year to 20 years in future)
            expYearSelect.innerHTML = '<option value="">Year</option>';
            for (let y = currentYear; y <= currentYear + 20; y++) {
                expYearSelect.innerHTML += `<option value="${y}">${y}</option>`;
            }
        }
        
        // Helper: Toggle traveler card visibility
        function toggleTravelerDetails() {
            const body = document.getElementById('traveler-form-body');
            const chev = document.getElementById('traveler-chevron');
            if (body.style.display === 'none') {
                body.style.display = 'block';
                chev.className = 'fa-solid fa-chevron-down';
            } else {
                body.style.display = 'none';
                chev.className = 'fa-solid fa-chevron-right';
            }
        }
        
        // Helper: Toggle Frequent Flyer program
        function toggleFrequentFlyer() {
            const container = document.getElementById('flyer-container');
            const sign = document.getElementById('flyer-toggle-sign');
            if (container.style.display === 'none') {
                container.style.display = 'block';
                sign.innerText = '-';
            } else {
                container.style.display = 'none';
                sign.innerText = '+';
            }
        }
        
        // Helper: Concatenate title, first and last name to book-pax-name
        function updateFormattedPaxName() {
            const title = document.getElementById('book-title').value;
            const lastname = document.getElementById('book-lastname').value.trim();
            const firstname = document.getElementById('book-firstname').value.trim();
            const fullname = `${title} ${firstname} ${lastname}`.trim();
            document.getElementById('book-pax-name').value = fullname;
        }
        
        // Helper: Synchronize mobile, email, passport to original form hidden fields
        function syncFormValues() {
            // Passport
            const passportNew = document.getElementById('book-passport-new').value.trim();
            document.getElementById('book-passport').value = passportNew;
            
            // Mobile
            const prefix = document.getElementById('book-phone-prefix').value;
            const number = document.getElementById('book-phone-number').value.trim();
            document.getElementById('book-phone').value = prefix + ' ' + number;
            
            // Email
            const emailNew = document.getElementById('book-email-new').value.trim();
            document.getElementById('book-email').value = emailNew;
        }

        let currentStep = 1;

        function goToStep(stepNum) {
            if (stepNum === 2 && currentStep === 1) {
                if (!validateStep1()) return;
            }
            
            document.getElementById('booking-step-1').style.display = 'none';
            document.getElementById('booking-step-2').style.display = 'none';
            document.getElementById('booking-step-3').style.display = 'none';
            
            document.getElementById('booking-step-' + stepNum).style.display = 'block';
            
            // Stepper visual nodes update
            for (let i = 1; i <= 3; i++) {
                const node = document.getElementById('step-node-' + i);
                const circle = node.querySelector('.step-circle');
                const text = node.querySelector('span');
                
                if (i < stepNum) {
                    circle.style.background = '#10b981';
                    circle.style.borderColor = '#10b981';
                    circle.style.color = 'white';
                    circle.innerHTML = '<i class="fa-solid fa-check"></i>';
                    text.style.color = '#10b981';
                    text.style.fontWeight = '700';
                } else if (i === stepNum) {
                    circle.style.background = 'var(--primary-blue)';
                    circle.style.borderColor = 'var(--primary-blue)';
                    circle.style.color = 'white';
                    circle.innerHTML = i;
                    text.style.color = 'var(--primary-blue)';
                    text.style.fontWeight = '700';
                } else {
                    circle.style.background = '#e2e8f0';
                    circle.style.borderColor = '#cbd5e1';
                    circle.style.color = 'var(--text-muted)';
                    circle.innerHTML = i;
                    text.style.color = 'var(--text-muted)';
                    text.style.fontWeight = '600';
                }
            }
            
            const progressLine = document.getElementById('step-progress-indicator');
            if (stepNum === 1) progressLine.style.width = '0%';
            else if (stepNum === 2) progressLine.style.width = '50%';
            else if (stepNum === 3) {
                progressLine.style.width = '100%';
                populateBookingSummary();
            }
            
            currentStep = stepNum;
        }

        function validateStep1() {
            const lastname = document.getElementById('book-lastname');
            const firstname = document.getElementById('book-firstname');
            const dobDay = document.getElementById('book-dob-day');
            const dobMonth = document.getElementById('book-dob-month');
            const dobYear = document.getElementById('book-dob-year');
            const passport = document.getElementById('book-passport-new');
            const expDay = document.getElementById('book-exp-day');
            const expMonth = document.getElementById('book-exp-month');
            const expYear = document.getElementById('book-exp-year');
            const phone = document.getElementById('book-phone-number');
            const email = document.getElementById('book-email-new');
            const confirmCB = document.getElementById('book-confirm-names');
            
            let valid = true;
            const fields = [lastname, firstname, dobDay, dobMonth, dobYear, passport, expDay, expMonth, expYear, phone, email];
            
            fields.forEach(f => {
                if (!f.value || f.value.trim() === '') {
                    f.style.borderColor = '#ef4444';
                    valid = false;
                } else {
                    f.style.borderColor = '#cbd5e1';
                }
            });
            
            if (!confirmCB.checked) {
                confirmCB.parentElement.style.borderColor = '#ef4444';
                confirmCB.parentElement.style.background = '#fef2f2';
                valid = false;
            } else {
                confirmCB.parentElement.style.borderColor = '#f3e8ff';
                confirmCB.parentElement.style.background = '#faf5ff';
            }
            
            if (!valid) {
                alert("Please fill in all required traveler details and check the passport name confirmation box.");
                return false;
            }
            
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email.value.trim())) {
                email.style.borderColor = '#ef4444';
                alert("Please enter a valid email address.");
                return false;
            }
            
            return true;
        }

        function populateBookingSummary() {
            document.getElementById('summary-pax-name').innerText = document.getElementById('book-pax-name').value || 'N/A';
            document.getElementById('summary-pax-passport').innerText = document.getElementById('book-passport-new').value || 'N/A';
            
            const dob = `${document.getElementById('book-dob-day').value}/${document.getElementById('book-dob-month').value}/${document.getElementById('book-dob-year').value}`;
            document.getElementById('summary-pax-dob').innerText = dob || 'N/A';
            
            const mobile = document.getElementById('book-phone-prefix').value + ' ' + document.getElementById('book-phone-number').value;
            document.getElementById('summary-pax-mobile').innerText = mobile || 'N/A';
            document.getElementById('summary-pax-email').innerText = document.getElementById('book-email-new').value || 'N/A';
            
            const ffNum = document.getElementById('book-flyer-number').value.trim();
            const ffProg = document.getElementById('book-flyer-program').value;
            if (ffNum) {
                document.getElementById('summary-pax-ff').innerText = `${ffProg} (${ffNum})`;
            } else {
                document.getElementById('summary-pax-ff').innerText = 'None';
            }
            
            const outSeat = document.getElementById('book-seat').value || 'Not selected';
            const retSeat = document.getElementById('book-return-seat').value || 'Not selected';
            
            document.getElementById('summary-outbound-seat').innerText = outSeat;
            const returnSeatContainer = document.getElementById('summary-return-seat-container');
            if (document.getElementById('book-return-id').value) {
                document.getElementById('summary-return-seat').innerText = retSeat;
                returnSeatContainer.style.display = 'table-row';
            } else {
                returnSeatContainer.style.display = 'none';
            }
            
            const displayPrice = document.getElementById('book-display-price').innerText;
            const priceNum = parseFloat(displayPrice.replace(/[^0-9.]/g, ''));
            const oldPrice = {{ modifying_old_price | default(0) }};
            const finalPrice = Math.max(0, priceNum - oldPrice);
            
            if (document.getElementById('summary-flight-price')) {
                document.getElementById('summary-flight-price').innerText = displayPrice;
            }
            document.getElementById('summary-total-price').innerText = 'LKR ' + finalPrice.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            
            // Populate Special Requests & Meals
            document.getElementById('summary-pax-meal').innerText = document.getElementById('book-meal-pref').value;
            document.getElementById('summary-pax-wheelchair').innerText = document.getElementById('book-wheelchair').value;
            document.getElementById('summary-pax-airport').innerText = document.getElementById('book-airport-assist').value;
            document.getElementById('summary-pax-allergies').innerText = document.getElementById('book-allergies').value.trim() || 'None';
            document.getElementById('summary-pax-other').innerText = document.getElementById('book-other-req').value.trim() || 'None';
        }

        function toggleSpecialRequests() {
            const body = document.getElementById('requests-form-body');
            const chev = document.getElementById('requests-chevron');
            if (body.style.display === 'none') {
                body.style.display = 'block';
                chev.className = 'fa-solid fa-chevron-down';
            } else {
                body.style.display = 'none';
                chev.className = 'fa-solid fa-chevron-right';
            }
        }

        function updatePaymentSelection(method) {
            const cardTile = document.getElementById('pay-tile-card');
            const cardForm = document.getElementById('card-payment-form');
            
            if (cardTile) {
                cardTile.style.borderColor = 'var(--primary-blue)';
                cardTile.style.background = '#f0f9ff';
                const span = cardTile.querySelector('span');
                if (span) span.style.color = '#0369a1';
            }
            if (cardForm) {
                cardForm.style.display = 'block';
            }
        }

        function formatCardNumber(input) {
            let value = input.value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
            let formatted = '';
            for (let i = 0; i < value.length; i++) {
                if (i > 0 && i % 4 === 0) {
                    formatted += ' ';
                }
                formatted += value[i];
            }
            input.value = formatted;
        }

        function formatExpiry(input) {
            let value = input.value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
            if (value.length > 2) {
                input.value = value.substr(0, 2) + '/' + value.substr(2, 2);
            } else {
                input.value = value;
            }
        }

        function updateVirtualCard() {
            const num = document.getElementById('card-number').value.trim() || '•••• •••• •••• ••••';
            const holder = document.getElementById('card-name').value.trim().toUpperCase() || 'JOHN DOE';
            const expiry = document.getElementById('card-expiry').value.trim() || 'MM/YY';
            
            document.getElementById('v-card-number').innerText = num;
            document.getElementById('v-card-holder').innerText = holder;
            document.getElementById('v-card-expiry').innerText = expiry;
        }

        function updateFrequentFlyerPrefix() {
            const prog = document.getElementById('book-flyer-program').value;
            const prefixEl = document.getElementById('ff-prefix');
            if (prog === 'OTHER') {
                const outboundId = parseInt(document.getElementById('book-outbound-id').value);
                const flight = cachedFlights.find(fl => fl.id === outboundId);
                if (flight && flight.flight_number) {
                    prefixEl.innerText = flight.flight_number.split('-')[0] + '-';
                } else {
                    prefixEl.innerText = 'EY-';
                }
            } else {
                prefixEl.innerText = prog + '-';
            }
        }

        // --- Interactive Seat Map fuselage selector logic ---
                let selectedOutboundSeats = [];
        let selectedReturnSeats = [];
        let activeSeatTab = 'outbound';
        let seatOccupancyMap = {}; 

        function initializeSeats(outboundId, returnId) {
            selectedOutboundSeats = [];
            selectedReturnSeats = [];
            activeSeatTab = 'outbound';
            
            // Seed occupancy based on flight IDs to make it look realistic
            seatOccupancyMap = {};
            const seed = (outboundId || 0) + (returnId || 0);
            const rows = 8;
            const cols = ['A', 'B', 'C', 'D', 'E', 'F'];
            for (let r = 1; r <= rows; r++) {
                cols.forEach(c => {
                    const seatName = `${r}${c}`;
                    const hash = (r * 31 + c.charCodeAt(0) * 17 + seed) % 100;
                    seatOccupancyMap[seatName] = hash < 25; // 25% occupancy
                });
            }

            // Reset inputs
            document.getElementById('book-seat').value = '';
            document.getElementById('book-return-seat').value = '';
            
            // Setup tab display
            const returnTab = document.getElementById('seat-tab-return');
            if (returnId) {
                returnTab.style.display = 'block';
            } else {
                returnTab.style.display = 'none';
            }
            
            switchSeatTab('outbound');
        }

        function switchSeatTab(tab) {
            activeSeatTab = tab;
            document.getElementById('seat-tab-outbound').classList.toggle('active', tab === 'outbound');
            document.getElementById('seat-tab-return').classList.toggle('active', tab === 'return');
            
            renderSeatGrid();
        }

        function renderSeatGrid() {
            const grid = document.getElementById('seat-grid-inner');
            grid.innerHTML = '';
            
            const rows = 8;
            const cols = ['A', 'B', 'C', 'aisle', 'D', 'E', 'F'];
            const currentSelectionArray = (activeSeatTab === 'outbound') ? selectedOutboundSeats : selectedReturnSeats;
            
            for (let r = 1; r <= rows; r++) {
                const rowDiv = document.createElement('div');
                rowDiv.className = 'seat-row';
                
                cols.forEach(c => {
                    const seatDiv = document.createElement('div');
                    if (c === 'aisle') {
                        seatDiv.className = 'seat aisle';
                        seatDiv.innerText = '';
                    } else {
                        const seatName = `${r}${c}`;
                        const isOccupied = seatOccupancyMap[seatName];
                        const isSelected = currentSelectionArray.includes(seatName);
                        
                        seatDiv.className = `seat ${isOccupied ? 'occupied' : ''} ${isSelected ? 'selected' : ''}`;
                        seatDiv.innerText = seatName;
                        
                        if (!isOccupied) {
                            seatDiv.onclick = function() {
                                selectSeat(seatName);
                            };
                        }
                    }
                    rowDiv.appendChild(seatDiv);
                });
                grid.appendChild(rowDiv);
            }
            
            const selectedText = currentSelectionArray.length > 0 ? currentSelectionArray.join(', ') : 'None';
            document.getElementById('selected-seat-display').innerText = selectedText;
        }

                function selectSeat(seatName) {
            const maxS = window.searchAdults || 1;
            if (activeSeatTab === 'outbound') {
                if (selectedOutboundSeats.includes(seatName)) {
                    selectedOutboundSeats = selectedOutboundSeats.filter(s => s !== seatName);
                } else if (selectedOutboundSeats.length < maxS) {
                    selectedOutboundSeats.push(seatName);
                } else { alert('You can only select up to ' + maxS + ' seat(s).'); return; }
                document.getElementById('book-seat').value = selectedOutboundSeats.join(', ');
                renderSeatGrid();
                if (selectedOutboundSeats.length === maxS) {
                    const returnId = document.getElementById('book-return-id').value;
                    if (returnId) setTimeout(() => switchSeatTab('return'), 300);
                }
            } else {
                if (selectedReturnSeats.includes(seatName)) {
                    selectedReturnSeats = selectedReturnSeats.filter(s => s !== seatName);
                } else if (selectedReturnSeats.length < maxS) {
                    selectedReturnSeats.push(seatName);
                } else { alert('You can only select up to ' + maxS + ' seat(s).'); return; }
                document.getElementById('book-return-seat').value = selectedReturnSeats.join(', ');
                renderSeatGrid();
            }
        }, 300);
                }
            } else {
                selectedReturnSeat = seatName;
                document.getElementById('book-return-seat').value = seatName;
                renderSeatGrid();
            }
        }

        function openBookingModal(outboundId, returnId, priceLkr, ticketNow) {
            {% if session.get('modifying_booking_id') %}
            const oldPriceNum = {{ modifying_old_price | default(0) }};
            const newPriceNum = Math.round(priceLkr);
            const diffNum = Math.max(0, newPriceNum - oldPriceNum);
            
            const msg = "--- FLIGHT CHANGE CONFIRMATION ---\n\n" +
                        "New Flight Price: LKR " + newPriceNum.toLocaleString() + "\n" +
                        "Previous Ticket Credit: -LKR " + oldPriceNum.toLocaleString() + "\n\n" +
                        "Total Balance to Pay: LKR " + diffNum.toLocaleString() + "\n\n" +
                        "Do you want to confirm these new travel dates and proceed to checkout?";
            if (!confirm(msg)) {
                return;
            }
            {% endif %}
            
            document.getElementById('book-outbound-id').value = outboundId;
            document.getElementById('book-return-id').value = returnId || '';
            document.getElementById('book-ticket-now').value = ticketNow ? 'true' : 'false';
            document.getElementById('book-display-price').innerText = "LKR " + Math.round(priceLkr).toLocaleString();
            
            const titleEl = document.getElementById('booking-modal-title');
            const submitBtn = document.getElementById('book-submit-btn');
            
            if (ticketNow) {
                titleEl.innerHTML = `<i class="fa-solid fa-plane-departure" style="margin-right: 8px;"></i>GDS Flight Instant Issuance`;
                submitBtn.innerText = "Book Ticket Now";
                submitBtn.style.background = 'var(--success-green)';
            } else {
                titleEl.innerHTML = `<i class="fa-solid fa-plane-departure" style="margin-right: 8px;"></i>GDS Flight Hold (HOLD for FREE)`;
                submitBtn.innerText = "Hold Booking (Free)";
                submitBtn.style.background = '#ff8c00';
            }
            
            // Go to step 1
            goToStep(1);
            
            // Initialize forms & select components
            populateDobAndExpiryDropdowns();
            initializeSeats(outboundId, returnId);
            
            // Clean inputs
            document.getElementById('book-lastname').value = '';
            document.getElementById('book-firstname').value = '';
            document.getElementById('book-passport-new').value = '';
            document.getElementById('book-phone-number').value = '';
            document.getElementById('book-email-new').value = '';
            document.getElementById('book-confirm-names').checked = false;
            
            // Clean Special service requests
            document.getElementById('book-meal-pref').value = 'Standard Meal';
            document.getElementById('book-wheelchair').value = 'No wheelchair assistance required';
            document.getElementById('book-airport-assist').value = 'No special airport assistance';
            document.getElementById('book-allergies').value = '';
            document.getElementById('book-other-req').value = '';
            
            document.getElementById('pay-method-card').checked = true;
            updatePaymentSelection('card');
            
            // Clean Card Payment Gateway details
            document.getElementById('card-name').value = '';
            document.getElementById('card-number').value = '';
            document.getElementById('card-expiry').value = '';
            document.getElementById('card-cvv').value = '';
            updateVirtualCard();
            
            // Clean hidden inputs
            document.getElementById('book-pax-name').value = '';
            document.getElementById('book-passport').value = '';
            document.getElementById('book-phone').value = '';
            document.getElementById('book-email').value = '';
            
            // Set Frequent Flyer default program & prefix dynamically
            const flight = cachedFlights.find(fl => fl.id === outboundId);
            let airlineCode = 'EY'; // fallback
            if (flight && flight.flight_number) {
                const parts = flight.flight_number.split('-');
                if (parts.length > 0) {
                    airlineCode = parts[0].toUpperCase();
                }
            }
            
            document.getElementById('ff-prefix').innerText = airlineCode + '-';
            const flyerProg = document.getElementById('book-flyer-program');
            let matchedOption = false;
            for (let i = 0; i < flyerProg.options.length; i++) {
                if (flyerProg.options[i].value === airlineCode) {
                    flyerProg.selectedIndex = i;
                    matchedOption = true;
                    break;
                }
            }
            if (!matchedOption) {
                flyerProg.value = 'OTHER';
            }
            
            // Show modal
            document.getElementById('booking-modal').style.display = 'flex';
        }

        function closeBookingModal() {
            document.getElementById('booking-modal').style.display = 'none';
        }

        let pendingBookingPayload = null;

        function closeCreditConfirmModal() {
            document.getElementById('credit-confirm-modal').style.display = 'none';
        }

        function closeSuccessReceiptModal() {
            document.getElementById('success-receipt-modal').style.display = 'none';
            // Close the flight results tab to return to the dashboard
            window.close();
            // Fallback if browser blocks window.close()
            window.location.href = '/';
        }

function printReceipt() {
            document.getElementById('success-receipt-modal').classList.add('printable-modal');
            document.getElementById('eticket-modal').classList.remove('printable-modal');
            window.print();
        }

        function downloadTicket() {
            if (!window.currentBookingData) return;
            document.getElementById('success-receipt-modal').style.display = 'none';
            generateEticket(window.currentBookingData.data, window.currentBookingData.payload);
            document.getElementById('eticket-modal').style.display = 'flex';
        }

        function closeEticketModal() {
            document.getElementById('eticket-modal').style.display = 'none';
            // Close the flight results tab to return to the dashboard
            window.close();
            // Fallback if browser blocks window.close()
            window.location.href = '/';
        }

        function printEticket() {
            document.getElementById('success-receipt-modal').classList.remove('printable-modal');
            document.getElementById('eticket-modal').classList.add('printable-modal');
            window.print();
        }

        function generateEticket(data, payload) {
            document.getElementById('eticket-pnr').innerText = data.pnr_reference || '-';
            document.getElementById('eticket-pax').innerText = payload.passenger_name || 'N/A';
            document.getElementById('eticket-ticket').innerText = data.ticket_number || 'PENDING';
            
            document.getElementById('eticket-meal').innerText = payload.meal_preference || 'Standard Meal (No Preference)';
            document.getElementById('eticket-wheelchair').innerText = payload.wheelchair_assistance || 'No wheelchair assistance required';
            document.getElementById('eticket-assist').innerText = payload.airport_assistance || 'No special airport assistance';
            document.getElementById('eticket-allergy').innerText = payload.allergy_conditions || 'None Reported';

            const whatsappText = `SKYLINE AIRWAYS E-TICKET\nPNR: ${data.pnr_reference || '-'}\nPassenger: ${payload.passenger_name || '-'}\nTicket: ${data.ticket_number || 'PENDING'}\nHave a safe flight!`;
            document.getElementById('eticket-whatsapp-btn').href = `https://wa.me/?text=${encodeURIComponent(whatsappText)}`;

            const outboundFlight = cachedFlights.find(fl => fl.id === payload.flight_id);
            const returnFlight = (outboundFlight && outboundFlight.return_flight && outboundFlight.return_flight.id === payload.return_flight_id) ? outboundFlight.return_flight : null;
            
            document.getElementById('eticket-flight-title').innerText = returnFlight ? '2. FLIGHT ITINERARY (ROUND TRIP)' : '2. FLIGHT ITINERARY (ONE WAY)';
            
            const container = document.getElementById('eticket-flights-container');
            container.innerHTML = '';
            
            if (outboundFlight) {
                const depDate = formatFlightDate(outboundFlight.departure_time);
                const depTime = formatFlightTime(outboundFlight.departure_time);
                const durText = getFlightDuration(outboundFlight);
                const depCity = getCityName(outboundFlight.origin);
                const arrCity = getCityName(outboundFlight.destination);
                const seatNum = payload.seat_number || '[ ]';
                
                container.innerHTML += `
                <div style="border: 1px solid #cbd5e1; border-radius: 4px; overflow: hidden; margin-bottom: 10px;">
                    <div style="background: #1e3a8a; color: white; padding: 6px 12px; font-size: 10.5px; font-weight: 700; text-transform: uppercase;">
                        OUTBOUND FLIGHT: ${depCity} (${outboundFlight.origin}) TO ${arrCity} (${outboundFlight.destination})
                    </div>
                    <div style="padding: 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed #cbd5e1;">
                        <div style="width: 150px;">
                            <div style="font-size: 22px; font-weight: 800; color: #0f172a;">${outboundFlight.origin}</div>
                            <div style="font-size: 10px; color: #475569;">${depCity}</div>
                        </div>
                        <div style="flex: 1; text-align: center; position: relative;">
                            <div style="height: 1px; background: #cbd5e1; width: 100%; position: absolute; top: 50%; z-index: 1;"></div>
                            <i class="fa-solid fa-plane" style="color: #3b82f6; background: white; padding: 0 5px; position: relative; z-index: 2; font-size: 14px;"></i>
                            <div style="font-size: 9px; color: #94a3b8; margin-top: 5px;">${durText} (Direct)</div>
                        </div>
                        <div style="width: 150px; text-align: right;">
                            <div style="font-size: 22px; font-weight: 800; color: #0f172a;">${outboundFlight.destination}</div>
                            <div style="font-size: 10px; color: #475569;">${arrCity}</div>
                        </div>
                    </div>
                    <div style="padding: 12px; display: flex; justify-content: space-between; font-size: 10px; background: #f8fafc;">
                        <div>
                            <div style="color: #94a3b8; margin-bottom: 2px;">FLIGHT NUMBER</div>
                            <div style="font-weight: 700; color: #0f172a;">${outboundFlight.flight_number}</div>
                        </div>
                        <div>
                            <div style="color: #94a3b8; margin-bottom: 2px;">DEPARTURE DATE & TIME</div>
                            <div style="font-weight: 700; color: #0f172a;">${depDate} / ${depTime}</div>
                        </div>
                        <div>
                            <div style="color: #94a3b8; margin-bottom: 2px;">SEAT NUMBER</div>
                            <div style="font-weight: 700; color: #0f172a;">${seatNum}</div>
                        </div>
                        <div>
                            <div style="color: #94a3b8; margin-bottom: 2px;">CABIN CLASS</div>
                            <div style="font-weight: 700; color: #0f172a;">Economy (G)</div>
                        </div>
                    </div>
                </div>`;
            }
            
            if (returnFlight) {
                const depDate = formatFlightDate(returnFlight.departure_time);
                const depTime = formatFlightTime(returnFlight.departure_time);
                const durText = getFlightDuration(returnFlight);
                const depCity = getCityName(returnFlight.origin);
                const arrCity = getCityName(returnFlight.destination);
                const seatNum = payload.return_seat_number || '[ ]';
                
                container.innerHTML += `
                <div style="border: 1px solid #cbd5e1; border-radius: 4px; overflow: hidden; margin-bottom: 10px;">
                    <div style="background: #1e3a8a; color: white; padding: 6px 12px; font-size: 10.5px; font-weight: 700; text-transform: uppercase;">
                        RETURN FLIGHT: ${depCity} (${returnFlight.origin}) TO ${arrCity} (${returnFlight.destination})
                    </div>
                    <div style="padding: 12px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px dashed #cbd5e1;">
                        <div style="width: 150px;">
                            <div style="font-size: 22px; font-weight: 800; color: #0f172a;">${returnFlight.origin}</div>
                            <div style="font-size: 10px; color: #475569;">${depCity}</div>
                        </div>
                        <div style="flex: 1; text-align: center; position: relative;">
                            <div style="height: 1px; background: #cbd5e1; width: 100%; position: absolute; top: 50%; z-index: 1;"></div>
                            <i class="fa-solid fa-plane" style="color: #3b82f6; background: white; padding: 0 5px; position: relative; z-index: 2; font-size: 14px; transform: rotate(180deg);"></i>
                            <div style="font-size: 9px; color: #94a3b8; margin-top: 5px;">${durText} (Direct)</div>
                        </div>
                        <div style="width: 150px; text-align: right;">
                            <div style="font-size: 22px; font-weight: 800; color: #0f172a;">${returnFlight.destination}</div>
                            <div style="font-size: 10px; color: #475569;">${arrCity}</div>
                        </div>
                    </div>
                    <div style="padding: 12px; display: flex; justify-content: space-between; font-size: 10px; background: #f8fafc;">
                        <div>
                            <div style="color: #94a3b8; margin-bottom: 2px;">FLIGHT NUMBER</div>
                            <div style="font-weight: 700; color: #0f172a;">${returnFlight.flight_number}</div>
                        </div>
                        <div>
                            <div style="color: #94a3b8; margin-bottom: 2px;">DEPARTURE DATE & TIME</div>
                            <div style="font-weight: 700; color: #0f172a;">${depDate} / ${depTime}</div>
                        </div>
                        <div>
                            <div style="color: #94a3b8; margin-bottom: 2px;">SEAT NUMBER</div>
                            <div style="font-weight: 700; color: #0f172a;">${seatNum}</div>
                        </div>
                        <div>
                            <div style="color: #94a3b8; margin-bottom: 2px;">CABIN CLASS</div>
                            <div style="font-weight: 700; color: #0f172a;">Economy (G)</div>
                        </div>
                    </div>
                </div>`;
            }
        }

        function formatFlightDate(dateStr) {
            if (!dateStr) return "June, 23 2019";
            const dateObj = new Date(dateStr);
            const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
            const month = months[dateObj.getMonth()];
            const day = dateObj.getDate();
            const year = dateObj.getFullYear();
            return `${month}, ${day} ${year}`;
        }

        function formatFlightTime(timeStr) {
            if (!timeStr) return "1:35 PM";
            if (timeStr.includes(':')) {
                let parts = timeStr.split(' ');
                let timePart = parts[parts.length - 1]; 
                let tParts = timePart.split(':');
                let hr = parseInt(tParts[0]);
                let min = tParts[1] || '00';
                let ampm = hr >= 12 ? 'PM' : 'AM';
                let displayHr = hr % 12;
                if (displayHr === 0) displayHr = 12;
                return `${displayHr}:${min} ${ampm}`;
            }
            return timeStr;
        }

        function getFlightTerminal(flightCode, isArrival) {
            let hash = 0;
            const code = flightCode || "FL123";
            for (let i = 0; i < code.length; i++) {
                hash = code.charCodeAt(i) + ((hash << 5) - hash);
            }
            const val = Math.abs(hash) % 3;
            if (isArrival) {
                return ['Terminal 3', 'Terminal A', 'Terminal C'][val];
            } else {
                return ['Terminal C', 'Terminal 2', 'Terminal 1'][val];
            }
        }

        function getFlightDuration(fl) {
            if (!fl) return "Total flight 8h 43m";
            const org = (fl.origin || 'CMB').toUpperCase();
            const dest = (fl.destination || 'MEL').toUpperCase();
            if (org === 'CMB' && dest === 'MEL') return "Total flight 10h 30m";
            if (org === 'MEL' && dest === 'CMB') return "Total flight 10h 45m";
            if (org === 'CMB' && dest === 'SIN') return "Total flight 4h 15m";
            if (org === 'SIN' && dest === 'CMB') return "Total flight 4h 20m";
            return "Total flight 7h 50m";
        }

        
        function openFareCalendar() {
            document.getElementById('fare-calendar-modal').style.display = 'flex';
            generateFareGrid();
        }

        function closeFareCalendar() {
            document.getElementById('fare-calendar-modal').style.display = 'none';
        }
        
        function formatCalDate(d) {
            const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            return `${String(d.getDate()).padStart(2, '0')} ${months[d.getMonth()]}, ${days[d.getDay()]}`;
        }

        function formatYMD(d) {
            return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
        }

        function searchNewDates(depDate, retDate) {
            const urlParams = new URLSearchParams(window.location.search);
            urlParams.set('date', depDate);
            urlParams.set('returnDate', retDate);
            window.location.search = urlParams.toString();
        }

        function generateFareGrid() {
            const urlParams = new URLSearchParams(window.location.search);
            const baseDepStr = urlParams.get('date');
            const baseDepDate = baseDepStr ? new Date(baseDepStr + 'T00:00:00') : new Date();
            const retDateParam = urlParams.get('returnDate');
            let baseRetDate = new Date(baseDepDate);
            if (retDateParam) {
                baseRetDate = new Date(retDateParam + 'T00:00:00');
            } else {
                baseRetDate.setDate(baseRetDate.getDate() + 5);
            }
            
            const depDates = [];
            for(let i = -3; i <= 3; i++) {
                let d = new Date(baseDepDate);
                d.setDate(d.getDate() + i);
                depDates.push(d);
            }
            
            const retDates = [];
            for(let i = -3; i <= 3; i++) {
                let d = new Date(baseRetDate);
                d.setDate(d.getDate() + i);
                retDates.push(d);
            }
            
            const thead = document.getElementById('fare-calendar-head');
            let headHTML = '<tr><th style="padding: 15px; border: 1px solid #e2e8f0; background: white;"></th>';
            depDates.forEach(d => {
                headHTML += `<th style="padding: 15px 5px; border: 1px solid #e2e8f0; font-weight: normal; color: #475569;">
                    <div style="font-size: 10px; font-weight: 600;">DEPART</div>
                    <div>${formatCalDate(d)}</div>
                </th>`;
            });
            headHTML += '</tr>';
            thead.innerHTML = headHTML;
            
            const tbody = document.getElementById('fare-calendar-body');
            let bodyHTML = '';
            
            let basePrice = 175678;
            if (cachedFlights && cachedFlights.length > 0) {
                basePrice = Math.min(...cachedFlights.map(f => f.price));
            }
            
            retDates.forEach((rd, rIdx) => {
                bodyHTML += `<tr>`;
                bodyHTML += `<td style="padding: 15px 5px; border: 1px solid #e2e8f0; font-weight: normal; color: #475569; background: #f8fafc;">
                    <div style="font-size: 10px; font-weight: 600;">RETURN</div>
                    <div>${formatCalDate(rd)}</div>
                </td>`;
                
                depDates.forEach((dd, dIdx) => {
                    // Make it empty if return is before departure
                    let strippedRd = new Date(rd.getFullYear(), rd.getMonth(), rd.getDate());
                    let strippedDd = new Date(dd.getFullYear(), dd.getMonth(), dd.getDate());
                    if (strippedRd < strippedDd) {
                        bodyHTML += `<td style="padding: 15px; border: 1px solid #e2e8f0; background: white;"></td>`;
                        return;
                    }
                    
                    let offset = (Math.sin(rIdx * 3 + dIdx * 7) * (basePrice * 0.25));
                    if (rIdx === 3 && dIdx === 3) offset = 0; 
                    let price = Math.round((basePrice + offset) / 10) * 10;
                    
                    let color = '#22c55e'; // CHEAPEST (Green)
                    if (price > basePrice * 1.05 && price < basePrice * 1.25) color = '#f59e0b'; // MEDIUM (Orange)
                    if (price >= basePrice * 1.25) color = '#ef4444'; // HIGH (Red)
                    
                    bodyHTML += `<td class="cal-cell" style="padding: 15px; border: 1px solid #e2e8f0; cursor: pointer; transition: background 0.2s; background: white;" onclick="searchNewDates('${formatYMD(dd)}', '${formatYMD(rd)}')">
                        <div style="color: ${color}; font-weight: 700; font-size: 13px;">LKR ${price.toLocaleString()}</div>
                        <div style="color: #64748b; font-size: 9px; margin-top: 4px; text-decoration: underline;">Select</div>
                    </td>`;
                });
                bodyHTML += `</tr>`;
            });
            tbody.innerHTML = bodyHTML;
        }

        function showSuccessReceipt(data, payload) {
            window.currentBookingData = { data, payload };
            const paymentMethod = payload.payment_method;
            const ticketNow = payload.ticket_now;
            
            // Find selected flight details from cachedFlights
            const outboundFlight = cachedFlights.find(fl => fl.id === payload.flight_id);
            const returnFlight = (outboundFlight && outboundFlight.return_flight && outboundFlight.return_flight.id === payload.return_flight_id) ? outboundFlight.return_flight : null;
            
            // Populate header title based on hold or purchase
            const headerTitle = document.getElementById('receipt-header-title');
            const statusText = document.getElementById('receipt-status');
            const itinerariesContainer = document.getElementById('receipt-itineraries-container');
            
            if (ticketNow) {
                headerTitle.innerText = "Payment Confirmation";
                statusText.innerText = "Confirmed & Ticketed";
                statusText.style.color = "#10b981";
            } else {
                headerTitle.innerText = "Booking Hold Confirmation";
                statusText.innerText = "Hold Confirmed";
                statusText.style.color = "#f59e0b";
            }
            
            // Clear existing itineraries
            itinerariesContainer.innerHTML = '';
            itinerariesContainer.style.display = 'none'; // Hide the itinerary section completely


            const outSeat = payload.seat_number || 'Not Selected';
            const retSeat = payload.return_seat_number;
            const seatDisplay = retSeat ? `${outSeat} (Outbound), ${retSeat} (Return)` : outSeat;
            
            const ticketNum = data.ticket_number || 'HOLD - PENDING PAYMENT';
            
            // Format Value Added Services dynamically
            let vasList = [];
            if (payload.meal_preference && payload.meal_preference !== 'Standard Meal') {
                vasList.push(`🍱 Meal: ${payload.meal_preference}`);
            }
            if (payload.wheelchair_assistance && payload.wheelchair_assistance.toLowerCase() !== 'no wheelchair assistance required') {
                vasList.push(`♿ Wheelchair: ${payload.wheelchair_assistance}`);
            }
            if (payload.airport_assistance && payload.airport_assistance.toLowerCase() !== 'no special airport assistance') {
                vasList.push(`🙋‍♂️ Assist: ${payload.airport_assistance}`);
            }
            if (payload.allergy_conditions) {
                vasList.push(`⚠️ Allergies: ${payload.allergy_conditions}`);
            }
            if (payload.other_requests) {
                vasList.push(`📝 Request: ${payload.other_requests}`);
            }
            const vasHTML = vasList.length > 0 ? vasList.join('<br>') : 'Standard Services';

            // Populate table values
            document.getElementById('receipt-pnr').innerText = data.pnr_reference || 'PNR-GDS' + Math.floor(Math.random() * 900000 + 100000);
            document.getElementById('receipt-ticket-number').innerText = ticketNum;
            document.getElementById('receipt-pax-name').innerText = payload.passenger_name || 'Sanka Lasitha';
            document.getElementById('receipt-passport').innerText = payload.passport_number || 'N/A';
            document.getElementById('receipt-route').innerText = document.getElementById('summary-cities').innerText || 'Colombo to Melbourne';
            document.getElementById('receipt-seats').innerText = seatDisplay;
            document.getElementById('receipt-vas-list').innerHTML = vasHTML;
            document.getElementById('receipt-pay-method').innerText = (paymentMethod === 'card') ? 'Corporate Credit Card (PG)' : 'Account Credit Wallet';
            document.getElementById('receipt-total-price').innerText = document.getElementById('summary-total-price').innerText;
            
            // Construct WhatsApp message
            const pnrRef = data.pnr_reference || 'Pending';
            const routeInfo = document.getElementById('summary-cities').innerText;
            const totalPrice = document.getElementById('summary-total-price').innerText;
            const payMethodDisplay = paymentMethod === 'card' ? 'Corporate Credit Card' : 'Agency Credit Wallet';
            
            const ticketInfo = ticketNow ? `\n🎫 *Ticket Number:* ${ticketNum}` : '';
            const messageText = `✈️ *SYSTEM FRD Airline - Ticket Confirmation* ✈️\n\nThank you for selecting our service for your travel partner.\n\nHere are your travel details:\n👤 *Passenger:* ${payload.passenger_name}\n🎫 *PNR Reference:* ${pnrRef}${ticketInfo}\n🎟 *Status:* ${ticketNow ? 'TICKETED' : 'HOLD'}\n🧳 *Route:* ${routeInfo}\n💺 *Seat(s):* ${seatDisplay}\n💳 *Payment Method:* ${payMethodDisplay}\n💰 *Total Amount:* ${totalPrice}\n\nThank you for selecting our service for your travel partner. We wish you a safe and wonderful flight! ✈️🌟`;
            
            const whatsappUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(messageText)}`;
            document.getElementById('receipt-whatsapp-btn').href = whatsappUrl;
            
            // Hide main modal and show success modal
            closeBookingModal();
            document.getElementById('success-receipt-modal').style.display = 'flex';
        }

        function executeCreditBookingSubmit() {
            if (!pendingBookingPayload) return;
            
            closeCreditConfirmModal();
            
            const submitBtn = document.getElementById('book-submit-btn');
            submitBtn.disabled = true;
            submitBtn.innerText = "Processing GDS transaction...";
            
            fetch('/api/flights/book', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(pendingBookingPayload)
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showSuccessReceipt(data, pendingBookingPayload);
                } else {
                    alert("Error confirming booking: " + data.error);
                }
            })
            .catch(err => {
                console.error(err);
                alert("Client/Network Error: " + err.message + "\n\nPlease check the console for more details.");
            })
            .finally(() => {
                submitBtn.disabled = false;
                if (ticketNow) {
                    submitBtn.innerText = "Pay Now & Ticket";
                } else {
                    submitBtn.innerText = "Hold Booking";
                }
            });
        }

        function submitBooking(event) {
            event.preventDefault();
            
            const outboundId = parseInt(document.getElementById('book-outbound-id').value);
            const returnIdVal = document.getElementById('book-return-id').value;
            const returnId = returnIdVal ? parseInt(returnIdVal) : null;
                        const ticketNow = document.getElementById('book-ticket-now').value === 'true';
            
            let allNames = [];
            let allPassports = [];
            document.querySelectorAll('.traveler-details-card').forEach(card => {
                let fn='', ln='', pass='';
                card.querySelectorAll('input').forEach(inp => {
                    if(inp.placeholder && inp.placeholder.includes('Other Names')) fn = inp.value.trim();
                    if(inp.placeholder && inp.placeholder.includes('Surnames')) ln = inp.value.trim();
                    if(inp.placeholder && inp.placeholder.includes('Passport Number')) pass = inp.value.trim();
                });
                if(fn || ln) allNames.push(fn + ' ' + ln);
                if(pass) allPassports.push(pass);
            });
            if(allNames.length > 0) document.getElementById('book-pax-name').value = allNames.join(' & ');
            if(allPassports.length > 0) document.getElementById('book-passport').value = allPassports.join(', ');
            
            const paymentMethod = document.querySelector('input[name="payment_method_option"]:checked').value;
            if (paymentMethod === 'card') {
                const cardName = document.getElementById('card-name').value.trim();
                const cardNum = document.getElementById('card-number').value.trim();
                const cardExp = document.getElementById('card-expiry').value.trim();
                const cardCvv = document.getElementById('card-cvv').value.trim();
                
                if (!cardName || !cardNum || !cardExp || !cardCvv) {
                    alert("Please fill in all Payment Gateway Bank details (Card Holder, Card Number, Expiry, and CVV/CVC).");
                    return;
                }
            }
            
            const payload = {
                flight_id: outboundId,
                passenger_name: document.getElementById('book-pax-name').value,
                passport_number: document.getElementById('book-passport').value,
                mobile: document.getElementById('book-phone').value,
                email: document.getElementById('book-email').value,
                seat_number: document.getElementById('book-seat').value,
                ticket_now: ticketNow,
                meal_preference: document.getElementById('book-meal-pref').value,
                wheelchair_assistance: document.getElementById('book-wheelchair').value,
                airport_assistance: document.getElementById('book-airport-assist').value,
                allergy_conditions: document.getElementById('book-allergies').value.trim(),
                other_requests: document.getElementById('book-other-req').value.trim(),
                payment_method: paymentMethod,
                b2c: true
            };
            
            if (returnId) {
                payload.return_flight_id = returnId;
                payload.return_seat_number = document.getElementById('book-return-seat').value;
            }
            
            if (paymentMethod === 'credit' && ticketNow) {
                // Fetch the agent's available credit balance from our new API endpoint
                fetch('/api/agent/credit')
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        const creditBalance = data.credit_balance;
                        const priceText = document.getElementById('summary-total-price').innerText;
                        const priceNum = parseFloat(priceText.replace(/[^0-9.]/g, ''));
                        const remaining = creditBalance - priceNum;
                        
                        document.getElementById('confirm-wallet-balance').innerText = 'LKR ' + Math.round(creditBalance).toLocaleString();
                        document.getElementById('confirm-wallet-deduct').innerText = 'LKR ' + Math.round(priceNum).toLocaleString();
                        
                        const remainingEl = document.getElementById('confirm-wallet-remaining');
                        remainingEl.innerText = 'LKR ' + Math.round(remaining).toLocaleString();
                        if (remaining < 0) {
                            remainingEl.style.color = '#ef4444';
                            alert("Warning: Insufficient credit balance to process this ticket placement. Please top up your wallet.");
                            return;
                        } else {
                            remainingEl.style.color = '#16a34a';
                        }
                        
                        // Store payload globally and show confirm modal
                        pendingBookingPayload = payload;
                        document.getElementById('credit-confirm-modal').style.display = 'flex';
                    } else {
                        alert("Error retrieving credit balance: " + data.error);
                    }
                })
                .catch(err => {
                    alert("Error communicating with agent wallet server.");
                });
            } else {
                // Otherwise submit card or non-ticket hold immediately
                const submitBtn = document.getElementById('book-submit-btn');
                submitBtn.disabled = true;
                submitBtn.innerText = "Processing GDS transaction...";
                
                fetch('/api/flights/book', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        showSuccessReceipt(data, payload);
                    } else {
                        alert("Error confirming booking: " + data.error);
                    }
                })
                .catch(err => {
                    console.error(err);
                    alert("Client/Network Error: " + err.message + "\n\nPlease check the console for more details.");
                })
                .finally(() => {
                    submitBtn.disabled = false;
                    if (ticketNow) {
                        submitBtn.innerText = "Book Ticket Now";
                    } else {
                        submitBtn.innerText = "Hold Booking (Free)";
                    }
                });
            }
        }
    