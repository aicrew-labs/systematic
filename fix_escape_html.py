import re

with open('static/index.html', 'r', encoding='utf-8') as f:
    c = f.read()

replacement = """
        function escapeHtml(unsafe) {
            if (unsafe == null) return '';
            return unsafe.toString()
                 .replace(/&/g, "&amp;")
                 .replace(/</g, "&lt;")
                 .replace(/>/g, "&gt;")
                 .replace(/"/g, "&quot;")
                 .replace(/'/g, "&#039;");
        }
"""

# Replace the first occurrence of // ── State
c = c.replace('// ── State ────────────────────────────────────────────────────────────', replacement + '\n        // ── State ────────────────────────────────────────────────────────────', 1)

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(c)

print('escapeHtml injected.')
