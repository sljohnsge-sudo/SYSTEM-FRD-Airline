with open(r'd:\GS\SYSTEM-FRD-Airline\templates\admin_dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Replace the sidebar with B2C specific links
sidebar_start = html.find('<nav class="sidebar-menu">')
sidebar_end = html.find('</aside>')
sidebar_content = '''<nav class="sidebar-menu">
                <a class="menu-item active" onclick="switchB2CAdminTab('b2c-users')">
                    <i class="fa-solid fa-user-tag"></i>
                    <span>B2C Users</span>
                </a>
                <a class="menu-item" onclick="switchB2CAdminTab('b2c-fees')">
                    <i class="fa-solid fa-hand-holding-dollar"></i>
                    <span>B2C Fee Config</span>
                </a>
                <a class="menu-item" onclick="switchB2CAdminTab('b2c-reports')">
                    <i class="fa-solid fa-file-contract"></i>
                    <span>B2C Reports</span>
                </a>
                <div style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;">
                    <a href="/logout" class="menu-item" style="color: #ff6b6b;">
                        <i class="fa-solid fa-right-from-bracket"></i>
                        <span>Logout Account</span>
                    </a>
                </div>
            </nav>
            <div class="sidebar-footer">
                <div class="user-profile">
                    <div class="profile-avatar" style="background: #e11d48;">
                        {{ admin.username[0].upper() }}
                    </div>
                    <div class="profile-info">
                        <div class="profile-name">{{ admin.company_name }}</div>
                        <div class="profile-role">B2C Administrator</div>
                    </div>
                </div>
            </div>
            '''
html = html[:sidebar_start] + sidebar_content + html[sidebar_end:]

# Replace header
header_target = '''<h1>ATL System Administrator</h1>
                    <p>Manage B2B contracts, adjust service fees, and evaluate transaction reports.</p>'''
header_replacement = '''<h1>ATL B2C System Administrator</h1>
                    <p>Manage B2C users, public markups, and evaluate B2C booking reports.</p>'''
html = html.replace(header_target, header_replacement)

# Remove the B2B Tabs from the HTML content
b2c_tab_start = html.find('<!-- TAB: B2C USERS -->')
tab_dashboard_start = html.find('<!-- TAB: ADMIN DASHBOARD OVERVIEW -->')
if b2c_tab_start != -1 and tab_dashboard_start != -1:
    html = html[:tab_dashboard_start] + html[b2c_tab_start:]

# Change the first b2c tab to active
html = html.replace('class="tab-content-panel"', 'class="tab-content-panel active"', 1)

# Add B2C JS logic at the bottom
js_target = '</body>'
js_replacement = '''
    <script>
        function switchB2CAdminTab(tabId) {
            document.querySelectorAll(".menu-item").forEach(item => item.classList.remove("active"));
            document.querySelectorAll(".tab-content-panel").forEach(panel => panel.classList.remove("active"));
            
            event.currentTarget.classList.add("active");
            document.getElementById(`tab-${tabId}`).classList.add("active");
            
            if (tabId === "b2c-users") loadAdminB2CUsers();
            else if (tabId === "b2c-fees") loadAdminB2CFees();
            else if (tabId === "b2c-reports") loadAdminB2CReports();
        }
        
        // Initial Load
        document.addEventListener('DOMContentLoaded', () => {
            loadAdminB2CUsers();
        });
    </script>
</body>'''
html = html.replace(js_target, js_replacement)

with open(r'd:\GS\SYSTEM-FRD-Airline\templates\b2c_admin_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("b2c_admin_dashboard.html created.")
