import re

with open('static/index.html', 'r', encoding='utf-8') as f:
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

# Add logout button next to setup button
if 'logout()' not in content:
    setup_btn_end = '</svg>\\n                </a>'
    logout_btn = '''</svg>
                </a>
                
                <button onclick="logout()" class="btn-setup" aria-label="Logout" style="background: rgba(220, 38, 38, 0.2); margin-left: 8px;">
                    <svg fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2" class="text-red-400">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                    </svg>
                </button>'''
    content = content.replace(setup_btn_end, logout_btn, 1)

# Add getAuthHeaders and logout functions
if 'function getAuthHeaders()' not in content:
    content = content.replace('let customersData = [];', '''
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

        let customersData = [];''', 1)

# Update fetch API calls
content = re.sub(r"fetch\(['\"`]/api/v1/customers['\"`]\)", "fetch('/api/v1/customers', { headers: getAuthHeaders() })", content)
content = re.sub(r"fetch\(['\"`]/api/v1/products['\"`]\)", "fetch('/api/v1/products', { headers: getAuthHeaders() })", content)
content = re.sub(r"fetch\(['\"`]/api/v1/rates['\"`]\)", "fetch('/api/v1/rates', { headers: getAuthHeaders() })", content)
content = re.sub(r"fetch\(['\"`]/api/v1/locations['\"`]\)", "fetch('/api/v1/locations', { headers: getAuthHeaders() })", content)

# POST /api/v1/rates
post_rates = """fetch('/api/v1/rates', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },"""
new_post_rates = """fetch('/api/v1/rates', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },"""
content = content.replace(post_rates, new_post_rates)

# POST /api/v1/analyze
post_analyze = """fetch('/api/v1/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },"""
new_post_analyze = """fetch('/api/v1/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },"""
content = content.replace(post_analyze, new_post_analyze)

# Add logout logic on 401s
if 'if (resp.status === 401) return logout();' not in content:
    content = content.replace('if (!resp.ok)', 'if (resp.status === 401) return logout();\\n                if (!resp.ok)')
    content = content.replace('if (!res.ok)', 'if (res.status === 401) return logout();\\n                if (!res.ok)')

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Updated static/index.html")
