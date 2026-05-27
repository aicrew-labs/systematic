import re

with open('static/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

new_js = '''
        // ── Boot ─────────────────────────────────────────────────────────────
        async function init() {
            // Load rates immediately — they appear in the header
            loadRates();

            try {
                const [custResp, catResp] = await Promise.all([
                    fetch('/api/v1/customers'),
                    fetch('/api/v1/config/product-costs'),
                ]);
                if (!custResp.ok || !catResp.ok) throw new Error('API not reachable');

                STATE.customers = await custResp.json();
                STATE.categories = await catResp.json();

                // Populate product category dropdown
                const sel = document.getElementById('prodCategory');
                sel.innerHTML = '<option value="">Select Category...</option>';
                STATE.categories.forEach(c => {
                    const opt = document.createElement('option');
                    opt.value = c.category_id;
                    opt.textContent = c.category_name || c.category_id;
                    // Store the config so we can calculate floor price if selected
                    opt.dataset.config = JSON.stringify(c);
                    sel.appendChild(opt);
                });
                
                // Add custom option
                const custOpt = document.createElement('option');
                custOpt.value = 'Custom';
                custOpt.textContent = 'Custom';
                sel.appendChild(custOpt);

                const badge = document.getElementById('statusBadge');
                badge.textContent = '● Live Data';
                badge.className = 'text-[11px] font-medium text-emerald-400 bg-emerald-400/10 px-2.5 py-1.5 rounded-full border border-emerald-400/20 flex items-center gap-1.5 shrink-0';
            } catch (err) {
                console.error('Init failed:', err);
                const badge = document.getElementById('statusBadge');
                badge.textContent = '● Backend Offline';
                badge.className = 'text-[11px] font-medium text-rose-400 bg-rose-400/10 px-2.5 py-1.5 rounded-full border border-rose-400/20 flex items-center gap-1.5 shrink-0';
            }
        }

        // ── Customer typeahead ───────────────────────────────────────────────
        function handleCustomerSearch(e) {
            const val = e.target.value.toLowerCase();
            const dropdown = document.getElementById('custDropdown');
            dropdown.innerHTML = '';
            const matches = STATE.customers
                .filter(c => c.name.toLowerCase().includes(val))
                .slice(0, 12);
            if (matches.length === 0) { dropdown.classList.remove('active'); return; }
            matches.forEach(c => {
                const div = document.createElement('div');
                div.className = 'search-item flex items-center justify-between';
                const label = c.total_orders > 0 ? `${c.total_orders} orders` : 'New Client';
                div.innerHTML = `<span>${escapeHtml(c.name)}</span><span class="search-item-count">${label}</span>`;
                div.onclick = () => {
                    document.getElementById('custName').value = c.name;
                    // Auto populate state and city if available
                    document.getElementById('custState').value = c.state || '';
                    document.getElementById('custCity').value = c.city || '';
                    STATE.selectedCustomer = c;
                    dropdown.classList.remove('active');
                };
                dropdown.appendChild(div);
            });
            dropdown.classList.add('active');
        }
        document.addEventListener('click', (e) => {
            const dd = document.getElementById('custDropdown');
            const inp = document.getElementById('custName');
            if (!dd.contains(e.target) && e.target !== inp) dd.classList.remove('active');
        });

        // ── Product Category dropdown ────────────────────────────────────────────
        function updateCustomFields() {
            const cat = document.getElementById('prodCategory').value;
            const customDiv = document.getElementById('customFields');
            if (cat === 'Custom') {
                customDiv.classList.remove('hidden');
            } else {
                customDiv.classList.add('hidden');
            }
        }

        // ── Form collapse on mobile ──────────────────────────────────────────
        function toggleForm() {
            const inner = document.getElementById('formInner');
            const btn   = document.getElementById('formToggleBtn');
            const collapsed = inner.classList.toggle('collapsed');
            btn.innerHTML = collapsed
                ? `<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg> Edit Enquiry`
                : `<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/></svg> Close`;
        }

        // Calculate floor price for custom configs purely in JS
        function calculateCustomFloorPrice() {
            let steelRate = _fullRates.prime_steel_rate || 0;
            const sType = document.getElementById('custSteelType').value.toUpperCase();
            if (sType === 'HC') steelRate = _fullRates.hc_steel_rate || 0;
            if (sType === 'COMMERCIAL') steelRate = _fullRates.commercial_steel_rate || 0;
            
            const steelCost = (steelRate / 1000) * 1000; // default 1000 weight
            
            let size = parseFloat(document.getElementById('custSize').value) || 0;
            if (size === 0) size = 1;
            
            const gsm = parseFloat(document.getElementById('custGSM').value) || 0;
            const yieldLossMult = 1 + (25 / 100); // 25% default
            
            const zincWeight = (( gsm / size ) * 0.51) * yieldLossMult;
            const zincRate = _fullRates.zinc_sgh_rate || _fullRates.zinc_rate || 0;
            const zincCost = zincWeight * zincRate;
            
            let convCost = 0;
            const p = (document.getElementById('custConversion').value || "").toLowerCase();
            if (p.includes("wiping fine")) convCost = _fullRates.conv_wiping_fine_rate || 0;
            else if (p.includes("wiping thick")) convCost = _fullRates.conv_wiping_thick_rate || 0;
            else if (p.includes("heavy fine")) convCost = _fullRates.conv_heavy_fine_rate || 0;
            else if (p.includes("heavy thick")) convCost = _fullRates.conv_heavy_thick_rate || 0;
            else if (p.includes("printing")) convCost = _fullRates.conv_printing_rate || 0;
            else if (p.includes("stranding")) convCost = _fullRates.conv_stranding_rate || 0;

            const floor = steelCost + zincCost + convCost;
            
            const steelDisp = `Steel: ₹${Math.round(steelCost).toLocaleString()}`;
            const zincDisp = zincCost > 0 ? `Zinc: ₹${Math.round(zincCost).toLocaleString()}` : "";
            const convDisp = `Conv: ₹${Math.round(convCost).toLocaleString()}`;
            
            const parts = [steelDisp, zincDisp, convDisp].filter(x => x).join(", ") + " (excl. tax & freight)";
            
            return {
                floor_val: `₹${floor.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`,
                floor_sub: parts
            };
        }

        // ── Analyze ──────────────────────────────────────────────────────────
        async function handleAnalyze(mode) {
            const cust = STATE.selectedCustomer;
            const custNameInput = document.getElementById('custName').value;
            const catSel = document.getElementById('prodCategory');
            const catId   = catSel.value;
            const qty         = parseFloat(document.getElementById('qty').value);
            const payTerms    = document.getElementById('payTerms').value;
            
            const custState = document.getElementById('custState').value;
            const custCity = document.getElementById('custCity').value;

            if (!custNameInput) { alert('Please enter a customer name.'); return; }
            if (!catId) { alert('Please select a product category.'); return; }
            if (!qty || qty <= 0) { alert('Please enter a valid quantity.'); return; }

            const algoBtn = document.getElementById('algoBtn');
            const aiBtn   = document.getElementById('aiBtn');
            const empty   = document.getElementById('emptyState');
            const loading = document.getElementById('loadingState');
            const results = document.getElementById('resultsState');

            algoBtn.disabled = true; aiBtn.disabled = true;
            empty.classList.add('hidden');
            results.classList.add('hidden');
            loading.classList.remove('hidden');
            loading.classList.add('flex');
            document.getElementById('loadingTitle').textContent = mode === 'ai' ? 'AI Processing…' : 'Algorithm Processing…';

            const steps = [1, 2, 3].map(i => document.getElementById(`step${i}`));
            steps.forEach(s => { s.className = 'step-item flex items-center gap-3'; s.children[0].innerHTML = ''; });
            steps[0].classList.add('active');
            
            // Collect custom params if Custom
            let customParams = null;
            if (catId === 'Custom') {
                customParams = {
                    steel_type: document.getElementById('custSteelType').value,
                    conversion_process: document.getElementById('custConversion').value,
                    size_mm: parseFloat(document.getElementById('custSize').value) || 0,
                    gsm: parseFloat(document.getElementById('custGSM').value) || 0
                };
            }

            try {
                const respPromise = fetch('/api/v1/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        customer_id: cust ? cust.id : null,
                        customer_name: custNameInput,
                        category_id: catId,
                        quantity: qty,
                        payment_terms: payTerms,
                        state: custState,
                        city: custCity,
                        mode: mode,
                        custom_params: customParams
                    }),
                });

                // Animate steps while request is in flight
                await new Promise(r => setTimeout(r, 350));
                steps[0].classList.replace('active', 'done'); steps[0].children[0].innerHTML = '✓';
                steps[1].classList.add('active');
                await new Promise(r => setTimeout(r, 350));
                steps[1].classList.replace('active', 'done'); steps[1].children[0].innerHTML = '✓';
                steps[2].classList.add('active');

                let data = {};
                
                if (catId === 'Custom') {
                    // Bypass backend history wait somewhat, mostly just render floor
                    // But we still wait for backend to return if we want to show anything else
                    // For custom, the floor price is calculated purely locally.
                    const customFloor = calculateCustomFloorPrice();
                    data = {
                        floor_val: customFloor.floor_val,
                        floor_sub: customFloor.floor_sub,
                        price_range: "N/A",
                        sug_low: null,
                        sug_high: null,
                        signals: [{sign: "check", text: "Custom calculation applied", color: "blue"}]
                    };
                    
                    // We still let the backend return, but we overwrite its floor price info
                    // The backend might return nothing useful for custom, but we hit it anyway
                    const resp = await respPromise;
                    if (resp.ok) {
                        const backData = await resp.json();
                        data.cards = backData.cards || [];
                    }
                } else {
                    const resp = await respPromise;
                    if (!resp.ok) {
                        const detail = await resp.text();
                        throw new Error(`API error ${resp.status}: ${detail}`);
                    }
                    data = await resp.json();
                }

                steps[2].classList.replace('active', 'done'); steps[2].children[0].innerHTML = '✓';
                await new Promise(r => setTimeout(r, 200));

                renderResults(data);

                loading.classList.replace('flex', 'hidden');
                results.classList.remove('hidden');
                results.style.display = 'flex';

                if (window.innerWidth < 1024) {
                    document.getElementById('formInner').classList.add('collapsed');
                    const tBtn = document.getElementById('formToggleBtn');
                    tBtn.classList.add('visible');
                    tBtn.innerHTML = `<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg> Edit Enquiry`;
                    setTimeout(() => document.querySelector('.results-panel').scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);
                }
            } catch (err) {
                alert(err.message);
                steps.forEach(s => s.classList.remove('active', 'done'));
                loading.classList.replace('flex', 'hidden');
                empty.classList.remove('hidden');
            } finally {
                algoBtn.disabled = false; aiBtn.disabled = false;
            }
        }
'''

start_marker = 'async function init() {'
end_marker = 'function renderResults'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

# Need to backtrack start_idx to the beginning of the comment `// ── Boot ───`
boot_comment = '// ── Boot ─────────────────────────────────────────────────────────────\n'
c_idx = content.rfind(boot_comment, 0, start_idx)
if c_idx != -1:
    start_idx = c_idx

if start_idx != -1 and end_idx != -1:
    content = content[:start_idx] + new_js.strip() + '\n\n        ' + content[end_idx:]
    with open('static/index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print('JS HTML updated.')
else:
    print('Markers not found.')
