with open(r'd:\GS\SYSTEM-FRD-Airline\templates\admin_dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Add Sidebar items
sidebar_target = '''                <div style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;">
                    <a href="{{ url_for('index') }}" class="menu-item">'''

sidebar_replacement = '''                <div style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px; padding-bottom: 5px;">
                    <div style="font-size: 11px; text-transform: uppercase; color: rgba(255,255,255,0.5); margin-bottom: 5px; padding-left: 20px; font-weight: bold;">B2C Configuration</div>
                    <a class="menu-item" onclick="switchAdminTab('b2c-users')">
                        <i class="fa-solid fa-user-tag"></i>
                        <span>B2C Users</span>
                    </a>
                    <a class="menu-item" onclick="switchAdminTab('b2c-fees')">
                        <i class="fa-solid fa-hand-holding-dollar"></i>
                        <span>B2C Fee Config</span>
                    </a>
                    <a class="menu-item" onclick="switchAdminTab('b2c-reports')">
                        <i class="fa-solid fa-file-contract"></i>
                        <span>B2C Reports</span>
                    </a>
                </div>
                <div style="margin-top: 10px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;">
                    <a href="{{ url_for('index') }}" class="menu-item">'''

html = html.replace(sidebar_target, sidebar_replacement)

# 2. Add Tab content sections
tab_target = '''            <!-- Modals -->'''

tab_replacement = '''            <!-- ========================================================= -->
            <!-- TAB: B2C USERS -->
            <!-- ========================================================= -->
            <section id="tab-b2c-users" class="tab-content-panel">
                <div class="content-card">
                    <div class="card-header">
                        <div class="card-title">
                            <i class="fa-solid fa-user-tag"></i>
                            <span>B2C Registered Users</span>
                        </div>
                    </div>
                    <div class="table-responsive">
                        <table class="custom-table" style="font-size:13px;">
                            <thead>
                                <tr>
                                    <th>Username</th>
                                    <th>Email</th>
                                    <th>Phone</th>
                                    <th>Registered Date</th>
                                </tr>
                            </thead>
                            <tbody id="admin-b2c-users-table">
                                <!-- Loaded dynamically -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            <!-- ========================================================= -->
            <!-- TAB: B2C FEE CONFIGURATION -->
            <!-- ========================================================= -->
            <section id="tab-b2c-fees" class="tab-content-panel">
                <div class="content-card">
                    <div class="card-header">
                        <div class="card-title">
                            <i class="fa-solid fa-hand-holding-dollar"></i>
                            <span>B2C Fee & Markup Configuration</span>
                        </div>
                    </div>
                    <div class="table-responsive">
                        <table class="custom-table" style="font-size:13px;">
                            <thead>
                                <tr>
                                    <th>Transaction Type</th>
                                    <th>Fee Scope</th>
                                    <th>Fee Amount</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="admin-b2c-fees-table">
                                <!-- Loaded dynamically -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            <!-- ========================================================= -->
            <!-- TAB: B2C REPORTS -->
            <!-- ========================================================= -->
            <section id="tab-b2c-reports" class="tab-content-panel">
                <div class="content-card">
                    <div class="card-header">
                        <div class="card-title">
                            <i class="fa-solid fa-file-contract"></i>
                            <span>B2C Flight Bookings</span>
                        </div>
                    </div>
                    <div class="table-responsive">
                        <table class="custom-table" style="font-size:13px;">
                            <thead>
                                <tr>
                                    <th>PNR</th>
                                    <th>User ID</th>
                                    <th>Total Price</th>
                                    <th>Status</th>
                                    <th>Booking Date</th>
                                </tr>
                            </thead>
                            <tbody id="admin-b2c-bookings-table">
                                <!-- Loaded dynamically -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </section>

            <!-- Modals -->'''

html = html.replace(tab_target, tab_replacement)

with open(r'd:\GS\SYSTEM-FRD-Airline\templates\admin_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("admin_dashboard.html updated successfully")
