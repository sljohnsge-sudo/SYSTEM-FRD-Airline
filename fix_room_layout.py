import os

b2c_home_path = r"d:\GS\SYSTEM-FRD-Airline\templates\b2c_home.html"

with open(b2c_home_path, 'r', encoding='utf-8') as f:
    content = f.read()

old_room_item = """                        roomsHTML += `
                            <div class="b2c-room-item" style="display: flex; gap: 16px; align-items: flex-start; padding: 15px 0; border-top: 1px solid #f1f5f9;">
                                <img src="${roomImg}" style="width: 100px; height: 75px; object-fit: cover; border-radius: 8px; border: 1px solid #cbd5e1;" alt="${r.room_type}">
                                <div style="flex-grow: 1;">
                                    <div class="b2c-room-name" style="font-weight: 700; color: #1e293b; font-size: 15px; margin-bottom: 4px;">${r.room_type}</div>
                                    <div style="margin-bottom: 6px;">
                                        <span style="font-size: 11px; background: #e0f2fe; color: #0284c7; padding: 2px 8px; border-radius: 4px; font-weight: bold; border: 1px solid #bae6fd; display: inline-block;">
                                            <i class="fa-solid fa-percent"></i> Wholesale Rate
                                        </span>
                                    </div>
                                    <div style="display: flex; align-items: center; gap: 4px; margin-top: 6px;">
                                        ${iconsHTML}
                                    </div>
                                </div>
                                <div style="text-align: right; min-width: 150px;">
                                    <div class="b2c-room-price" style="font-size: 20px; font-weight: 800; color: #c3122e;">
                                        LKR ${totalPricePerNight.toLocaleString()}<span class="b2c-room-price-sub" style="font-size: 11px; color: #64748b;">/night</span>
                                    </div>
                                    <div style="font-size: 11px; color: #64748b; margin-bottom: 8px;">
                                        Total (${nights} nts): <strong>LKR ${totalStayPrice.toLocaleString()}</strong>
                                    </div>
                                    <button class="btn-book-room" style="background: #006ce4; color: white; border: none; padding: 8px 18px; border-radius: 20px; font-weight: 700; font-size: 13px; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='#0053b3';" onmouseout="this.style.background='#006ce4';" onclick="bookB2CHotelRoom(${r.id}, '${r.room_type.replace(/'/g, "\\'")}', '${h.name.replace(/'/g, "\\'")}', ${totalPricePerNight}, ${nights}, '${roomImgEscaped}')">Book Room</button>
                                </div>
                            </div>
                        `;"""

new_room_item = """                        roomsHTML += `
                            <div class="b2c-room-item" style="padding: 15px 0; border-top: 1px solid #f1f5f9;">
                                <div style="display: flex; gap: 12px; align-items: flex-start; margin-bottom: 12px;">
                                    <img src="${roomImg}" style="width: 80px; height: 60px; object-fit: cover; border-radius: 8px; border: 1px solid #cbd5e1; flex-shrink: 0;" alt="${r.room_type}">
                                    <div style="flex-grow: 1; min-width: 0;">
                                        <div class="b2c-room-name" style="font-weight: 700; color: #1e293b; font-size: 14px; line-height: 1.2; margin-bottom: 6px; white-space: normal; word-break: break-word;">${r.room_type}</div>
                                        <div style="margin-bottom: 6px;">
                                            <span style="font-size: 10px; background: #e0f2fe; color: #0284c7; padding: 2px 6px; border-radius: 4px; font-weight: bold; border: 1px solid #bae6fd; display: inline-block;">
                                                <i class="fa-solid fa-percent"></i> Wholesale Rate
                                            </span>
                                        </div>
                                        <div style="display: flex; align-items: center; gap: 6px; font-size: 12px;">
                                            ${iconsHTML}
                                        </div>
                                    </div>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: flex-end; background: #f8fafc; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0;">
                                    <div>
                                        <div class="b2c-room-price" style="font-size: 16px; font-weight: 800; color: #c3122e;">
                                            LKR ${totalPricePerNight.toLocaleString()}<span class="b2c-room-price-sub" style="font-size: 10px; color: #64748b;">/nt</span>
                                        </div>
                                        <div style="font-size: 10px; color: #64748b; margin-top: 2px;">
                                            Total (${nights} nts): <strong style="color: #334155;">LKR ${totalStayPrice.toLocaleString()}</strong>
                                        </div>
                                    </div>
                                    <button class="btn-book-room" style="background: #006ce4; color: white; border: none; padding: 8px 16px; border-radius: 20px; font-weight: 700; font-size: 12px; cursor: pointer; transition: background 0.2s;" onmouseover="this.style.background='#0053b3';" onmouseout="this.style.background='#006ce4';" onclick="bookB2CHotelRoom(${r.id}, '${r.room_type.replace(/'/g, "\\'")}', '${h.name.replace(/'/g, "\\'")}', ${totalPricePerNight}, ${nights}, '${roomImgEscaped}')">Book Now</button>
                                </div>
                            </div>
                        `;"""

if old_room_item in content:
    content = content.replace(old_room_item, new_room_item)
    with open(b2c_home_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replaced room item layout successfully.")
else:
    print("Could not find old_room_item block in b2c_home.html")
