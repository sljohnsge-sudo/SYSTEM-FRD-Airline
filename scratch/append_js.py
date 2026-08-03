with open(r'd:\GS\SYSTEM-FRD-Airline\static\js\main.js', 'a', encoding='utf-8') as f:
    f.write('''\n
// Toggle Agent Status
function toggleAgentStatus(agentId, newStatus) {
    if (!confirm(`Are you sure you want to ${newStatus === 'active' ? 'activate' : 'deactivate'} this agent?`)) return;
    
    fetch("/api/admin/agents/toggle-status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ agent_id: agentId, status: newStatus })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showNotification("Status Updated", data.message, "success");
            loadAdminAgents();
        } else {
            showNotification("Update Failed", data.error, "danger");
        }
    });
}
''')
