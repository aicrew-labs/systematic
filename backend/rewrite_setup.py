import os

HTML_CONTENT = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Quote Intelligence - Setup</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
    <style>
        body { background: #0f172a; color: #f1f5f9; font-family: 'Inter', system-ui, -apple-system, sans-serif; }
        .glass { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(16px); border: 1px solid rgba(255, 255, 255, 0.05); }
        .glass-card { background: rgba(30,41,59,0.7); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px); border: 1px solid rgba(148,163,184,0.15); border-radius: 16px; }
        .btn { padding: 8px 16px; border-radius: 8px; font-weight: 600; cursor: pointer; transition: all 0.2s; font-size: 13px; }
        .btn-primary { background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; border: none; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3); }
        .btn-primary:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(99, 102, 241, 0.4); }
        .btn-secondary { background: rgba(51, 65, 85, 0.5); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.2); }
        .btn-secondary:hover { background: rgba(71, 85, 105, 0.7); color: white; }
        .btn-green { background: linear-gradient(135deg, #10b981, #059669); color: white; border: none; box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3); }
        .btn-green:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4); }
        .input-field { width: 100%; padding: 8px 12px; background: rgba(15, 23, 42, 0.6); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 6px; color: white; font-size: 13px; transition: all 0.2s; }
        .input-field:focus { outline: none; border-color: #6366f1; box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2); }
        label { display: block; font-size: 11px; font-weight: 600; color: #94a3b8; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.05em; }
        
        .table-container { overflow-x: auto; border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.05); }
        table { width: 100%; border-collapse: collapse; text-align: left; font-size: 13px; }
        th { background: rgba(15, 23, 42, 0.8); padding: 12px 16px; font-weight: 600; color: #cbd5e1; border-bottom: 1px solid rgba(255, 255, 255, 0.05); white-space: nowrap; }
        td { padding: 12px 16px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); color: #f1f5f9; }
        tr:hover td { background: rgba(51, 65, 85, 0.3); }
        .row-action { color: #6366f1; font-weight: 600; cursor: pointer; }
        .row-action:hover { color: #818cf8; text-decoration: underline; }
        
        /* Modal */
        #editModal { display: none; position: fixed; inset: 0; background: rgba(15, 23, 42, 0.8); backdrop-filter: blur(4px); z-index: 50; align-items: center; justify-content: center; }
        #editModal.open { display: flex; animation: fadeIn 0.2s ease-out forwards; }
        .modal-content { background: #1e293b; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; width: 100%; max-width: 700px; max-height: 90vh; overflow-y: auto; padding: 24px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5); transform: scale(0.95); opacity: 0; }
        #editModal.open .modal-content { animation: slideUp 0.3s ease-out forwards; }
        
        @keyframes fadeIn { to { opacity: 1; } }
        @keyframes slideUp { to { transform: scale(1); opacity: 1; } }

        /* Rates bar */
        .rates-bar { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; flex: 1; justify-content: center; }
        @media (min-width: 1024px) { .rates-bar { flex-wrap: nowrap; gap: 8px; } }

        .rate-field { display: flex; flex-direction: column; align-items: flex-start; min-width: 100px; }
        .rate-field label { font-size: 9px; font-weight: 600; letter-spacing: .06em; text-transform: uppercase; color: #94a3b8; margin-bottom: 2px; white-space: nowrap; }
        .rate-input-wrap { position: relative; display: flex; align-items: center; }
        .rate-input-wrap .rate-prefix { position: absolute; left: 8px; font-size: 11px; color: #64748b; pointer-events: none; font-weight: 600; }
        .rate-input { width: 108px; padding: 5px 8px 5px 18px; background: rgba(15,23,42,.85); border: 1px solid rgba(148,163,184,.2); border-radius: 8px; color: #f1f5f9; font-size: 12px; font-weight: 600; outline: none; transition: border-color .2s, box-shadow .2s; -moz-appearance: textfield; }
        .rate-input::-webkit-inner-spin-button, .rate-input::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
        .rate-input:focus { border-color: #6366f1; box-shadow: 0 0 0 2px rgba(99,102,241,.18); }
        .rate-input.rate-edited { border-color: #f59e0b; box-shadow: 0 0 0 2px rgba(245,158,11,.12); color: #fbbf24; }

        .rate-divider { width: 1px; height: 32px; background: rgba(148,163,184,.12); flex-shrink: 0; display: none; }
        @media (min-width: 1024px) { .rate-divider { display: block; } }

        .btn-confirm { display: flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: 9px; font-size: 12px; font-weight: 700; white-space: nowrap; cursor: pointer; transition: all .25s; min-height: 32px; border: none; flex-shrink: 0;
            background: linear-gradient(135deg, #10b981, #059669); color: #fff; box-shadow: 0 2px 12px rgba(16,185,129,.2); }
        .btn-confirm:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 18px rgba(16,185,129,.35); }
        .btn-confirm:active:not(:disabled) { transform: scale(.97); }
        .btn-confirm:disabled { opacity: .5; cursor: not-allowed; }
        .btn-confirm.saving { background: linear-gradient(135deg, #6366f1, #8b5cf6); }
        .btn-confirm.saved  { background: linear-gradient(135deg, #10b981, #14b8a6); }

        .rate-as-of { font-size: 9px; color: #475569; white-space: nowrap; text-align: center; flex-shrink: 0; }
    </style>
</head>
<body class="min-h-screen flex flex-col relative pb-10" onload="init()">
    
    <!-- Header -->
    <header class="border-b border-slate-800/50 glass sticky top-0 z-40">
        <div class="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
            <div class="flex items-center gap-3">
                <a href="/static/index.html" class="w-9 h-9 rounded-xl bg-slate-800 flex items-center justify-center hover:bg-slate-700 transition" aria-label="Back to Dashboard">
                    <svg class="w-5 h-5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7"/></svg>
                </a>
                <div>
                    <h1 class="text-sm font-bold text-white tracking-tight">Setup</h1>
                    <p class="text-[10px] text-slate-400">Quote Intelligence</p>
                </div>
            </div>

            <!-- Commodity Rates Bar -->
            <div class="rates-bar">
                <!-- Prime Steel -->
                <div class="rate-field">
                    <label for="ratePrime">Prime Steel ₹/MT</label>
                    <div class="rate-input-wrap">
                        <span class="rate-prefix">₹</span>
                        <input type="number" id="ratePrime" class="rate-input" placeholder="52000" step="100" oninput="onRateEdit(this)" aria-label="Prime Steel price per MT">
                    </div>
                </div>
                <div class="rate-divider"></div>
                <!-- HC Steel -->
                <div class="rate-field">
                    <label for="rateHC">HC Steel ₹/MT</label>
                    <div class="rate-input-wrap">
                        <span class="rate-prefix">₹</span>
                        <input type="number" id="rateHC" class="rate-input" placeholder="67000" step="100" oninput="onRateEdit(this)" aria-label="HC Steel price per MT">
                    </div>
                </div>
                <div class="rate-divider"></div>
                <!-- Commercial Steel -->
                <div class="rate-field">
                    <label for="rateComm">Comm Steel ₹/MT</label>
                    <div class="rate-input-wrap">
                        <span class="rate-prefix">₹</span>
                        <input type="number" id="rateComm" class="rate-input" placeholder="50000" step="100" oninput="onRateEdit(this)" aria-label="Commercial Steel price per MT">
                    </div>
                </div>
                <div class="rate-divider"></div>
                <!-- Zinc SHG -->
                <div class="rate-field">
                    <label for="rateZincSHG">Zinc SHG ₹/kg</label>
                    <div class="rate-input-wrap">
                        <span class="rate-prefix">₹</span>
                        <input type="number" id="rateZincSHG" class="rate-input" placeholder="260" step="1" oninput="onRateEdit(this)" aria-label="Zinc price per kg">
                    </div>
                </div>
                <div class="rate-divider"></div>
                <!-- Confirm button + as-of label -->
                <div class="flex flex-col items-center gap-1">
                    <button id="confirmRatesBtn" class="btn-confirm" onclick="confirmRates()" disabled>
                        <svg class="w-3.5 h-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5"/></svg>
                        Confirm
                    </button>
                    <span id="rateAsOf" class="rate-as-of">Loading…</span>
                </div>
            </div>

        </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto w-full px-4 mt-8 flex-1 flex flex-col gap-8">
        
        <!-- Charts Section -->
        <div>
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-lg font-bold text-white">Commodity Price Trends</h2>
                <select id="timeframeSelect" class="input-field !w-auto" onchange="loadRateHistory()">
                    <option value="7">Last 7 Days</option>
                    <option value="14">Last 14 Days</option>
                    <option value="30" selected>Last 30 Days</option>
                    <option value="90">Last 90 Days</option>
                </select>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="glass-card p-4">
                    <h3 class="text-sm font-semibold text-slate-300 mb-2">Steel Rates (₹/MT)</h3>
                    <div class="relative h-48 w-full"><canvas id="steelChart"></canvas></div>
                </div>
                <div class="glass-card p-4">
                    <h3 class="text-sm font-semibold text-slate-300 mb-2">Zinc Rates (₹/kg)</h3>
                    <div class="relative h-48 w-full"><canvas id="zincChart"></canvas></div>
                </div>
            </div>
        </div>

        <!-- Table Section: Product Cost Config -->
        <div>
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-lg font-bold text-white">Product Cost Configurations</h2>
                <div class="flex items-center gap-3">
                    <input type="text" id="searchInput" class="input-field" placeholder="Search categories..." oninput="renderTable()" style="width: 250px; background: rgba(15, 23, 42, 0.4); margin-bottom: 0;">
                    
                    <label class="btn btn-green flex items-center gap-2 cursor-pointer">
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                        Upload Excel
                        <input type="file" class="hidden" accept=".xlsx, .xls" onchange="handleConfigUpload(event)">
                    </label>

                    <button class="btn btn-primary flex items-center gap-2" onclick="openModal()">
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4"/></svg>
                        Add Category
                    </button>
                </div>
            </div>
            <div class="glass table-container">
                <table id="configTable">
                    <thead>
                        <tr>
                            <th>Category ID</th>
                            <th>Name</th>
                            <th>Size (Min-Max)</th>
                            <th>GSM</th>
                            <th>Steel Type</th>
                            <th>Conversion Process</th>
                            <th>Yield Loss %</th>
                            <th>Floor Price (₹/MT)</th>
                            <th>Margin %</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="configTableBody">
                        <tr><td colspan="10" class="text-center py-8 text-slate-400">Loading configurations...</td></tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Table Section: Daily Rates -->
        <div>
            <div class="flex items-center justify-between mb-4">
                <h2 class="text-lg font-bold text-white">Daily Conversion & Additional Rates</h2>
                <div class="flex items-center gap-3">
                    <label class="btn btn-green flex items-center gap-2 cursor-pointer">
                        <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/></svg>
                        Upload Excel
                        <input type="file" class="hidden" accept=".xlsx, .xls" onchange="handleRatesUpload(event)">
                    </label>
                </div>
            </div>
            
            <div class="glass-card p-6">
                <form id="dailyRatesForm" onsubmit="saveAllDailyRates(event)" class="grid grid-cols-1 md:grid-cols-3 gap-6">
                    
                    <div class="space-y-4">
                        <h3 class="text-sm font-semibold text-indigo-400 border-b border-slate-700 pb-2">Steel & Zinc</h3>
                        <div>
                            <label>Prime Steel ₹/MT</label>
                            <input type="number" id="dr_prime" class="input-field" step="100" required>
                        </div>
                        <div>
                            <label>HC Steel ₹/MT</label>
                            <input type="number" id="dr_hc" class="input-field" step="100" required>
                        </div>
                        <div>
                            <label>Commercial Steel ₹/MT</label>
                            <input type="number" id="dr_comm" class="input-field" step="100" required>
                        </div>
                        <div>
                            <label>Zinc SHG ₹/kg</label>
                            <input type="number" id="dr_zinc_shg" class="input-field" step="1" required>
                        </div>
                        <div>
                            <label>Zinc (General) ₹/kg</label>
                            <input type="number" id="dr_zinc" class="input-field" step="1" required>
                        </div>
                        <div>
                            <label>Wire Rod Rate ₹/MT</label>
                            <input type="number" id="dr_wire_rod" class="input-field" step="10" required>
                        </div>
                    </div>

                    <div class="space-y-4">
                        <h3 class="text-sm font-semibold text-emerald-400 border-b border-slate-700 pb-2">Conversion Rates</h3>
                        <div>
                            <label>Wiping Fine ₹/MT</label>
                            <input type="number" id="dr_conv_wf" class="input-field" step="1" required>
                        </div>
                        <div>
                            <label>Wiping Thick ₹/MT</label>
                            <input type="number" id="dr_conv_wt" class="input-field" step="1" required>
                        </div>
                        <div>
                            <label>Heavy Fine ₹/MT</label>
                            <input type="number" id="dr_conv_hf" class="input-field" step="1" required>
                        </div>
                        <div>
                            <label>Heavy Thick ₹/MT</label>
                            <input type="number" id="dr_conv_ht" class="input-field" step="1" required>
                        </div>
                    </div>

                    <div class="space-y-4">
                        <h3 class="text-sm font-semibold text-emerald-400 border-b border-slate-700 pb-2">Other Processes & Logistics</h3>
                        <div>
                            <label>Printing Rate ₹/MT</label>
                            <input type="number" id="dr_conv_print" class="input-field" step="1" required>
                        </div>
                        <div>
                            <label>Stranding Rate ₹/MT</label>
                            <input type="number" id="dr_conv_strand" class="input-field" step="1" required>
                        </div>
                        <div>
                            <label>Loading Cost ₹/MT</label>
                            <input type="number" id="dr_loading_cost" class="input-field" step="1" required>
                        </div>
                        <div>
                            <label>Fuel Surcharge %</label>
                            <input type="number" id="dr_fuel_surcharge" class="input-field" step="0.1" required>
                        </div>
                        <div>
                            <label>Freight Rate ₹/MT/km</label>
                            <input type="number" id="dr_freight_rate" class="input-field" step="0.01" required>
                        </div>

                        <div class="pt-6">
                            <button type="submit" id="saveDailyRatesBtn" class="btn btn-primary w-full h-10">Save All Rates</button>
                        </div>
                    </div>

                </form>
            </div>
        </div>
    </main>

    <!-- Edit Modal for Product Config -->
    <div id="editModal">
        <div class="modal-content">
            <h2 id="modalTitle" class="text-lg font-bold text-white mb-6">Edit Configuration</h2>
            <form id="configForm" onsubmit="saveConfig(event)">
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <label for="category_id">Category ID *</label>
                        <input type="text" id="category_id" class="input-field" required placeholder="e.g. RCA_FINE_0_90" pattern="[A-Za-z0-9_]+">
                    </div>
                    <div>
                        <label for="category_name">Category Name *</label>
                        <input type="text" id="category_name" class="input-field" required placeholder="e.g. RCA Fine COM 0.90 MM">
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <label for="size_min">Size Min *</label>
                        <input type="number" step="0.01" id="size_min" class="input-field" required placeholder="0.80">
                    </div>
                    <div>
                        <label for="size_max">Size Max *</label>
                        <input type="number" step="0.01" id="size_max" class="input-field" required placeholder="0.90">
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <label for="steel_type">Steel Type *</label>
                        <select id="steel_type" class="input-field" required>
                            <option value="Prime">Prime</option>
                            <option value="Commercial">Commercial</option>
                            <option value="HC">HC</option>
                        </select>
                    </div>
                    <div>
                        <label for="gsm_kg_per_mt">GSM (kg/MT) *</label>
                        <input type="number" step="1" id="gsm_kg_per_mt" class="input-field" required placeholder="60">
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div>
                        <label for="conversion_process">Conversion Process *</label>
                        <select id="conversion_process" class="input-field" required>
                            <option value="Wiping Fine">Wiping Fine</option>
                            <option value="Wiping Thick">Wiping Thick</option>
                            <option value="Heavy Fine">Heavy Fine</option>
                            <option value="Heavy Thick">Heavy Thick</option>
                            <option value="Printing">Printing</option>
                            <option value="Stranding">Stranding</option>
                        </select>
                    </div>
                    <div>
                        <label for="steel_weight">Steel Weight *</label>
                        <input type="number" step="0.01" id="steel_weight" class="input-field" required placeholder="1000">
                    </div>
                </div>

                <div class="grid grid-cols-2 gap-4 mb-6">
                    <div>
                        <label for="yield_loss_pct">Yield Loss % *</label>
                        <input type="number" step="0.01" id="yield_loss_pct" class="input-field" required placeholder="25">
                    </div>
                    <div>
                        <div class="flex items-center gap-2">
                            <input type="number" step="0.1" id="min_margin_pct" class="input-field" required placeholder="Min %" title="Min Margin">
                            <span class="text-slate-400">-</span>
                            <input type="number" step="0.1" id="max_margin_pct" class="input-field" required placeholder="Max %" title="Max Margin">
                        </div>
                        <label class="mt-1">Margin Range %</label>
                    </div>
                </div>

                <div class="flex justify-end gap-3">
                    <button type="button" class="btn btn-secondary" onclick="closeModal()">Cancel</button>
                    <button type="submit" class="btn btn-primary min-w-[100px]" id="saveBtn">Save Config</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        let configData = [];
        let isEditing = false;
        let _fullRates = {};

        Chart.defaults.color = '#94a3b8';
        Chart.defaults.font.family = 'Inter';

        let steelChartInst = null;
        let zincChartInst = null;

        async function init() {
            await loadRates();
            loadRateHistory();
            await loadConfigs();
        }

        // --- Rates ---

        async function loadRates() {
            try {
                const resp = await fetch('/api/v1/rates');
                if (!resp.ok) throw new Error('rates API failed');
                const r = await resp.json();
                _fullRates = r;
                
                // Header inputs
                document.getElementById('ratePrime').value = r.prime_steel_rate;
                document.getElementById('rateHC').value    = r.hc_steel_rate;
                document.getElementById('rateComm').value  = r.commercial_steel_rate;
                document.getElementById('rateZincSHG').value = r.zinc_sgh_rate;
                
                // Form inputs
                document.getElementById('dr_prime').value = r.prime_steel_rate;
                document.getElementById('dr_hc').value = r.hc_steel_rate;
                document.getElementById('dr_comm').value = r.commercial_steel_rate;
                document.getElementById('dr_zinc_shg').value = r.zinc_sgh_rate;
                document.getElementById('dr_zinc').value = r.zinc_rate;
                document.getElementById('dr_wire_rod').value = r.wire_rod_rate;
                document.getElementById('dr_conv_wf').value = r.conv_wiping_fine_rate;
                document.getElementById('dr_conv_wt').value = r.conv_wiping_thick_rate;
                document.getElementById('dr_conv_hf').value = r.conv_heavy_fine_rate;
                document.getElementById('dr_conv_ht').value = r.conv_heavy_thick_rate;
                document.getElementById('dr_conv_print').value = r.conv_printing_rate;
                document.getElementById('dr_conv_strand').value = r.conv_stranding_rate;
                document.getElementById('dr_loading_cost').value = r.loading_cost_per_mt || 0;
                document.getElementById('dr_fuel_surcharge').value = r.fuel_surcharge_pct || 0;
                document.getElementById('dr_freight_rate').value = r.freight_rate_per_mt_km || 0;

                setRateAsOf(r.rate_date || null);
                ['ratePrime','rateHC','rateComm','rateZincSHG'].forEach(id => document.getElementById(id).classList.remove('rate-edited'));
                document.getElementById('confirmRatesBtn').disabled = true;
                
                updateFloorPrices(); // Update table if it was loaded
            } catch (e) {
                document.getElementById('rateAsOf').textContent = 'Rates unavailable';
            }
        }

        function setRateAsOf(dateStr) {
            const el = document.getElementById('rateAsOf');
            if (!dateStr) { el.textContent = 'No data yet'; return; }
            const d = new Date(dateStr);
            const today = new Date();
            const isToday = d.toDateString() === today.toDateString();
            const fmt = d.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
            el.textContent = isToday ? `Today's rates` : `As of ${fmt}`;
            el.style.color = isToday ? '#10b981' : '#f59e0b';
        }

        function onRateEdit(input) {
            input.classList.add('rate-edited');
            document.getElementById('confirmRatesBtn').disabled = false;
        }

        async function confirmRates() {
            const prime   = parseFloat(document.getElementById('ratePrime').value);
            const hc      = parseFloat(document.getElementById('rateHC').value);
            const comm    = parseFloat(document.getElementById('rateComm').value);
            const zincShg = parseFloat(document.getElementById('rateZincSHG').value);

            if (!prime || !hc || !comm || !zincShg) {
                alert('Please enter valid values for all rates in the header.'); return;
            }

            const btn = document.getElementById('confirmRatesBtn');
            btn.disabled = true;
            btn.classList.add('saving');
            btn.innerHTML = `Saving...`;

            const payload = { 
                ..._fullRates, 
                prime_steel_rate: prime, 
                hc_steel_rate: hc, 
                commercial_steel_rate: comm, 
                zinc_sgh_rate: zincShg,
                zinc_rate: zincShg
            };
            delete payload.rate_date;

            try {
                const resp = await fetch('/api/v1/rates', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                if (!resp.ok) throw new Error(await resp.text());
                await loadRates(); // Reload everything to sync form
                
                loadRateHistory();

                btn.classList.remove('saving');
                btn.classList.add('saved');
                btn.innerHTML = `Saved!`;
                setTimeout(() => {
                    btn.classList.remove('saved');
                    btn.innerHTML = `Confirm`;
                    btn.disabled = true;
                }, 2500);
            } catch (err) {
                alert('Failed to save rates: ' + err.message);
                btn.classList.remove('saving');
                btn.innerHTML = `Confirm`;
                btn.disabled = false;
            }
        }

        async function saveAllDailyRates(e) {
            e.preventDefault();
            const btn = document.getElementById('saveDailyRatesBtn');
            btn.disabled = true;
            btn.textContent = 'Saving...';

            const payload = {
                prime_steel_rate: parseFloat(document.getElementById('dr_prime').value),
                hc_steel_rate: parseFloat(document.getElementById('dr_hc').value),
                commercial_steel_rate: parseFloat(document.getElementById('dr_comm').value),
                zinc_sgh_rate: parseFloat(document.getElementById('dr_zinc_shg').value),
                zinc_rate: parseFloat(document.getElementById('dr_zinc').value),
                wire_rod_rate: parseFloat(document.getElementById('dr_wire_rod').value),
                conv_wiping_fine_rate: parseFloat(document.getElementById('dr_conv_wf').value),
                conv_wiping_thick_rate: parseFloat(document.getElementById('dr_conv_wt').value),
                conv_heavy_fine_rate: parseFloat(document.getElementById('dr_conv_hf').value),
                conv_heavy_thick_rate: parseFloat(document.getElementById('dr_conv_ht').value),
                conv_printing_rate: parseFloat(document.getElementById('dr_conv_print').value),
                conv_stranding_rate: parseFloat(document.getElementById('dr_conv_strand').value),
                loading_cost_per_mt: parseFloat(document.getElementById('dr_loading_cost').value),
                fuel_surcharge_pct: parseFloat(document.getElementById('dr_fuel_surcharge').value),
                freight_rate_per_mt_km: parseFloat(document.getElementById('dr_freight_rate').value)
            };

            try {
                const resp = await fetch('/api/v1/rates', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });
                if (!resp.ok) throw new Error(await resp.text());
                await loadRates(); 
                loadRateHistory();
            } catch (err) {
                alert('Failed to save rates: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Save All Rates';
            }
        }

        // --- Charts ---

        async function loadRateHistory() {
            const days = document.getElementById('timeframeSelect').value;
            try {
                const resp = await fetch(`/api/v1/rates/history?days=${days}`);
                if (!resp.ok) throw new Error('Failed to fetch history');
                const history = await resp.json();
                renderCharts(history.reverse()); // Ensure chronological order if descending
            } catch (e) {
                console.error('Chart error', e);
            }
        }

        function renderCharts(data) {
            const labels = data.map(d => {
                if(!d.rate_date) return '';
                const dt = new Date(d.rate_date);
                return dt.toLocaleDateString('en-IN', {day:'numeric', month:'short'});
            });

            const primeData = data.map(d => d.prime_steel_rate);
            const hcData = data.map(d => d.hc_steel_rate);
            const commData = data.map(d => d.commercial_steel_rate);
            const zincData = data.map(d => d.zinc_sgh_rate);

            const commonOptions = {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#cbd5e1' } },
                    tooltip: { mode: 'index', intersect: false }
                },
                scales: {
                    x: { grid: { display: false, drawBorder: false } },
                    y: { grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false } }
                },
                interaction: { mode: 'nearest', axis: 'x', intersect: false }
            };

            if (steelChartInst) steelChartInst.destroy();
            steelChartInst = new Chart(document.getElementById('steelChart'), {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        { label: 'Prime Steel', data: primeData, borderColor: '#6366f1', borderWidth: 2, tension: 0.3 },
                        { label: 'HC Steel', data: hcData, borderColor: '#10b981', borderWidth: 2, tension: 0.3 },
                        { label: 'Comm Steel', data: commData, borderColor: '#f59e0b', borderWidth: 2, tension: 0.3 }
                    ]
                },
                options: commonOptions
            });

            if (zincChartInst) zincChartInst.destroy();
            zincChartInst = new Chart(document.getElementById('zincChart'), {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        { label: 'Zinc', data: zincData, borderColor: '#f43f5e', backgroundColor: '#f43f5e20', borderWidth: 2, fill: true, tension: 0.3 }
                    ]
                },
                options: commonOptions
            });
        }

        // --- Config Table ---

        async function loadConfigs() {
            const tbody = document.getElementById('configTableBody');
            try {
                const res = await fetch('/api/v1/config/product-costs');
                if (!res.ok) throw new Error('Failed to fetch data');
                configData = await res.json();
                renderTable();
            } catch (err) {
                tbody.innerHTML = `<tr><td colspan="10" class="text-center py-8 text-rose-400">Error: ${err.message}</td></tr>`;
            }
        }

        function renderTable() {
            const tbody = document.getElementById('configTableBody');
            const search = (document.getElementById('searchInput')?.value || '').toLowerCase();
            
            const filteredData = configData.filter(c => {
                const id = (c.category_id || '').toLowerCase();
                const name = (c.category_name || '').toLowerCase();
                const stype = (c.steel_type || '').toLowerCase();
                return id.includes(search) || name.includes(search) || stype.includes(search);
            });

            if (filteredData.length === 0) {
                if (configData.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="10" class="text-center py-8 text-slate-400">No configurations found. Add one to get started.</td></tr>`;
                } else {
                    tbody.innerHTML = `<tr><td colspan="10" class="text-center py-8 text-slate-400">No matching categories found.</td></tr>`;
                }
                return;
            }

            tbody.innerHTML = filteredData.map((c) => {
                const i = configData.indexOf(c);
                const floorPrice = calculateFloorPrice(c);

                return `
                <tr>
                    <td class="font-mono text-xs text-slate-300">${c.category_id}</td>
                    <td class="font-medium">${c.category_name}</td>
                    <td>${c.size_min} - ${c.size_max}</td>
                    <td>${c.gsm_kg_per_mt}</td>
                    <td><span class="px-2 py-1 rounded bg-slate-800 text-xs font-bold text-indigo-300">${c.steel_type}</span></td>
                    <td>${c.conversion_process}</td>
                    <td>${c.yield_loss_pct}%</td>
                    <td id="floorPrice-${i}" data-val="${floorPrice}" class="text-indigo-300 font-bold">₹${floorPrice.toFixed(2)}</td>
                    <td>${c.min_margin_pct}% - ${c.max_margin_pct}%</td>
                    <td>
                        <div class="flex items-center gap-3">
                            <span class="row-action" onclick="openModal(${i})">Edit</span>
                            <span class="row-action text-rose-500 hover:text-rose-400" onclick="deleteConfig(${i})">Delete</span>
                        </div>
                    </td>
                </tr>
            `}).join('');
        }

        function calculateFloorPrice(c) {
            let steelRate = _fullRates.prime_steel_rate || 0;
            if (c.steel_type.toUpperCase().includes("HC")) steelRate = _fullRates.hc_steel_rate || 0;
            if (c.steel_type.toUpperCase().includes("COMMERCIAL")) steelRate = _fullRates.commercial_steel_rate || 0;
            
            const steelCost = (steelRate / 1000) * (c.steel_weight || 0);
            
            const sizeMin = (c.size_min && c.size_min > 0) ? c.size_min : 1.0;
            const yieldLossMult = 1 + ((c.yield_loss_pct || 0) / 100);
            const zincWeight = (((c.gsm_kg_per_mt || 0) / sizeMin) * 0.51) * yieldLossMult;
            const zincRate = _fullRates.zinc_sgh_rate || _fullRates.zinc_rate || 0;
            const zincCost = zincWeight * zincRate;
            
            let convCost = 0;
            const p = (c.conversion_process || "").toLowerCase();
            if (p.includes("wiping fine")) convCost = _fullRates.conv_wiping_fine_rate || 0;
            else if (p.includes("wiping thick")) convCost = _fullRates.conv_wiping_thick_rate || 0;
            else if (p.includes("heavy fine")) convCost = _fullRates.conv_heavy_fine_rate || 0;
            else if (p.includes("heavy thick")) convCost = _fullRates.conv_heavy_thick_rate || 0;
            else if (p.includes("printing")) convCost = _fullRates.conv_printing_rate || 0;
            else if (p.includes("stranding")) convCost = _fullRates.conv_stranding_rate || 0;

            return steelCost + zincCost + convCost;
        }

        function updateFloorPrices() {
            if (!configData || configData.length === 0) return;
            renderTable();
        }

        async function deleteConfig(index) {
            const c = configData[index];
            if (!confirm(`Are you sure you want to delete configuration for ${c.category_name} (${c.category_id})?`)) return;

            try {
                const res = await fetch(`/api/v1/config/product-costs/${c.category_id}`, { method: 'DELETE' });
                if (!res.ok) throw new Error(await res.text());
                await loadConfigs();
            } catch (err) {
                alert('Failed to delete: ' + err.message);
            }
        }

        function openModal(index = -1) {
            const modal = document.getElementById('editModal');
            const title = document.getElementById('modalTitle');
            const form = document.getElementById('configForm');
            
            form.reset();
            
            if (index >= 0) {
                isEditing = true;
                title.textContent = 'Edit Configuration';
                const c = configData[index];
                document.getElementById('category_id').value = c.category_id;
                document.getElementById('category_id').disabled = true;
                document.getElementById('category_id').classList.add('opacity-50');
                
                document.getElementById('category_name').value = c.category_name;
                document.getElementById('size_min').value = c.size_min;
                document.getElementById('size_max').value = c.size_max;
                document.getElementById('gsm_kg_per_mt').value = c.gsm_kg_per_mt;
                document.getElementById('steel_type').value = c.steel_type;
                document.getElementById('conversion_process').value = c.conversion_process;
                document.getElementById('steel_weight').value = c.steel_weight;
                document.getElementById('yield_loss_pct').value = c.yield_loss_pct;
                document.getElementById('min_margin_pct').value = c.min_margin_pct;
                document.getElementById('max_margin_pct').value = c.max_margin_pct;
            } else {
                isEditing = false;
                title.textContent = 'Add Configuration';
                document.getElementById('category_id').disabled = false;
                document.getElementById('category_id').classList.remove('opacity-50');
                
                document.getElementById('steel_weight').value = 1000;
                document.getElementById('yield_loss_pct').value = 25;
                document.getElementById('min_margin_pct').value = 10;
                document.getElementById('max_margin_pct').value = 15;
            }
            
            modal.classList.add('open');
        }

        function closeModal() {
            document.getElementById('editModal').classList.remove('open');
        }

        async function saveConfig(e) {
            e.preventDefault();
            const btn = document.getElementById('saveBtn');
            btn.disabled = true;
            btn.textContent = 'Saving...';
            
            const payload = {
                category_id: document.getElementById('category_id').value,
                category_name: document.getElementById('category_name').value,
                size_min: parseFloat(document.getElementById('size_min').value),
                size_max: parseFloat(document.getElementById('size_max').value),
                gsm_kg_per_mt: parseFloat(document.getElementById('gsm_kg_per_mt').value),
                steel_type: document.getElementById('steel_type').value,
                conversion_process: document.getElementById('conversion_process').value,
                steel_weight: parseFloat(document.getElementById('steel_weight').value),
                yield_loss_pct: parseFloat(document.getElementById('yield_loss_pct').value),
                min_margin_pct: parseFloat(document.getElementById('min_margin_pct').value),
                max_margin_pct: parseFloat(document.getElementById('max_margin_pct').value)
            };

            try {
                const res = await fetch('/api/v1/config/product-costs', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (!res.ok) throw new Error(await res.text());
                
                closeModal();
                await loadConfigs(); // Reload table
            } catch (err) {
                alert('Failed to save: ' + err.message);
            } finally {
                btn.disabled = false;
                btn.textContent = 'Save Config';
            }
        }

        // --- Excel Uploads ---

        function handleConfigUpload(e) {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = async function(evt) {
                try {
                    const data = evt.target.result;
                    const workbook = XLSX.read(data, {type: 'binary'});
                    const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
                    const json = XLSX.utils.sheet_to_json(firstSheet);
                    
                    let successCount = 0;
                    for (let row of json) {
                        // Fuzzy mapping logic based on expected columns
                        const payload = {
                            category_id: row['Category ID'] || row['category_id'] || row['ID'],
                            category_name: row['Category Name'] || row['category_name'] || row['Name'],
                            size_min: parseFloat(row['Size Min'] || row['size_min']),
                            size_max: parseFloat(row['Size Max'] || row['size_max']),
                            gsm_kg_per_mt: parseFloat(row['GSM'] || row['gsm_kg_per_mt'] || row['gsm']),
                            steel_type: row['Steel Type'] || row['steel_type'] || 'Prime',
                            conversion_process: row['Conversion Process'] || row['conversion_process'],
                            steel_weight: parseFloat(row['Steel Weight'] || row['steel_weight'] || 1000),
                            yield_loss_pct: parseFloat(row['Yield Loss'] || row['yield_loss_pct'] || 25),
                            min_margin_pct: parseFloat(row['Min Margin'] || row['min_margin_pct'] || 10),
                            max_margin_pct: parseFloat(row['Max Margin'] || row['max_margin_pct'] || 15)
                        };

                        if (!payload.category_id) {
                            // auto-generate from name if possible
                            if (payload.category_name) {
                                payload.category_id = payload.category_name.toUpperCase().replace(/\W+/g, '_');
                            } else {
                                continue;
                            }
                        }

                        const res = await fetch('/api/v1/config/product-costs', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(payload)
                        });
                        if (res.ok) successCount++;
                    }
                    alert(`Successfully imported ${successCount} product cost configurations!`);
                    loadConfigs();
                } catch (err) {
                    alert('Error parsing Excel: ' + err.message);
                }
                e.target.value = ''; // reset file input
            };
            reader.readAsBinaryString(file);
        }

        function handleRatesUpload(e) {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = async function(evt) {
                try {
                    const data = evt.target.result;
                    const workbook = XLSX.read(data, {type: 'binary'});
                    const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
                    const json = XLSX.utils.sheet_to_json(firstSheet);
                    
                    if (json.length === 0) throw new Error("No data found in the Excel sheet.");
                    const row = json[0]; // Take first row
                    
                    const payload = {
                        prime_steel_rate: parseFloat(row['Prime Steel'] || row['prime_steel_rate'] || _fullRates.prime_steel_rate),
                        hc_steel_rate: parseFloat(row['HC Steel'] || row['hc_steel_rate'] || _fullRates.hc_steel_rate),
                        commercial_steel_rate: parseFloat(row['Comm Steel'] || row['Commercial Steel'] || row['commercial_steel_rate'] || _fullRates.commercial_steel_rate),
                        zinc_sgh_rate: parseFloat(row['Zinc SHG'] || row['zinc_sgh_rate'] || _fullRates.zinc_sgh_rate),
                        zinc_rate: parseFloat(row['Zinc'] || row['zinc_rate'] || _fullRates.zinc_rate),
                        wire_rod_rate: parseFloat(row['Wire Rod'] || row['wire_rod_rate'] || _fullRates.wire_rod_rate),
                        conv_wiping_fine_rate: parseFloat(row['Wiping Fine'] || row['conv_wiping_fine_rate'] || _fullRates.conv_wiping_fine_rate),
                        conv_wiping_thick_rate: parseFloat(row['Wiping Thick'] || row['conv_wiping_thick_rate'] || _fullRates.conv_wiping_thick_rate),
                        conv_heavy_fine_rate: parseFloat(row['Heavy Fine'] || row['conv_heavy_fine_rate'] || _fullRates.conv_heavy_fine_rate),
                        conv_heavy_thick_rate: parseFloat(row['Heavy Thick'] || row['conv_heavy_thick_rate'] || _fullRates.conv_heavy_thick_rate),
                        conv_printing_rate: parseFloat(row['Printing'] || row['conv_printing_rate'] || _fullRates.conv_printing_rate),
                        conv_stranding_rate: parseFloat(row['Stranding'] || row['conv_stranding_rate'] || _fullRates.conv_stranding_rate)
                    };

                    const res = await fetch('/api/v1/rates', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                    if (!res.ok) throw new Error(await res.text());
                    
                    alert('Successfully updated daily rates from Excel!');
                    await loadRates();
                    loadRateHistory();
                } catch (err) {
                    alert('Error importing Rates Excel: ' + err.message);
                }
                e.target.value = ''; // reset file input
            };
            reader.readAsBinaryString(file);
        }

    </script>
</body>
</html>
"""

with open('static/setup.html', 'w', encoding='utf-8') as f:
    f.write(HTML_CONTENT)
