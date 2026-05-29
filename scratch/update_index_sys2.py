import re

file_path = "static/index.html"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Update feedback form HTML to include a select dropdown for status
old_html = r"""            <form id="feedbackForm" onsubmit="submitFeedback\(event\)">
                <div class="mb-4">
                    <textarea id="feedbackText" rows="6" class="w-full bg-slate-900/50 border border-slate-700 text-slate-200 text-sm rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors placeholder:text-slate-500" placeholder="Let us know what's on your mind..." required></textarea>
                </div>"""

new_html = """            <form id="feedbackForm" onsubmit="submitFeedback(event)">
                <div class="mb-4">
                    <textarea id="feedbackText" rows="6" class="w-full bg-slate-900/50 border border-slate-700 text-slate-200 text-sm rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors placeholder:text-slate-500" placeholder="Let us know what's on your mind..." required></textarea>
                </div>
                
                <div class="mb-4">
                    <label class="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">Status</label>
                    <select id="feedbackStatusSelect" class="w-full bg-slate-900/50 border border-slate-700 text-slate-200 text-sm rounded-xl px-4 py-3 focus:outline-none focus:border-indigo-500 transition-colors appearance-none cursor-pointer">
                        <option value="Open">Open</option>
                        <option value="Under Review">Under Review</option>
                        <option value="Accepted">Accepted</option>
                        <option value="Rejected">Rejected</option>
                        <option value="Deployed/Closed">Deployed/Closed</option>
                    </select>
                </div>"""

content = re.sub(old_html, new_html, content, flags=re.DOTALL)


# Update JS logic to handle the select dropdown
old_js = r"""        function openFeedbackModal\(\) \{
            const m = document\.getElementById\('feedbackModal'\);
            const c = document\.getElementById\('feedbackModalContent'\);
            
            // Prefill with existing feedback if we have it from currentUser
            const fText = document\.getElementById\('feedbackText'\);
            const fBadge = document\.getElementById\('feedbackStatusBadge'\);
            const devSection = document\.getElementById\('devCommentsSection'\);
            const devText = document\.getElementById\('devCommentsText'\);
            
            fText\.value = '';
            fBadge\.className = 'hidden px-2\.5 py-1 text-xs font-semibold rounded-full border';
            devSection\.classList\.add\('hidden'\);
            
            if \(currentUser && currentUser\.feedback\) \{
                fText\.value = currentUser\.feedback;
                
                if \(currentUser\.feedback_status\) \{
                    fBadge\.classList\.remove\('hidden'\);
                    fBadge\.textContent = currentUser\.feedback_status;"""

new_js = """        function openFeedbackModal() {
            const m = document.getElementById('feedbackModal');
            const c = document.getElementById('feedbackModalContent');
            
            // Prefill with existing feedback if we have it from currentUser
            const fText = document.getElementById('feedbackText');
            const fBadge = document.getElementById('feedbackStatusBadge');
            const devSection = document.getElementById('devCommentsSection');
            const devText = document.getElementById('devCommentsText');
            const fSelect = document.getElementById('feedbackStatusSelect');
            
            fText.value = '';
            fSelect.value = 'Open'; // default
            fBadge.className = 'hidden px-2.5 py-1 text-xs font-semibold rounded-full border';
            devSection.classList.add('hidden');
            
            if (currentUser && currentUser.feedback) {
                fText.value = currentUser.feedback;
                
                if (currentUser.feedback_status) {
                    fSelect.value = currentUser.feedback_status;
                    fBadge.classList.remove('hidden');
                    fBadge.textContent = currentUser.feedback_status;"""

content = re.sub(old_js, new_js, content, flags=re.DOTALL)


old_submit = r"""        async function submitFeedback\(e\) \{
            e\.preventDefault\(\);
            const text = document\.getElementById\('feedbackText'\)\.value;
            const btn = document\.getElementById\('feedbackBtn'\);
            const ogText = btn\.innerHTML;
            btn\.innerHTML = 'Saving\.\.\.';
            btn\.disabled = true;

            try \{
                const res = await fetch\('/api/v1/auth/feedback', \{
                    method: 'POST',
                    headers: \{ 'Content-Type': 'application/json' \},
                    body: JSON\.stringify\(\{ feedback: text \}\)
                \}\);
                if \(!res\.ok\) throw new Error\(await res\.text\(\)\);
                
                // Update local user object
                if \(currentUser\) \{
                    currentUser\.feedback = text;
                    currentUser\.feedback_status = 'Open';
                \}"""

new_submit = """        async function submitFeedback(e) {
            e.preventDefault();
            const text = document.getElementById('feedbackText').value;
            const statusVal = document.getElementById('feedbackStatusSelect').value;
            const btn = document.getElementById('feedbackBtn');
            const ogText = btn.innerHTML;
            btn.innerHTML = 'Saving...';
            btn.disabled = true;

            try {
                const res = await fetch('/api/v1/auth/feedback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ feedback: text, status: statusVal })
                });
                if (!res.ok) throw new Error(await res.text());
                
                // Update local user object
                if (currentUser) {
                    currentUser.feedback = text;
                    currentUser.feedback_status = statusVal;
                }"""

content = re.sub(old_submit, new_submit, content, flags=re.DOTALL)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated index.html")
