import re

with open('static/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_form = '''                    <div class="relative">
                        <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">Customer Name</label>
                        <input type="text" id="custName" class="form-input" placeholder="Search customer..." autocomplete="off" oninput="handleCustomerSearch(event)" onclick="handleCustomerSearch(event)" required>
                        <div id="custDropdown" class="search-dropdown"></div>
                    </div>
                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">State</label>
                            <input type="text" id="custState" class="form-input" placeholder="State">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">City</label>
                            <input type="text" id="custCity" class="form-input" placeholder="City">
                        </div>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">Product Category</label>
                        <div class="select-wrapper">
                            <select id="prodCategory" class="form-select" onchange="updateCustomFields()" required>
                                <option value="">Select Category...</option>
                            </select>
                        </div>
                    </div>
                    
                    <!-- Custom Fields (Hidden by default) -->
                    <div id="customFields" class="hidden space-y-3 p-3 bg-slate-800/50 rounded-xl border border-slate-700">
                        <div class="grid grid-cols-2 gap-3">
                            <div>
                                <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">Steel Type</label>
                                <div class="select-wrapper">
                                    <select id="custSteelType" class="form-select">
                                        <option value="Prime">Prime</option>
                                        <option value="HC">HC</option>
                                        <option value="Commercial">Commercial</option>
                                    </select>
                                </div>
                            </div>
                            <div>
                                <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">Conversion</label>
                                <div class="select-wrapper">
                                    <select id="custConversion" class="form-select">
                                        <option value="Wiping Fine">Wiping Fine</option>
                                        <option value="Wiping Thick">Wiping Thick</option>
                                        <option value="Heavy Fine">Heavy Fine</option>
                                        <option value="Heavy Thick">Heavy Thick</option>
                                        <option value="Printing">Printing</option>
                                        <option value="Stranding">Stranding</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div class="grid grid-cols-2 gap-3">
                            <div>
                                <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">Wire Size (mm)</label>
                                <input type="number" id="custSize" class="form-input" placeholder="e.g. 1.25" step="0.01">
                            </div>
                            <div>
                                <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">GSM</label>
                                <input type="number" id="custGSM" class="form-input" placeholder="e.g. 90" step="0.1">
                            </div>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-3">
                        <div>
                            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">Quantity</label>
                            <input type="number" id="qty" class="form-input" placeholder="e.g. 25" step="0.01" required>
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">Payment Terms</label>
                            <div class="select-wrapper">
                                <select id="payTerms" class="form-select">
                                    <option value="Advance">Advance</option>
                                    <option value="30 Days" selected>30 Days</option>
                                    <option value="45 Days">45 Days</option>
                                    <option value="60 Days">60 Days</option>
                                    <option value="90 Days">90 Days</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-3 pt-2">
                        <button type="button" id="algoBtn" onclick="handleAnalyze('algo')" class="btn-algo w-full rounded-xl font-semibold text-sm text-white flex justify-center items-center gap-2">
                            <svg class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M9 17v-6h13M9 5v6h13M3 7h.01M3 12h.01M3 17h.01"/></svg>
                            Algo Quote
                        </button>
                        <button type="button" id="aiBtn" onclick="handleAnalyze('ai')" class="btn-primary w-full rounded-xl font-semibold text-sm text-white flex justify-center items-center gap-2">
                            <svg class="w-4 h-4 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                            AI Quote
                        </button>
                    </div>
                    <p class="text-[10px] text-slate-500 text-center pt-1">Algo is free for testing. AI uses OpenAI credits.</p>'''

start_marker = '<div class="relative">\n                        <label class="block text-xs font-semibold text-slate-400 uppercase tracking-wide mb-1.5">Customer Name</label>'
end_marker = '<p class="text-[10px] text-slate-500 text-center pt-1">Algo is free for testing. AI uses OpenAI credits.</p>'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_form.strip() + '\n' + content[end_idx + len(end_marker):]
    with open('static/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Form HTML updated.')
else:
    print('Markers not found.')
