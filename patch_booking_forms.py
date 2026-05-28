import re

def patch_file():
    with open('templates/b2c_flight_results.html', 'r', encoding='utf-8') as f:
        c = f.read()

    submit_code = '''            const ticketNow = document.getElementById('book-ticket-now').value === 'true';
            
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
            if(allPassports.length > 0) document.getElementById('book-passport').value = allPassports.join(', ');'''
    c = c.replace("const ticketNow = document.getElementById('book-ticket-now').value === 'true';", submit_code)

    modal_code = '''            document.getElementById('book-submit-btn').innerText = ticketNow ? 'Pay Now & Ticket' : 'Hold Booking';

            document.querySelectorAll('.traveler-cloned').forEach(el => el.remove());
            const origCard = document.getElementById('traveler-form-body').closest('.traveler-details-card');
            let lastCard = origCard;
            for(let i=2; i<=(window.searchAdults||1); i++) {
                const clone = origCard.cloneNode(true);
                clone.classList.add('traveler-cloned');
                clone.querySelector('.traveler-header').innerHTML = `<span style="display: flex; align-items: center; gap: 8px; color: #1e293b;">
                                <span style="position: relative; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; background: #e0f2fe; color: #0284c7; border-radius: 50%;">
                                    <i class="fa-solid fa-user" style="font-size: 14px;"></i>
                                </span>
                                Adult ${i}
                            </span>
                            <i class="fa-solid fa-chevron-down" style="color: #64748b; font-size: 14px;"></i>`;
                clone.querySelectorAll('input').forEach(inp => inp.value = '');
                clone.querySelectorAll('[id]').forEach(el => el.removeAttribute('id'));
                origCard.parentNode.insertBefore(clone, lastCard.nextSibling);
                lastCard = clone;
            }
            selectedOutboundSeats = [];
            selectedReturnSeats = [];'''
    c = c.replace("document.getElementById('book-submit-btn').innerText = ticketNow ? 'Pay Now & Ticket' : 'Hold Booking';", modal_code)

    seat_init = '''        let selectedOutboundSeats = [];
        let selectedReturnSeats = [];
        let activeSeatTab = 'outbound';
        let seatOccupancyMap = {}; 

        function initializeSeats(outboundId, returnId) {
            selectedOutboundSeats = [];
            selectedReturnSeats = [];'''
    
    # regex replacement for seat_init
    pattern = r"let selectedOutboundSeat = '';\s*let selectedReturnSeat = '';\s*let activeSeatTab = 'outbound';\s*let seatOccupancyMap = \{\};\s*function initializeSeats\(outboundId, returnId\) \{\s*selectedOutboundSeat = '';\s*selectedReturnSeat = '';"
    c = re.sub(pattern, seat_init, c)

    c = c.replace("const currentSelection = (activeSeatTab === 'outbound') ? selectedOutboundSeat : selectedReturnSeat;", 
                  "const currentSelectionArray = (activeSeatTab === 'outbound') ? selectedOutboundSeats : selectedReturnSeats;")
    
    c = c.replace("const isSelected = currentSelection === seatName;", 
                  "const isSelected = currentSelectionArray.includes(seatName);")

    c = c.replace("const selectedText = currentSelection ? currentSelection : 'None';", 
                  "const selectedText = currentSelectionArray.length > 0 ? currentSelectionArray.join(', ') : 'None';")

    seat_select = '''        function selectSeat(seatName) {
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
        }'''
    
    c = re.sub(r"function selectSeat\(seatName\) \{.*?\}", seat_select, c, flags=re.DOTALL)

    with open('templates/b2c_flight_results.html', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    patch_file()
