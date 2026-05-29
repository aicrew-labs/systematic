import re

file_path = "c:/Personal/Projects/systematic/systematic/static/index.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace User Menu Container
old_menu = """                <div class="relative group cursor-pointer" id="userMenuContainer" style="display: none;">
                    <button class="text-[12px] font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 h-9 px-3 rounded-xl border border-slate-700 flex items-center gap-2 transition-colors focus:outline-none">
                        <span id="userInfo"></span>
                        <svg class="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-200 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
                        </svg>
                    </button>
                    <!-- Dropdown -->
                    <div class="absolute right-0 mt-1.5 w-40 bg-slate-800 border border-slate-700 rounded-xl shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 overflow-hidden">
                        <div class="py-1">
                            <button onclick="openChangePasswordModal()" class="w-full text-left px-4 py-2 text-[13px] text-slate-300 hover:bg-slate-700 hover:text-white transition-colors">
                                Change Password
                            </button>
                            <button onclick="logout()" class="w-full text-left px-4 py-2 text-[13px] text-red-400 hover:bg-slate-700 hover:text-red-300 transition-colors">
                                Logout
                            </button>
                        </div>
                    </div>
                </div>"""

new_menu = """                <div class="relative group cursor-pointer" id="userMenuContainer" style="display: none;">
                    <!-- Avatar Button -->
                    <button class="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 border border-slate-600/50 flex items-center justify-center text-[13px] font-bold text-white shadow-md hover:ring-2 hover:ring-indigo-400/50 hover:ring-offset-2 hover:ring-offset-slate-900 transition-all focus:outline-none overflow-hidden" id="userAvatarBtn">
                        <span id="userInitials"></span>
                    </button>
                    
                    <!-- Dropdown -->
                    <div class="absolute right-0 mt-2 w-48 bg-slate-800 border border-slate-700/60 rounded-xl shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 overflow-hidden backdrop-blur-md">
                        <!-- User Name Header -->
                        <div class="px-4 py-3 border-b border-slate-700/50 bg-slate-800/80 cursor-default">
                            <p class="text-sm font-semibold text-slate-100 truncate" id="userFullName"></p>
                            <p class="text-[11px] text-slate-400 truncate" id="userIdDisplay"></p>
                        </div>
                        <div class="py-1">
                            <button onclick="alert('Profile functionality coming soon!')" class="w-full text-left px-4 py-2 text-[13px] text-slate-300 hover:bg-slate-700/70 hover:text-white transition-colors flex items-center gap-2">
                                <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" /></svg>
                                Profile
                            </button>
                            <button onclick="openChangePasswordModal()" class="w-full text-left px-4 py-2 text-[13px] text-slate-300 hover:bg-slate-700/70 hover:text-white transition-colors flex items-center gap-2">
                                <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" /></svg>
                                Change Password
                            </button>
                            <button onclick="openFeedbackModal()" class="w-full text-left px-4 py-2 text-[13px] text-slate-300 hover:bg-slate-700/70 hover:text-white transition-colors flex items-center gap-2">
                                <svg class="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
                                Feedback
                            </button>
                        </div>
                        <div class="border-t border-slate-700/50 py-1">
                            <button onclick="logout()" class="w-full text-left px-4 py-2 text-[13px] text-red-400 hover:bg-slate-700/70 hover:text-red-300 transition-colors flex items-center gap-2">
                                <svg class="w-4 h-4 text-red-400/70" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
                                Logout
                            </button>
                        </div>
                    </div>
                </div>"""

content = content.replace(old_menu, new_menu)

# Replace JS logic
old_js = """                    const ui = document.getElementById('userInfo');
                    if (ui) {
                        ui.textContent = user.full_name || user.user_id;
                        document.getElementById('userMenuContainer').style.display = 'block';
                    }"""

