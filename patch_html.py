import re

def update_html():
    path = r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\flight_results.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Replace the media print CSS
    old_css = r"""        @media print \{
            body > \* \{
                display: none !important;
            \}
            #success-receipt-modal \{
                display: flex !important;
                position: absolute !important;
                left: 0 !important;
                top: 0 !important;
                width: 100% !important;
                height: auto !important;
                background: white !important;
                z-index: 999999 !important;
                padding: 0 !important;
            \}
            #success-receipt-modal > div \{
                box-shadow: none !important;
                border: none !important;
                max-width: 100% !important;
                width: 100% !important;
                margin: 0 !important;
                border-radius: 0 !important;
            \}
            \.no-print \{
                display: none !important;
            \}
        \}"""
    
    new_css = """        @media print {
            body > * {
                display: none !important;
            }
            .printable-modal {
                display: flex !important;
                position: absolute !important;
                left: 0 !important;
                top: 0 !important;
                width: 100% !important;
                height: auto !important;
                background: white !important;
                z-index: 999999 !important;
                padding: 0 !important;
            }
            .printable-modal > div {
                box-shadow: none !important;
                border: none !important;
                max-width: 100% !important;
                width: 100% !important;
                margin: 0 !important;
                border-radius: 0 !important;
            }
            .no-print {
                display: none !important;
            }
        }"""
    
    content = re.sub(old_css, new_css, content)

    # 2. Add eticket HTML below success-receipt-modal
    eticket_html = """
    <!-- E-Ticket Modal -->
    <div id="eticket-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(15, 23, 42, 0.6); z-index: 10600; align-items: center; justify-content: center; backdrop-filter: blur(4px); overflow-y: auto; padding: 20px 0;">
        <div style="background: white; width: 100%; max-width: 800px; border-radius: 8px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); overflow: hidden; margin: auto; font-family: 'Inter', sans-serif;">
            <div id="printable-eticket-content" style="padding: 40px; color: #333;">
                <!-- Header -->
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 20px;">
                    <div>
                        <h1 style="margin: 0; color: #1e3a8a; font-size: 28px; font-weight: 800;">SKYLINE</h1>
                        <div style="color: #64748b; font-size: 12px; letter-spacing: 2px;">AIRWAYS</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: #64748b; font-size: 10px; font-weight: bold; margin-bottom: 2px;">BOOKING REFERENCE (PNR)</div>
                        <div id="eticket-pnr" style="color: #1e3a8a; font-size: 24px; font-weight: 800;">-</div>
                    </div>
                </div>

                <!-- Title banner -->
                <div style="border-top: 2px solid #1e3a8a; border-bottom: 2px solid #1e3a8a; padding: 8px 0; text-align: center; margin-bottom: 20px;">
                    <span style="color: #1e3a8a; font-weight: 700; letter-spacing: 1px; font-size: 15px;">E-TICKET ITINERARY & RECEIPT</span>
                </div>

                <!-- Info box -->
                <div style="border: 1px solid #cbd5e1; border-radius: 4px; padding: 12px; font-size: 10px; color: #475569; margin-bottom: 20px; line-height: 1.4;">
                    This is your travel itinerary and e-ticket receipt, which forms part of your contract of carriage. Your electronic ticket is recorded in the airline's computer reservation system. You may need to show this receipt to enter the airport and/or to prove return or onward travel to customs and immigration officials.<br>
                    <b>All timings mentioned are local.</b>
                </div>

                <!-- Section 1 -->
                <div style="background: #e2e8f0; color: #1e3a8a; padding: 6px 12px; font-weight: 700; font-size: 12px; margin-bottom: 10px;">
                    1. TRAVELER INFORMATION
                </div>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 11px; border: 1px solid #cbd5e1;">
                    <tr>
                        <td style="padding: 10px; border-right: 1px solid #cbd5e1; width: 50%;">
                            <div style="color: #94a3b8; font-size: 9px; margin-bottom: 4px;">PASSENGER NAME</div>
                            <div id="eticket-pax" style="font-weight: 700; color: #0f172a; font-size: 13px;">-</div>
                        </td>
                        <td style="padding: 10px;">
                            <div style="color: #94a3b8; font-size: 9px; margin-bottom: 4px;">TICKET NUMBER</div>
                            <div id="eticket-ticket" style="font-weight: 700; color: #0f172a; font-size: 13px;">-</div>
                        </td>
                    </tr>
                </table>

                <!-- Section 2 -->
                <div style="background: #e2e8f0; color: #1e3a8a; padding: 6px 12px; font-weight: 700; font-size: 12px; margin-bottom: 10px;" id="eticket-flight-title">
                    2. FLIGHT ITINERARY
                </div>
                <div id="eticket-flights-container" style="margin-bottom: 20px;">
                    <!-- Flight blocks will be injected here -->
                </div>

                <!-- Section 3 -->
                <div style="background: #e2e8f0; color: #1e3a8a; padding: 6px 12px; font-weight: 700; font-size: 12px; margin-bottom: 10px;">
                    3. BAGGAGE ALLOWANCE
                </div>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 11px; border: 1px solid #cbd5e1;">
                    <tr>
                        <td style="padding: 10px; border-right: 1px solid #cbd5e1; width: 50%;">
                            <div style="color: #94a3b8; font-size: 9px; margin-bottom: 4px;">CHECKED BAGGAGE ALLOWANCE</div>
                            <div style="font-weight: 700; color: #0f172a; font-size: 12px;">30 KG (Per Adult Passenger)</div>
                        </td>
                        <td style="padding: 10px;">
                            <div style="color: #94a3b8; font-size: 9px; margin-bottom: 4px;">HAND CABIN LUGGAGE</div>
                            <div style="font-weight: 700; color: #0f172a; font-size: 12px;">7 KG (1 Piece Max)</div>
                        </td>
                    </tr>
                </table>

                <!-- Section 4 -->
                <div style="background: #e2e8f0; color: #1e3a8a; padding: 6px 12px; font-weight: 700; font-size: 12px; margin-bottom: 10px;">
                    4. VALUE ADDED SERVICES & SPECIAL REQUESTS
                </div>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 11px; border: 1px solid #cbd5e1;">
                    <tr>
                        <td style="padding: 10px; border-right: 1px solid #cbd5e1; border-bottom: 1px solid #cbd5e1; width: 50%;">
                            <div style="color: #94a3b8; font-size: 9px; margin-bottom: 4px;">SPECIAL MEAL REQUEST</div>
                            <div id="eticket-meal" style="font-weight: 700; color: #0f172a; font-size: 12px;">Standard Meal (No Preference)</div>
                        </td>
                        <td style="padding: 10px; border-bottom: 1px solid #cbd5e1;">
                            <div style="color: #94a3b8; font-size: 9px; margin-bottom: 4px;">WHEELCHAIR REQUEST</div>
                            <div id="eticket-wheelchair" style="font-weight: 700; color: #0f172a; font-size: 12px;">No wheelchair assistance required</div>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-right: 1px solid #cbd5e1; width: 50%;">
                            <div style="color: #94a3b8; font-size: 9px; margin-bottom: 4px;">AIRPORT SPECIAL ASSISTANCE</div>
                            <div id="eticket-assist" style="font-weight: 700; color: #0f172a; font-size: 12px;">No special airport assistance</div>
                        </td>
                        <td style="padding: 10px;">
                            <div style="color: #94a3b8; font-size: 9px; margin-bottom: 4px;">ALLERGY CONDITIONS</div>
                            <div id="eticket-allergy" style="font-weight: 700; color: #0f172a; font-size: 12px;">None Reported</div>
                        </td>
                    </tr>
                </table>

                <!-- Section 5 -->
                <div style="background: #e2e8f0; color: #1e3a8a; padding: 6px 12px; font-weight: 700; font-size: 12px; margin-bottom: 10px;">
                    5. TERMS, CONDITIONS & IMPORTANT NOTICES
                </div>
                <ul style="font-size: 9.5px; color: #dc2626; padding-left: 15px; margin-top: 5px; margin-bottom: 30px; line-height: 1.5; list-style-type: square;">
                    <li><span style="color: #475569;">A Processing Fee will apply to all documents refunded in addition to any fees charged by the supplier. You will receive the refund, where applicable, within 30 working days. For details, please call hotline number 0112222222.</span></li>
                    <li><span style="color: #475569;">Re-issue or re-validation may attract Airline fees.</span></li>
                    <li><span style="color: #475569;">Please ensure that you carry all valid travel documents for the destination / transit city prior to departure.</span></li>
                    <li><span style="color: #475569;">All timings are based on a city's local time.</span></li>
                    <li><span style="color: #475569;">Flight times given above may change without any prior notice from the Airline. Kindly call the local Airline office to obtain updated information on your flight timings.</span></li>
                    <li><span style="color: #475569;">Carriage and other services provided by the airline are subject to conditions of carriage, which are hereby incorporated by reference. The conditions of carriage may be obtained directly from the airline.</span></li>
                    <li><span style="color: #475569;">Standard airport check-in begins 3 hours prior to the scheduled departure time. Late arrival at the check-in counter may prevent you from boarding the flights.</span></li>
                    <li><span style="color: #475569;">Prior to travel check with the departure airport for restrictions on carriage of liquids, aerosols and gels in hand baggage.</span></li>
                </ul>
            </div>

            <!-- Action Footer -->
            <div style="background: #f8fafc; border-top: 1px solid #f1f5f9; padding: 18px 24px; display: flex; justify-content: flex-end; gap: 10px;" class="no-print">
                <button type="button" onclick="closeEticketModal()" style="background: white; border: 1px solid #cbd5e1; color: #475569; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 13.5px; font-weight: bold;">
                    Done
                </button>
                <button type="button" onclick="printEticket()" style="background: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-size: 13.5px; font-weight: bold; display: inline-flex; align-items: center; gap: 6px;">
                    <i class="fa-solid fa-print"></i> Print E-Ticket
                </button>
            </div>
        </div>
    </div>
"""
    if 'id="eticket-modal"' not in content:
        content = content.replace('<!-- Print styling specifically to focus on success modal receipt -->', eticket_html + '\n    <!-- Print styling specifically to focus on success modal receipt -->')

    # 3. Update Javascript functions
    js_update = """
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
            window.location.reload();
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

            const outboundFlight = cachedFlights.find(fl => fl.id === payload.flight_id);
            const returnFlight = payload.return_flight_id ? cachedFlights.find(fl => fl.id === payload.return_flight_id) : null;
            
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
"""
    
    old_js = r"""        function printReceipt\(\) \{
            window.print\(\);
        \}

        function downloadTicket\(\) \{
            alert\("Generating E-Ticket\.\.\."\);
            // Move to next step \(dashboard for now\)
            window.location.href = '/agent_dashboard';
        \}"""
    
    content = re.sub(old_js, js_update.strip(), content)

    # 4. Save window.currentBookingData in showSuccessReceipt
    old_show = "function showSuccessReceipt(data, payload) {"
    new_show = "function showSuccessReceipt(data, payload) {\n            window.currentBookingData = { data, payload };"
    if "window.currentBookingData = { data, payload };" not in content:
        content = content.replace(old_show, new_show)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        
if __name__ == '__main__':
    update_html()
