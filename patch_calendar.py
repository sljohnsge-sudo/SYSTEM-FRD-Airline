import re

def patch():
    path = r"c:\Users\SankaLasitha\OneDrive - Acorn\Desktop\SYSTEM FRD Airline\templates\flight_results.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add Ribbon CSS
    ribbon_css = """
        .ribbon {
            width: 65px;
            height: 60px;
            background: #ff8c00;
            color: white;
            text-align: center;
            font-weight: 800;
            font-size: 13px;
            line-height: 1.2;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            position: relative;
        }
        .ribbon::after {
            content: '';
            position: absolute;
            bottom: -15px;
            left: 0;
            border-left: 32.5px solid #ff8c00;
            border-right: 32.5px solid #ff8c00;
            border-bottom: 15px solid transparent;
        }
        
        .cal-cell:hover {
            background: #effcff !important;
        }
"""
    if ".ribbon" not in content:
        content = content.replace("/* Modal Styles */", ribbon_css + "        /* Modal Styles */")

    # 2. Add Banner HTML
    banner_html = """
            <!-- Fare Calendar Banner -->
            <div class="fare-calendar-banner" style="background: white; border: 1px solid var(--border-color); border-radius: 4px; display: flex; align-items: center; justify-content: space-between; padding: 0 20px 0 0; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); height: 60px;">
                <div style="display: flex; align-items: center; height: 100%;">
                    <!-- Orange Ribbon -->
                    <div class="ribbon">
                        LOW<br>PRICE
                    </div>
                    
                    <div style="padding-left: 20px; display: flex; align-items: center; gap: 10px; color: #475569; font-weight: 600; font-size: 15px;">
                        <i class="fa-solid fa-chart-area" style="font-size: 20px;"></i>
                        Flexible with your dates? We found cheaper fares for you!
                    </div>
                </div>
                
                <div style="display: flex; align-items: center; gap: 10px;">
                    <button onclick="openFareCalendar()" style="background: white; border: 1px solid #3b82f6; color: #3b82f6; padding: 8px 16px; border-radius: 4px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 8px; font-size: 14px; transition: all 0.2s;">
                        <i class="fa-regular fa-calendar-days"></i> View Fare Calendar
                    </button>
                    <button style="background: white; border: 1px solid #3b82f6; color: #003b95; padding: 8px 12px; border-radius: 4px; cursor: pointer; transition: all 0.2s;">
                        <i class="fa-solid fa-share-nodes"></i>
                    </button>
                </div>
            </div>
"""
    if "fare-calendar-banner" not in content:
        # insert before <!-- Sorting tabs -->
        content = content.replace("<!-- Sorting tabs -->", banner_html + "\n            <!-- Sorting tabs -->")

    # 3. Add Modal HTML
    modal_html = """
    <!-- Fare Calendar Modal -->
    <div class="modal-overlay" id="fare-calendar-modal" style="z-index: 10500;">
        <div class="modal-content" style="width: 900px; max-width: 95vw; background: white; border-radius: 8px; display: flex; flex-direction: column; max-height: 90vh;">
            <div style="padding: 15px 20px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center;">
                <h2 style="margin: 0; font-size: 18px; color: #0f172a;">Weekly Fare</h2>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="background: #22c55e; color: white; font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 2px;">CHEAPEST</span>
                    <span style="background: #f59e0b; color: white; font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 2px;">MEDIUM</span>
                    <span style="background: #ef4444; color: white; font-size: 10px; font-weight: 800; padding: 2px 6px; border-radius: 2px;">HIGH</span>
                    <i class="fa-solid fa-xmark" style="color: #94a3b8; font-size: 20px; cursor: pointer; margin-left: 15px;" onclick="closeFareCalendar()"></i>
                </div>
            </div>
            
            <div style="padding: 20px; flex: 1; overflow-y: auto;">
                <div style="display: flex; align-items: center; gap: 15px; margin-bottom: 20px;">
                    <span style="font-size: 14px; color: #475569;">Select Preferred Airline:</span>
                    <div style="display: flex; border: 1px solid #cbd5e1; border-radius: 4px; overflow: hidden;">
                        <button style="background: #0284c7; color: white; border: none; padding: 8px 16px; font-size: 14px; font-weight: 600; cursor: pointer;">Any Airline</button>
                        <input type="text" placeholder="+ Airline" style="border: none; padding: 8px 12px; outline: none; border-left: 1px solid #cbd5e1; width: 150px;">
                    </div>
                    <button style="background: #0369a1; color: white; border: none; padding: 8px 24px; border-radius: 4px; font-weight: 600; cursor: pointer;">Find</button>
                </div>
                
                <div style="overflow-x: auto;">
                    <table style="width: 100%; border-collapse: collapse; min-width: 800px; text-align: center; border: 1px solid #e2e8f0; font-size: 12px;">
                        <thead id="fare-calendar-head" style="background: #f8fafc;">
                        </thead>
                        <tbody id="fare-calendar-body">
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
"""
    if 'id="fare-calendar-modal"' not in content:
        # insert before <!-- E-Ticket Modal -->
        content = content.replace("<!-- E-Ticket Modal -->", modal_html + "\n    <!-- E-Ticket Modal -->")

    # 4. Add JS Functions
    js_code = """
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

        function generateFareGrid() {
            const urlParams = new URLSearchParams(window.location.search);
            const baseDepDate = new Date(urlParams.get('date') || new Date());
            const retDateParam = urlParams.get('returnDate');
            let baseRetDate = new Date(baseDepDate);
            if (retDateParam) {
                baseRetDate = new Date(retDateParam);
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
            
            const basePrice = cachedFlights.length > 0 ? cachedFlights[0].price : 175678;
            
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
                    
                    bodyHTML += `<td class="cal-cell" style="padding: 15px; border: 1px solid #e2e8f0; cursor: pointer; transition: background 0.2s; background: white;">
                        <div style="color: ${color}; font-size: 10px;">LKR</div>
                        <div style="color: ${color}; font-weight: 600;">${price.toLocaleString()}</div>
                    </td>`;
                });
                bodyHTML += `</tr>`;
            });
            tbody.innerHTML = bodyHTML;
        }
"""
    if "function openFareCalendar()" not in content:
        content = content.replace("function showSuccessReceipt", js_code + "\n        function showSuccessReceipt")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
        
if __name__ == '__main__':
    patch()
