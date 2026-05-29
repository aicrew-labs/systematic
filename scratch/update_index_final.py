import re

file_path = "static/index.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update UserInfo parsing to store the global user object for Feedback modal
init_code = """
        let currentUser = null;
        async function init() {
            // Apply user info
            try {
                const meRes = await fetch('/api/v1/auth/me', { cache: 'no-store' });
                if (meRes.ok) {
                    const user = await meRes.json();
                    currentUser = user;
                    const name = user.full_name || user.user_id;
                    const initials = name.split(' ').map(n => n[0]).join('').substring(0,2).toUpperCase();
                    
                    const ui = document.getElementById('userInitials');
                    if (ui) {
                        ui.textContent = initials;
                        document.getElementById('userFullName').textContent = name;
                        document.getElementById('userIdDisplay').textContent = '@' + user.user_id;
                        document.getElementById('userMenuContainer').style.display = 'block';
                    }
                    const adminBtn = document.getElementById('adminUsersBtn');
                    if (adminBtn && user.role === 'admin') {
                        adminBtn.classList.remove('!hidden');
                    }
                }
            } catch (e) {
                console.error('Failed to parse user info', e);
            }
"""
content = re.sub(r'\s*async function init\(\) \{.*?console\.error\(\'Failed to parse user info\', e\);\n\s*\}', init_code, content, flags=re.DOTALL)


# 2. Update the logout function with animation
logout_js = """
        async function logout() {
            const overlay = document.getElementById('logoutOverlay');
            if (overlay) {
                overlay.classList.remove('hidden');
                overlay.classList.add('flex');
                void overlay.offsetWidth; // trigger reflow
                overlay.classList.remove('opacity-0');
                overlay.classList.add('opacity-100');
            }
            
            try {
                await fetch('/api/v1/auth/logout', { method: 'POST' });
            } catch(e) {}
            
            localStorage.removeItem('sys_user');
            
            setTimeout(() => {
                window.location.href = '/login';
            }, 1200);
        }
"""
content = re.sub(r'\s*async function logout\(\) \{.*?window\.location\.href = \'/login\';\n\s*\}', logout_js, content, flags=re.DOTALL)


# 3. Add logout overlay HTML right after <body>
logout_overlay = """
    <!-- Logout Overlay -->
    <div id="logoutOverlay" class="fixed inset-0 bg-slate-950/90 backdrop-blur-xl z-[999] hidden flex-col items-center justify-center opacity-0 transition-opacity duration-700">
        <div class="relative w-24 h-24 mb-6">
            <div class="absolute inset-0 rounded-full border-4 border-slate-700"></div>
            <div class="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin"></div>
            <div class="absolute inset-0 flex items-center justify-center">
                <svg class="w-8 h-8 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
            </div>
        </div>
        <h2 class="text-2xl font-bold text-white tracking-wide animate-pulse">Signing Out...</h2>
        <p class="text-slate-400 mt-2">See you next time!</p>
    </div>
"""
content = content.replace("<body>", f"<body>{logout_overlay}")


# 4. Replace Feedback modal HTML
feedback_modal_old = """    <!-- Feedback Modal -->
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
    </div>"""

feedback_modal_new = """    <!-- Feedback Modal -->
    <div id="feedbackModal" class="fixed inset-0 bg-slate-900/80 backdrop-blur-sm z-[100] hidden items-center justify-center opacity-0 transition-opacity duration-300">
        <div class="bg-slate-800 border border-slate-700 rounded-2xl p-6 w-full max-w-lg shadow-2xl transform scale-95 transition-transform duration-300" id="feedbackModalContent">
            
            <div class="flex justify-between items-center mb-4">
                <h3 class="text-lg font-semibold text-slate-100 flex items-center gap-2">
                    <svg class="w-5 h-5 text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" /></svg>
                    Your Feedback
                </h3>
                <div id="feedbackStatusBadge" class="hidden px-2.5 py-1 text-xs font-semibold rounded-full border">
                </div>
            </div>

            <form id="feedbackForm" onsubmit="submitFeedback(event)">
                <div class="mb-4">
                    <textarea id="feedbackText" rows="6" class="w-full bg-slate-900/50 border border-slate-700 text-slate-200 text-sm rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors placeholder:text-slate-500" placeholder="Let us know what's on your mind..." required></textarea>
                </div>
                
                <div id="devCommentsSection" class="hidden mb-4 bg-slate-900/60 border border-slate-700/50 rounded-xl p-4">
                    <div class="flex items-center gap-2 mb-2">
                        <svg class="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                        <span class="text-xs font-semibold text-emerald-400 uppercase tracking-wider">Developer Response</span>
                    </div>
                    <p id="devCommentsText" class="text-sm text-slate-300"></p>
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
    </div>"""

