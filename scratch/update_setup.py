import re

with open('backend/rewrite_setup.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add auth check at the very top of <head>
if "const token = localStorage.getItem('sys_access_token');" not in content:
    content = content.replace('<head>', '''<head>
    <script>
        // Auth Check
        const token = localStorage.getItem('sys_access_token');
        if (!token) {
            window.location.href = '/login';
        }
    </script>''', 1)

# Add logout button
if 'logout()' not in content:
    dashboard_btn = '''<a href="/" class="btn btn-secondary flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18"/></svg>
                        Back to Dashboard
                    </a>'''
    logout_btn = '''<button onclick="logout()" class="btn btn-secondary flex items-center gap-2" style="background: rgba(220, 38, 38, 0.2); color: #fca5a5; border-color: rgba(220,38,38,0.3);">
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
                        Logout
                    </button>'''
    content = content.replace(dashboard_btn, dashboard_btn + '\\n                    ' + logout_btn, 1)

# Add getAuthHeaders and logout to script
if 'function getAuthHeaders()' not in content:
    content = content.replace('let allConfigs = [];', '''
        function getAuthHeaders() {
            const token = localStorage.getItem('sys_access_token');
            if (!token) {
                window.location.href = '/login';
                return {};
            }
            return {
                'Authorization': `Bearer ${token}`
            };
        }

        function logout() {
            localStorage.removeItem('sys_access_token');
            localStorage.removeItem('sys_user');
            window.location.href = '/login';
        }

        let allConfigs = [];''', 1)

# Update fetch calls
content = re.sub(r"fetch\(['\"`]/api/v1/config/product-costs['\"`]\)", "fetch('/api/v1/config/product-costs', { headers: getAuthHeaders() })", content)
content = re.sub(r"fetch\(['\"`]/api/v1/rates/history\?days=\$\{days\}['\"`]\)", "fetch(`/api/v1/rates/history?days=${days}`, { headers: getAuthHeaders() })", content)
content = re.sub(r"fetch\(['\"`]/api/v1/rates['\"`]\)", "fetch('/api/v1/rates', { headers: getAuthHeaders() })", content)

# update save config fetch
post_config = """fetch('/api/v1/config/product-costs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },"""
new_post_config = """fetch('/api/v1/config/product-costs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },"""
content = content.replace(post_config, new_post_config)

# update delete config fetch
delete_config = """fetch(`/api/v1/config/product-costs/${id}`, {
                    method: 'DELETE'
                });"""
new_delete_config = """fetch(`/api/v1/config/product-costs/${id}`, {
                    method: 'DELETE',
                    headers: getAuthHeaders()
                });"""
content = content.replace(delete_config, new_delete_config)

# Add 401 handling globally
if 'if (res.status === 401) return logout();' not in content:
    content = content.replace('if (!res.ok)', 'if (res.status === 401) return logout();\\n                if (!res.ok)')

with open('backend/rewrite_setup.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated backend/rewrite_setup.py")