new_js = """                    const name = user.full_name || user.user_id;
                    const initials = name.split(' ').map(n => n[0]).join('').substring(0,2).toUpperCase();
                    
                    const ui = document.getElementById('userInitials');
                    if (ui) {
                        ui.textContent = initials;
                        document.getElementById('userFullName').textContent = name;
                        document.getElementById('userIdDisplay').textContent = '@' + user.user_id;
                        document.getElementById('userMenuContainer').style.display = 'block';
                    }"""

content = content.replace(old_js, new_js)

# Insert Feedback Modal before pwdModal
feedback_html = """
    <!-- Feedback Modal -->
    <div id="feedbackModal" class="fixed inset-0 bg-slate-900/80 backdrop-blur-sm z-[100] hidden items-center justify-center opacity-0 transition-opacity duration-300">
        <div class="bg-slate-800 border border-slate-700 rounded-2xl p-6 w-full max-w-md shadow-2xl transform scale-95 transition-transform duration-300" id="feedbackModalContent">
            <h3 class="text-lg font-semibold mb-4 text-slate-100 flex items-center gap-2">
                <svg class="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
                Send Feedback
            </h3>
            <p class="text-sm text-slate-400 mb-4">Your feedback helps us improve Systematic Quote Intelligence. What's on your mind?</p>
            <form id="feedbackForm" onsubmit="submitFeedback(event)">
                <div class="mb-4">
                    <textarea id="feedbackText" rows="6" class="w-full bg-slate-900/50 border border-slate-700 text-slate-200 text-sm rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors placeholder:text-slate-500" placeholder="I would love it if..." required></textarea>
                </div>
                <div class="flex justify-end gap-3">
                    <button type="button" onclick="closeFeedbackModal()" class="px-4 py-2 text-sm font-medium text-slate-400 hover:text-slate-200 transition-colors">
                        Cancel
                    </button>
                    <button type="submit" id="feedbackBtn" class="px-5 py-2 text-sm font-medium text-white bg-indigo-600 rounded-xl hover:bg-indigo-500 transition-colors flex items-center gap-2">
                        Submit
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
                    </button>
                </div>
            </form>
        </div>
    </div>

    <script>
        function openFeedbackModal() {
            const m = document.getElementById('feedbackModal');
            const c = document.getElementById('feedbackModalContent');
            document.getElementById('feedbackText').value = '';
            m.classList.remove('hidden');
            m.classList.add('flex');
            // trigger reflow
            void m.offsetWidth;
            m.classList.remove('opacity-0');
            m.classList.add('opacity-100');
            c.classList.remove('scale-95');
            c.classList.add('scale-100');
            document.getElementById('feedbackText').focus();
        }

        function closeFeedbackModal() {
            const m = document.getElementById('feedbackModal');
            const c = document.getElementById('feedbackModalContent');
            m.classList.remove('opacity-100');
            m.classList.add('opacity-0');
            c.classList.remove('scale-100');
            c.classList.add('scale-95');
            setTimeout(() => {
                m.classList.remove('flex');
                m.classList.add('hidden');
            }, 300);
        }

        async function submitFeedback(e) {
            e.preventDefault();
            const text = document.getElementById('feedbackText').value;
            const btn = document.getElementById('feedbackBtn');
            const ogText = btn.innerHTML;
            btn.innerHTML = 'Sending...';
            btn.disabled = true;

            try {
                const res = await fetch('/api/v1/auth/feedback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ feedback: text })
                });
                if (!res.ok) throw new Error(await res.text());
                closeFeedbackModal();
                setTimeout(() => alert('Thank you! Your feedback has been saved.'), 350);
            } catch (err) {
                alert('Error saving feedback: ' + err.message);
            } finally {
                btn.innerHTML = ogText;
                btn.disabled = false;
            }
        }
    </script>
"""

content = content.replace("    <!-- Change Password Modal -->", feedback_html + "\n    <!-- Change Password Modal -->")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated index.html successfully.")
