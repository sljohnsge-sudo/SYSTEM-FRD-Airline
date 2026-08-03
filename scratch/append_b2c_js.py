with open(r'd:\GS\SYSTEM-FRD-Airline\static\js\main.js', 'a', encoding='utf-8') as f:
    f.write("""

// ==========================================
// B2C ADMIN PORTAL LOGIC
// ==========================================

function loadAdminB2CUsers() {
    fetch("/api/admin/b2c/users")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const tbody = document.getElementById("admin-b2c-users-table");
                if (!tbody) return;
                tbody.innerHTML = "";
                data.users.forEach(u => {
                    const date = u.registered_at ? u.registered_at.split('T')[0] : 'N/A';
                    tbody.innerHTML += `
                        <tr>
                            <td><strong>${u.username}</strong></td>
                            <td>${u.email}</td>
                            <td>${u.phone || 'N/A'}</td>
                            <td>${date}</td>
                        </tr>
                    `;
                });
            }
        });
}

function loadAdminB2CFees() {
    fetch("/api/admin/b2c/fees/list")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const tbody = document.getElementById("admin-b2c-fees-table");
                if (!tbody) return;
                tbody.innerHTML = "";
                data.fees.forEach(f => {
                    const amountType = f.amount_type || 'fixed';
                    const isFixed = amountType === 'fixed' ? 'selected' : '';
                    const isPct = amountType === 'percentage' ? 'selected' : '';
                    
                    tbody.innerHTML += `
                        <tr>
                            <td><strong style="text-transform:uppercase; color:var(--text-dark, #333);">${f.transaction_type}</strong></td>
                            <td><span class="badge badge-ticketed">${f.fee_type}</span></td>
                            <td>
                                <div style="display: flex; gap: 8px; align-items: center;">
                                    <input type="number" id="b2c-fee-amt-${f.id}" class="form-control" style="width: 130px;" value="${f.amount.toFixed(2)}" min="0">
                                    <select id="b2c-fee-type-${f.id}" class="form-control" style="width: 80px; padding: 5px;">
                                        <option value="fixed" ${isFixed}>$USD</option>
                                        <option value="percentage" ${isPct}>%</option>
                                    </select>
                                </div>
                            </td>
                            <td>
                                <button class="btn-action" style="color: #333;" onclick="updateAdminB2CFee(${f.id})">
                                    <i class="fa-solid fa-floppy-disk"></i> Save Rate
                                </button>
                            </td>
                        </tr>
                    `;
                });
            }
        });
}

function updateAdminB2CFee(id) {
    const val = document.getElementById(`b2c-fee-amt-${id}`).value;
    const typeVal = document.getElementById(`b2c-fee-type-${id}`).value;
    
    if (!val || parseFloat(val) < 0) {
        showNotification("Invalid Entry", "Markup rate cannot be negative.", "danger");
        return;
    }
    
    fetch("/api/admin/b2c/fees/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: id, amount: parseFloat(val), amount_type: typeVal })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showNotification("B2C Markup Applied", data.message, "success");
            loadAdminB2CFees();
        } else {
            showNotification("Update Failed", data.error, "danger");
        }
    });
}

function loadAdminB2CReports() {
    fetch("/api/admin/b2c/bookings")
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                const tbody = document.getElementById("admin-b2c-bookings-table");
                if (!tbody) return;
                tbody.innerHTML = "";
                data.bookings.forEach(b => {
                    const date = b.created_at ? b.created_at.split('T')[0] : 'N/A';
                    let badgeClass = 'badge-pending';
                    if (b.status === 'ticketed' || b.status === 'confirmed') badgeClass = 'badge-ticketed';
                    if (b.status === 'cancelled') badgeClass = 'badge-failed';
                    
                    tbody.innerHTML += `
                        <tr>
                            <td><strong>${b.pnr}</strong></td>
                            <td>User ID: ${b.b2c_user_id}</td>
                            <td style="color:var(--success); font-weight:700;">$${b.total_price.toFixed(2)}</td>
                            <td><span class="badge ${badgeClass}">${b.status.toUpperCase()}</span></td>
                            <td>${date}</td>
                        </tr>
                    `;
                });
            }
        });
}
""")