if feedback_modal_old in content:
    content = content.replace(feedback_modal_old, feedback_modal_new)
else:
    print("Could not find exact old feedback modal string, falling back to regex")
    content = re.sub(r'    <!-- Feedback Modal -->.*?</div>\s*</div>', feedback_modal_new, content, flags=re.DOTALL)


# 5. Update openFeedbackModal and submitFeedback
feedback_js_old = """        function openFeedbackModal() {
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
        }"""

feedback_js_new = """        function openFeedbackModal() {
            const m = document.getElementById('feedbackModal');
            const c = document.getElementById('feedbackModalContent');
            
            // Prefill with existing feedback if we have it from currentUser
            const fText = document.getElementById('feedbackText');
            const fBadge = document.getElementById('feedbackStatusBadge');
            const devSection = document.getElementById('devCommentsSection');
            const devText = document.getElementById('devCommentsText');
            
            fText.value = '';
            fBadge.className = 'hidden px-2.5 py-1 text-xs font-semibold rounded-full border';
            devSection.classList.add('hidden');
            
            if (currentUser && currentUser.feedback) {
                fText.value = currentUser.feedback;
                
                if (currentUser.feedback_status) {
                    fBadge.classList.remove('hidden');
                    fBadge.textContent = currentUser.feedback_status;
                    if (currentUser.feedback_status === 'Open') {
                        fBadge.classList.add('bg-yellow-500/10', 'text-yellow-400', 'border-yellow-500/20');
                    } else if (currentUser.feedback_status === 'Under Review') {
                        fBadge.classList.add('bg-blue-500/10', 'text-blue-400', 'border-blue-500/20');
                    } else if (currentUser.feedback_status === 'Accepted' || currentUser.feedback_status === 'Deployed/Closed') {
                        fBadge.classList.add('bg-emerald-500/10', 'text-emerald-400', 'border-emerald-500/20');
                    } else if (currentUser.feedback_status === 'Rejected') {
                        fBadge.classList.add('bg-red-500/10', 'text-red-400', 'border-red-500/20');
                    } else {
                        fBadge.classList.add('bg-slate-500/10', 'text-slate-300', 'border-slate-500/20');
                    }
                }
                
                if (currentUser.feedback_dev_comments) {
                    devText.textContent = currentUser.feedback_dev_comments;
                    devSection.classList.remove('hidden');
                }
            }

            m.classList.remove('hidden');
            m.classList.add('flex');
            void m.offsetWidth;
            m.classList.remove('opacity-0');
            m.classList.add('opacity-100');
            c.classList.remove('scale-95');
            c.classList.add('scale-100');
            fText.focus();
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
            btn.innerHTML = 'Saving...';
            btn.disabled = true;

            try {
                const res = await fetch('/api/v1/auth/feedback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ feedback: text })
                });
                if (!res.ok) throw new Error(await res.text());
                
                // Update local user object
                if (currentUser) {
                    currentUser.feedback = text;
                    currentUser.feedback_status = 'Open';
                }
                
                closeFeedbackModal();
                setTimeout(() => alert('Thank you! Your feedback has been saved.'), 350);
            } catch (err) {
                alert('Error saving feedback: ' + err.message);
            } finally {
                btn.innerHTML = ogText;
                btn.disabled = false;
            }
        }"""

if feedback_js_old in content:
    content = content.replace(feedback_js_old, feedback_js_new)
else:
    print("Could not find old JS, falling back to regex")
    content = re.sub(r'        function openFeedbackModal\(\) \{.*?btn\.disabled = false;\n\s*\}', feedback_js_new, content, flags=re.DOTALL)


with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("index.html successfully updated")
