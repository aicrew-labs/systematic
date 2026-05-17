# Master prompt: Wire manufacturing intelligence dashboard

## Purpose of this document

This is a complete, self-contained prompt for building a wire and cable manufacturing intelligence dashboard. It can be used with any LLM (Claude, GPT-4, Gemini, etc.) to resume, extend, or hand off development from scratch. It includes all business context, system design decisions, data structures, UI specifications, technical stack, and a built-in FAQ so no follow-up questions are needed.

---

## 1. Business context

### Who is the client?

**Systematic Industries Pvt Ltd** (parent company) operates a wire and cable manufacturing group in India with two main entities:

- **Sayli plant** — MS (mild steel) wire drawing, HC (high carbon) wire drawing, annealing
- **Veritas Industries Pvt Ltd** — 4 manufacturing units (Unit 1, 2, 3, 4) producing MS wire, HC wire, HC patented wire, GI (galvanised iron) wire, ACSR (aluminium conductor steel reinforced), stranding, weld mesh, OFC (optical fibre cable) products

**Total units in scope: 5** (Sayli + Veritas Units 1–4). All billing is under one parent company. Each unit may produce overlapping products (e.g. MS wire 2.62mm can be made at both Sayli and Veritas Unit 1). Units are not rigidly product-specialised.

### What does the business do?

1. Receives raw material (wire rod — MS and HC grades) from external mills: Rashmi Metallurgical, Shyam Metalics, SKS Ispat, TATA Steel, JSW, Jindal, etc.
2. Wire rod is processed through drawing machines across 5 plants to produce finished wire products of various diameters and grades.
3. Finished goods are dispatched to ~257 customers across India and export markets.
4. Products include: MS wire (multiple diameters), HC patented wire, HC wire, GI wire (fine and heavy coating), ACSR, weld mesh, OFC cable (2F, 4F, 6F in FRP & yarn variants).

### Current pain points

- The decision maker who quotes prices to customers does so from memory, without real-time access to FG stock, machine utilisation, order backlog, or historical pricing data.
- This leads to: margin loss (quoted too low), missed orders (quoted too high), and impossible delivery promises (committed dates the plant cannot meet).
- Plant MIS data (production, stock, efficiency) is captured daily in Excel files by multiple people across units — it is not in a live system.
- The order book is in an ERP system (web-based), but the decision maker does not always have access to it.
- Historical quotes exist in the ERP but have not been exported to a structured format yet.
- Conversion cost (machine time + power + labour per MT of output) is not formally tracked — it exists as vague institutional knowledge.

---

## 2. System overview

### What we are building

A **web-based intelligence dashboard** for wire manufacturing operations. It has four modules:

1. **Operations overview** — daily snapshot of RM stock, production, FG inventory, scrap, machine utilisation, manpower
2. **Order book** — open sales orders, dispatched vs pending quantities, estimated dispatch ETA per order
3. **Quote intelligence** — AI-powered price suggestion for incoming customer enquiries, with reasoning
4. **Capacity planner** — plant-wise capacity vs current load, RM availability check, dispatch date estimation

### Who uses it

5–10 people: the owner, plant managers, and sales/commercial managers. Must work on both desktop and mobile (used on the go for quoting decisions).

### Hosting

Phase 1: hosted on **Railway** (cloud PaaS). PostgreSQL database on Railway. Backend on Railway. Frontend served as a React app.

Future: may migrate to company server. Must be designed to be portable.

---

## 3. Technical stack

### Frontend
- **React** (functional components, hooks)
- **Tailwind CSS** for styling
- Mobile-first responsive design
- No heavy UI libraries — keep it clean and fast

### Backend
- **Python + FastAPI**
- REST API serving the frontend
- Handles Excel file parsing, database writes, and AI prompt assembly

### Database
- **PostgreSQL** (hosted on Railway)
- Stores historical data that accumulates over time
- Daily Excel uploads are parsed and inserted — not replaced — so history builds up

### AI layer
- **Anthropic Claude API** — model: `claude-sonnet-4-20250514`
- Used exclusively for the quote intelligence reasoning layer
- The system pulls structured data from the database, assembles it into a context-rich prompt, sends it to Claude, and displays the response
- Claude does not hallucinate numbers — all figures (stock, prices, utilisation) come from the database; Claude only reasons over them

### Data ingestion
- Phase 1: manual daily upload via a file upload page within the dashboard
- Phase 2: automated pickup from a shared Google Drive or OneDrive folder via API
- File formats: `.xlsx`, `.xls`, `.csv`

---

## 4. Data sources and their structures

### 4.1 Plant MIS Excel files (daily, one per unit)

Each unit submits a daily MIS Excel. Files vary slightly by unit but contain these core sheets:

**Sayli MIS (`.xls` format, 17 sheets):**
- `MIS-REPORT` — daily production per machine per shift (date, machine, shift, hours, operator, RM grade, inlet size, outlet size, weight per metre, machine speed, capacity, achieved production, efficiency %)
- `Summary All` — daily rolled-up totals: RM receipt, total production (MS wire MT, HC wire MT), finish production, efficiency % by unit, scrap details (short coils, bailed scrap, mill scale, bandhi), manpower cost, power consumption (units/MT), dispatch totals by destination
- `STOCK` — wire rod stock register: opening balance, receipt today, cumulative receipt, issue for production, closing stock — by size, mill, grade
- `FG, N. C Packinglist Stock` — finished goods register per party per size: WO number, WO qty, FG qty, packing qty, NC qty, dispatch qty, balance qty, FG stock qty, status (Running / Completed / Stock)
- `Dispt` — dispatch details: date, vehicle number, challan/invoice number, product size, customer, actual quantity dispatched, in/out time
- `Recept` — raw material inward: date, weight slip, vehicle, size, grade, quantity, coils, invoice number, party name, vehicle in/out time
- `Daily Inventory` — daily closing balances for: FG, for annealing, FD for drawing, non-moving, wire rod + annl-WR, scrap, total
- `Sayli efficincy` — machine-wise efficiency: WRC machines (wire rod coiler) and FD machines (fine drawing), shift A and B, operator, WR used, product size, production MT, target production, speed, efficiency %
- `Manpower report` — headcount by category (operator, helper, furnace, bailing, dispatch, housekeeping): required, A shift, B shift, total, present, shortage
- `Sheet3` (historical production detail — Unit I fine drawing machines, F1–F8)

**Veritas Unit files (`.xlsx` format, one per unit):**
- `SMS` — shift morning summary: machine name, inlet size, finish size, A shift qty, B shift qty, daily total, cumulative total
- `SUMMARY` / `Details` — day-wise production totals: MS wire, HC wire for ACSR, weld mesh, stranding, ACSR, FG production
- `DAYWISE` — product-level daily production (Unit 2: GI wire by size; Unit 3: HC wire by size and grade; Unit 4: FCA/RCA products)
- `ZINC GAP` (Units 2, 3, 4) — galvanising data: FG size, speed, standard production, actual production, efficiency, zinc specification (gsm), zinc required (kg), zinc consumed, gap
- `WD details` / `WD -4` — wire drawing stock: opening stock, production (day/cumulative), issue to next process, closing stock — by size
- `FG DATA DAILY` — finished goods daily tracking
- `STOCK` — RM and WIP stock register
- `DROSSING` — zinc dross tracking (weight of dross removed per day)
- `DISPATCH` / `DAILY DISP` — dispatch records

**Key fields to extract and store daily:**
```
date, unit_name, machine_id, product_type, product_size_mm, grade,
rm_grade, rm_mill, shift, hours_worked, production_mt, capacity_mt,
efficiency_pct, scrap_kg, scrap_type, fg_stock_mt, wr_stock_mt,
wr_received_mt, wr_consumed_mt, dispatch_mt, dispatch_customer,
power_units_consumed, manpower_present, manpower_required
```

### 4.2 CRM / Order book (daily export from ERP)

**File:** `CRM_Dashboard.xlsx` (419 rows in sample, April–May 2026)

**Columns:**
```
Sr no, Sales Order ID, Sales Order Date, Sales Order Number,
PO No, Customer Name, Total Qty (MT), Dispatch Qty (MT),
Shortclose Qty (MT), Sales Order Status, R.M (sales rep),
SO Reject Reason, Management Approval Attachment,
PO/Cust Confirmation Attachment, Action
```

**Status values:** `PENDING FOR INVOICE`, `SO SHORT CLOSED`, `SO CREATED`, `AMMEND SO CREATED`, `SO CANCELLED`, `SO REJECTED BY MIS`, `SO REJECTED BY CREDIT CONTROL`

**Key metrics from sample data:**
- 332 active pending orders
- 18,277 MT total ordered (all statuses)
- 8,686 MT dispatched
- 9,591 MT remaining (balance)
- 127 orders with zero dispatch yet (3,380 MT)
- 257 unique customers
- 19 sales reps

**Important gap:** The CRM export currently has only total quantity per SO — no line-item product/size breakdown. This needs to be addressed in future ERP exports or supplemented with the full SO detail view.

### 4.3 Historical quote data (to be exported from ERP)

**Not yet available as a file.** Will be provided as a CSV export. Until then, use synthetic data (see Section 7).

**Required columns:**
```
so_number, so_date, customer_name, customer_type (new/repeat),
product_name, product_size_mm, grade, quantity, unit (MT/MTS/KME),
unit_rate_inr, net_amount_inr, payment_terms, credit_days,
freight_terms, hsn_code, gst_pct, billing_unit,
outcome (won/lost/pending), sales_rep, notes
```

**ERP SO structure (from screenshots):**
- Header: SO number, PO number, PO date, contact person, billing unit, enquiry date, quote expiry date, SO validity date, customer, billing details, payment terms, credit days, consignee, shipping details, invoice type (Normal / OFC Domestic / etc.)
- Line items: product name (e.g. "HC Patented Wire 5.10 MM"), description, HSN code, GST%, unit rate (INR), quantity, unit (MTS/MT/KME), RMS No (raw material source code, e.g. "STERLITE 5.10MM"), net amount

**Pricing units vary by product:**
- MS wire: ₹ per MT (metric tonne)
- HC patented wire: ₹ per MTS (metres)
- OFC cable: ₹ per KME (kilo metres)
- Other products: confirm per product type

### 4.4 Raw material prices (GRN data)

**GRN = Goods Receipt Note** — the record of RM arriving at the plant. Each GRN entry links to a purchase invoice with per-MT rate.

**Not yet available as a structured export.** To be obtained from ERP GRN screen. Required columns:
```
grn_date, vendor_name, invoice_number, po_number,
rm_size_mm, rm_grade, quantity_mt, coils,
rate_per_mt_inr, total_amount_inr, plant_unit
```

**Current vendors and approximate market rates (May 2026, to be confirmed):**
- Rashmi Metallurgical — IS 7887 G-4, 5.5mm — ~₹52,000–54,000/MT
- Shyam Metalics — IS 7887 G-4, 5.5mm — ~₹51,500–53,000/MT
- SKS Ispat — IS 7887 G-4, 5.5mm — ~₹52,000/MT
- TATA Steel — HC72B, 5.5mm — ~₹66,000–68,000/MT (HC grade premium)
- JSW Steel — CAQ G-1, 5.5mm — ~₹52,500/MT
- Jindal — IS 7887 G-3, 8.5mm — ~₹53,500/MT

### 4.5 Product catalogue (~50 products)

Products are identified by type + size + grade. There is no formal product master file yet. Build one from the MIS and ERP data.

**Known products (from files and ERP screenshots):**

MS wire (drawing): 1.10mm, 1.18mm, 1.25mm, 1.38mm, 1.45mm, 1.52mm, 1.58mm, 1.60mm, 1.70mm, 1.80mm, 1.90mm, 2.00mm, 2.10mm, 2.12mm, 2.20mm, 2.23mm, 2.25mm, 2.28mm, 2.32mm, 2.38mm, 2.42mm, 2.45mm, 2.49mm, 2.58mm, 2.60mm, 2.62mm, 2.70mm, 2.80mm, 2.90mm, 2.98mm, 3.00mm, 3.13mm, 3.15mm, 3.94mm, 5.58mm, 6.00mm, 6.78mm, 7.78mm

HC patented wire: 4.90mm, 5.10mm, 5.68mm (quoted in MTS — metres)

GI wire (fine coating): 0.80mm IS, 0.90mm IS, 1.00mm IS, 1.25mm IS, 1.40mm IS, 1.60mm IS, 2.00mm (quoted by Veritas Unit 2, unit: MT or KG)

OFC cable: 2F 4.5mm DIA FRP & Yarn, 4F UT UA 5.8mm FRP With Yarn, 6F UT UA 5.8mm FRP With Yarn (quoted in KME)

ACSR, stranding, weld mesh — tracked in Veritas Unit 1 summary

### 4.6 Machine / capacity master (to be built manually)

No formal file exists. Build a `machines` table with:
```
machine_id, unit_name, machine_type, min_diameter_mm, max_diameter_mm,
capacity_mt_per_shift, product_types_capable[], notes
```

**Known machines from MIS:**
- Sayli: MS1–MS8 (medium drawing, 2.xx–6mm range, ~9–10 MT/shift capacity), F1–F8 (fine drawing, 0.9–2.5mm range, ~67–134 MT/month capacity per machine at 100% efficiency), WRC1–WRC3 (wire rod coiler, 5.5mm → 5.5mm, ~10.4 MT/shift target)
- Veritas Unit 1: HC drawing machines (U1-HC-8B1, U1-HC-7B1, U1-HC-11B1, U1-HC-6B1), stranding machines, weld mesh
- Veritas Unit 2: GI galvanising lines (0.8–2.0mm), wet drawing machines
- Veritas Unit 3: HC drawing, patenting, galvanising (heavy coating GI)
- Veritas Unit 4: FCA/RCA machines (4×0.80mm, 6.1×1.40mm strands), GI

**Capacity model assumption (Phase 1):** Any machine within its diameter range can produce any product of compatible type. Capacity is expressed as MT/shift or MT/day. Throughput varies by wire size (thinner = slower MT/day).

---

## 5. Database schema

### Core tables

```sql
-- Plants / units
CREATE TABLE units (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,  -- 'Sayli', 'Veritas Unit 1', etc.
  location VARCHAR(100),
  active BOOLEAN DEFAULT TRUE
);

-- Machine master
CREATE TABLE machines (
  id SERIAL PRIMARY KEY,
  unit_id INTEGER REFERENCES units(id),
  machine_code VARCHAR(50),   -- 'MS1', 'F1', 'U1-HC-8B1'
  machine_type VARCHAR(50),   -- 'fine_drawing', 'medium_drawing', 'galvanising', etc.
  min_dia_mm DECIMAL(6,2),
  max_dia_mm DECIMAL(6,2),
  capacity_mt_per_shift DECIMAL(8,3),
  active BOOLEAN DEFAULT TRUE
);

-- Product master
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  product_type VARCHAR(100),  -- 'MS Wire', 'HC Patented Wire', 'GI Wire', 'OFC Cable'
  size_mm DECIMAL(6,3),
  grade VARCHAR(50),          -- 'IS 7887 G-4', 'HC72B', etc.
  unit_of_measure VARCHAR(10), -- 'MT', 'MTS', 'KME', 'KG'
  hsn_code VARCHAR(20),
  gst_pct DECIMAL(4,2)
);

-- Daily production snapshot
CREATE TABLE daily_production (
  id SERIAL PRIMARY KEY,
  snapshot_date DATE NOT NULL,
  unit_id INTEGER REFERENCES units(id),
  machine_id INTEGER REFERENCES machines(id),
  product_id INTEGER REFERENCES products(id),
  shift CHAR(1),              -- 'A', 'B'
  hours_worked DECIMAL(4,1),
  production_mt DECIMAL(10,3),
  capacity_mt DECIMAL(10,3),
  efficiency_pct DECIMAL(6,2),
  operator_name VARCHAR(100),
  rm_grade VARCHAR(50),
  rm_mill VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Daily inventory snapshot
CREATE TABLE daily_inventory (
  id SERIAL PRIMARY KEY,
  snapshot_date DATE NOT NULL,
  unit_id INTEGER REFERENCES units(id),
  product_id INTEGER REFERENCES products(id),
  inventory_type VARCHAR(50), -- 'FG', 'WIP', 'FD_for_drawing', 'for_annealing', 'non_moving', 'scrap', 'wire_rod'
  quantity_mt DECIMAL(10,3),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Raw material stock
CREATE TABLE rm_stock (
  id SERIAL PRIMARY KEY,
  snapshot_date DATE NOT NULL,
  unit_id INTEGER REFERENCES units(id),
  rm_size_mm DECIMAL(6,2),
  rm_grade VARCHAR(50),
  rm_mill VARCHAR(100),
  opening_coils INTEGER,
  opening_qty_mt DECIMAL(10,3),
  received_coils INTEGER,
  received_qty_mt DECIMAL(10,3),
  consumed_coils INTEGER,
  consumed_qty_mt DECIMAL(10,3),
  closing_coils INTEGER,
  closing_qty_mt DECIMAL(10,3),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Raw material prices (from GRN)
CREATE TABLE rm_prices (
  id SERIAL PRIMARY KEY,
  grn_date DATE,
  vendor_name VARCHAR(100),
  rm_size_mm DECIMAL(6,2),
  rm_grade VARCHAR(50),
  invoice_number VARCHAR(100),
  quantity_mt DECIMAL(10,3),
  rate_per_mt_inr DECIMAL(12,2),
  unit_id INTEGER REFERENCES units(id),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Sales orders (from CRM export)
CREATE TABLE sales_orders (
  id SERIAL PRIMARY KEY,
  so_id INTEGER,              -- ERP Sales Order ID
  so_number VARCHAR(50),
  so_date DATE,
  po_number VARCHAR(100),
  customer_name VARCHAR(200),
  total_qty DECIMAL(10,3),
  dispatch_qty DECIMAL(10,3),
  shortclose_qty DECIMAL(10,3),
  status VARCHAR(50),
  sales_rep VARCHAR(100),
  reject_reason TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Sales order line items (from full SO detail export)
CREATE TABLE so_line_items (
  id SERIAL PRIMARY KEY,
  so_id INTEGER REFERENCES sales_orders(id),
  product_id INTEGER REFERENCES products(id),
  quantity DECIMAL(10,3),
  unit VARCHAR(10),
  unit_rate_inr DECIMAL(12,2),
  net_amount_inr DECIMAL(14,2),
  rms_no VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Quote history
CREATE TABLE quote_history (
  id SERIAL PRIMARY KEY,
  so_number VARCHAR(50),
  quote_date DATE,
  customer_name VARCHAR(200),
  is_repeat_customer BOOLEAN,
  product_id INTEGER REFERENCES products(id),
  quantity DECIMAL(10,3),
  unit VARCHAR(10),
  unit_rate_inr DECIMAL(12,2),
  net_amount_inr DECIMAL(14,2),
  payment_terms VARCHAR(50),
  credit_days INTEGER,
  freight_terms VARCHAR(50),
  billing_unit VARCHAR(100),
  outcome VARCHAR(20),        -- 'won', 'lost', 'pending', 'cancelled'
  sales_rep VARCHAR(100),
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Dispatch records
CREATE TABLE dispatches (
  id SERIAL PRIMARY KEY,
  dispatch_date DATE,
  unit_id INTEGER REFERENCES units(id),
  so_id INTEGER REFERENCES sales_orders(id),
  customer_name VARCHAR(200),
  product_id INTEGER REFERENCES products(id),
  challan_number VARCHAR(100),
  vehicle_number VARCHAR(50),
  actual_qty DECIMAL(10,3),
  unit VARCHAR(10),
  via_party VARCHAR(100),
  billing_unit VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 6. API endpoints (FastAPI)

```
POST   /api/upload/mis              # Upload daily MIS Excel file
POST   /api/upload/orders           # Upload daily CRM order book
POST   /api/upload/quotes           # Upload historical quote CSV
GET    /api/dashboard/overview      # Operations overview data
GET    /api/dashboard/orders        # Order book with filters
GET    /api/dashboard/capacity      # Capacity vs load per unit
POST   /api/quote/suggest           # Get AI-powered quote suggestion
GET    /api/products                # Product master list
GET    /api/customers               # Customer list with history
GET    /api/machines                # Machine master
GET    /api/inventory/current       # Current FG stock by product
GET    /api/rm/stock                # Current RM stock
GET    /api/rm/prices               # Latest RM prices by grade/mill
GET    /api/quote/history           # Quote history with filters
```

---

## 7. Quote intelligence module — detailed specification

### What it does

When a customer calls with an enquiry, the user enters: customer name, product, size/grade, quantity, unit, and payment terms. The system instantly surfaces:

1. Customer classification (new vs repeat, number of past orders)
2. Last price quoted to this specific customer for this product
3. Current FG stock available for immediate dispatch
4. Machine utilisation % for the relevant production line
5. Estimated dispatch date (if FG insufficient, calculates production time)
6. Current RM cost for this product's input material
7. Recent quotes to other customers for the same product (with won/lost)
8. Market rate range (derived from recent quote history)
9. AI-generated price suggestion range with plain-English reasoning

### How the AI reasoning works

The backend assembles a structured context block and sends it to Claude:

```
SYSTEM PROMPT:
You are a pricing intelligence assistant for a wire and cable manufacturing company 
in India. You help commercial managers decide what price to quote to customers. 
You will be given structured data about the enquiry, current stock, machine 
utilisation, cost, and recent pricing history. Based on this, suggest a price 
range with clear reasoning. Be direct and commercial. Keep reasoning to 3-4 
sentences. Always state the floor price (cost + minimum margin) explicitly.

USER PROMPT (assembled dynamically):
Enquiry details:
- Customer: [name], [new/repeat customer, X past orders]
- Product: [product name], [size]mm, [grade]
- Quantity: [qty] [unit]
- Payment terms: [terms], [credit days] days credit

Current situation:
- FG stock available: [qty] [unit] (can dispatch immediately: [yes/no, partial])
- Machine utilisation (relevant line): [pct]% 
- Estimated dispatch time if production needed: [X] days
- RM cost for this product: ₹[rate]/MT ([vendor], [grade])
- Estimated conversion cost: ₹[rate]/MT (power + labour + overhead)
- Estimated total cost: ₹[rate]/[unit]

Pricing context:
- Last quoted to THIS customer: ₹[rate]/[unit] on [date] — [won/lost]
- Recent quotes to OTHER customers for same product:
  * [customer]: ₹[rate] on [date] — [won/lost]
  * [customer]: ₹[rate] on [date] — [won/lost]
  * [customer]: ₹[rate] on [date] — [won/lost]
- Market rate range (last 30 days): ₹[low]–₹[high]/[unit]

Please suggest a price range and explain your reasoning.
```

### Conversion cost estimation (Phase 1)

Until formal cost data is available, estimate conversion cost as follows based on MIS data:

```
Power cost: avg units consumed per MT × ₹8/unit (industrial tariff)
  → From MIS: typically 180–270 units/MT for MS wire drawing
  → Power cost estimate: ₹1,440–₹2,160/MT

Labour cost: (total manpower cost per month) ÷ (total MT produced per month)
  → From MIS: manpower cost ~₹40,000–50,000/day for Sayli
  → At ~50 MT/day production: ~₹800–1,000/MT

Overhead allocation: 15% of (power + labour)
  → Approx ₹340–480/MT

Total conversion cost estimate: ₹2,580–₹3,640/MT for MS wire drawing
→ Round to ₹3,000/MT as default for MS wire
→ HC wire (patented): use ₹4,500/MT (additional patenting cost)
→ GI wire: use ₹5,500/MT (zinc cost + galvanising)
→ OFC: use ₹8,000/KME (FRP, yarn, additional materials)
```

These are estimates to be replaced with actuals once GRN and formal cost tracking is in place.

### Synthetic quote history (use until real data available)

Generate 150 rows covering April–May 2026 with these customers and products:

Customers (from CRM): Systematic Industries Ltd – Sarigam, Polycab India Ltd – Daman, Diamond Power Infrastructure Ltd, Fort Gloster Industries Ltd, Shree Hanuman Tubes Pvt Ltd, Maccaferri Environmental Solutions, TRANSRAIL LIGHTING LTD, Chandresh Cables Ltd, KEI Industries Ltd, Nirmal Networks, Cisfiber Infra Solution, Ascent Networks Pvt Ltd, Al Ma Cabrol FZC LLC, NIRMAL NETWORKS

Products and approximate rate ranges (May 2026):
- MS Wire 2.62mm (MT): ₹58,000–₹63,000/MT
- MS Wire 1.38mm (MT): ₹61,000–₹66,000/MT
- MS Wire 5.58mm (MT): ₹55,000–₹59,000/MT
- HC Patented Wire 5.10mm (MTS): ₹87,000–₹93,000/MTS
- HC Patented Wire 5.68mm (MTS): ₹87,000–₹92,000/MTS
- HC Patented Wire 4.90mm (MTS): ₹88,000–₹94,000/MTS
- GI Wire 0.90mm IS (MT): ₹72,000–₹78,000/MT
- GI Wire 1.25mm IS (MT): ₹70,000–₹75,000/MT
- OFC 2F 4.5mm FRP & Yarn (KME): ₹3,700–₹4,200/KME
- OFC 4F UT UA 5.8mm (KME): ₹6,500–₹7,500/KME
- OFC 6F UT UA 5.8mm (KME): ₹8,500–₹9,500/KME

Won/lost distribution: approximately 70% won, 30% lost (lost quotes tend to be at the higher end of each range).

---

## 8. UI specification — quote intelligence module

### Screen layout (mobile-first, single column on mobile, two-column on desktop)

**Section 1 — Input form**
- Dropdown: Customer name (searchable, from customer master)
- Dropdown: Product type
- Dropdown: Size / grade (filtered by product type selection)
- Number input: Quantity
- Dropdown: Unit (MT / MTS / KME / KG)
- Dropdown: Payment terms (1-Days / 30 Days / 45 Days / etc.)
- Button: "Get suggested quote" → triggers API call to `/api/quote/suggest`

**Section 2 — Context cards (6 metric cards in 2×3 grid)**
- Customer type (New / Repeat + number of past orders)
- Last quoted to them (rate + date)
- FG stock available (qty + "ready to dispatch now" or "partial")
- Machine utilisation % (unit name + line type)
- Estimated dispatch (days + explanation)
- RM cost (rate/unit + vendor + grade)

**Section 3 — Market signals panel**
- Bulleted signal list with coloured dot indicators:
  - Green dot: favourable signals (stock available, won recently at similar rate, good payment terms)
  - Amber dot: watch signals (machine underutilised, similar price won/lost mix)
  - Red dot: risk signals (low stock, long dispatch time, customer lost last time)
  - Blue dot: informational (payment terms, credit days)

**Section 4 — AI suggested price range**
- Large price range display: ₹[LOW] — ₹[HIGH] per [unit]
- Visual bar showing: floor price → suggested range → market ceiling
- AI reasoning paragraph (3–4 sentences, plain English)
- "This is a suggestion only — final quote is at your discretion" disclaimer

**Section 5 — Quote history table**
- Last 5 quotes for this product across all customers
- Columns: date, customer, rate, unit, qty, outcome (Won / Lost)
- Link: "View full history" → opens filtered history view

### UI design principles
- Clean, flat design — no gradients, no shadows
- White cards with 0.5px borders
- Mobile-friendly tap targets (minimum 44px height on interactive elements)
- Colour coding: green = positive/won, amber = caution, red = risk/lost, blue = informational
- No jargon — labels use plain language (not "MT utilisation coefficient" — just "machine utilisation %")
- Data loads fast — all context cards populate from a single API call before the AI response arrives
- AI response streams in (typewriter effect) so the user sees it appearing in real time

---

## 9. Operations overview module — specification

**Top metrics bar (always visible):**
- Total RM in stock (MT)
- Total FG in stock (MT)
- Total open orders (MT pending)
- Today's production (MT, all units combined)
- Average machine utilisation % (all units)

**Section 1 — RM stock**
Table: size, mill, grade, opening stock MT, received today MT, consumed today MT, closing MT — filterable by unit

**Section 2 — Production today**
Per-unit cards showing: unit name, total production MT, efficiency %, top-producing machine, vs yesterday comparison

**Section 3 — FG inventory**
Table: product, size, available MT, in production (WIP), for annealing, non-moving — with search and filter

**Section 4 — Machine utilisation**
Horizontal bar chart per unit: each machine as a bar, colour-coded green (>70%), amber (40–70%), red (<40%)

**Section 5 — Scrap summary**
Today's scrap: short coils MT, bailed scrap MT, mill scale MT, bandhi MT — with % of production

**Section 6 — Manpower**
Per-unit: operators required vs present, helpers required vs present, shortage count highlighted in red

---

## 10. Order book module — specification

**Filters:** customer name search, status filter, sales rep filter, product type filter, date range

**Summary row:** total orders MT, total dispatched MT, total pending MT, orders with zero dispatch count

**Main table:**
- SO number
- SO date
- Customer name
- Product (if line-item data available)
- Total qty / unit
- Dispatched qty
- Balance qty
- Status badge (colour coded)
- Sales rep
- Estimated dispatch date (calculated from capacity planner)
- Actions: view details

**Detail view (per SO):** Shows all line items, dispatch history, and a "Check capacity" button that triggers the capacity planner for that specific order.

---

## 11. Capacity planner module — specification

**Input:** Select an order (or enter product + quantity manually)

**Output:**
1. FG check: "X MT available in stock → can dispatch immediately"
2. If FG insufficient: "Need to produce Y MT more"
3. Machine assignment: "Best unit for this product: [unit] on [machine] — currently at [Z]% utilisation"
4. Production time estimate: "At current throughput: [W] MT/day → Y MT will take [N] days"
5. RM check: "RM available: [grade] [qty] MT in stock at [unit] → sufficient / shortfall of [Z] MT"
6. Dispatch ETA: "Earliest possible dispatch: [date range]"

**Plant load view:**
- Per unit: total capacity MT/day vs current committed production MT/day (from open order book)
- Colour-coded load bar: green = <70% loaded, amber = 70–90%, red = >90%

---

## 12. FAQ — built-in answers to likely follow-up questions

**Q: The MIS Excel files have different structures across units — how do I parse them?**
A: Each file type has a known sheet structure. Build a parser per file type (Sayli `.xls` vs Veritas Unit 1/2/3/4 `.xlsx`). Use openpyxl for `.xlsx` and xlrd for `.xls`. The key is to identify the header row dynamically (search for known column names like "DATE", "M/C", "SHIFT") rather than hardcoding row numbers, since rows above the header vary.

**Q: What if the Excel format changes slightly each month?**
A: Build a validation step: after parsing, check that key columns exist and that the date range makes sense. If validation fails, flag the file for manual review rather than silently inserting bad data. Keep the raw uploaded file in a separate storage bucket for audit purposes.

**Q: How do I handle the fact that production efficiency is already calculated in the MIS — should I recalculate it?**
A: Trust the MIS efficiency figure for display. Only recalculate it if the source data (capacity, actual production) is available and the pre-calculated figure seems anomalous (>100% or negative). The MIS efficiency formula is: `actual_production / (capacity × hours / 12) × 100`.

**Q: Products don't have a universal product code — how do I match them across files?**
A: Build a product normalisation function: strip whitespace, lowercase, standardise size format to X.XXmm. Example: "MS WIRE 2.62 MM", "ms wire 2.62mm", "2.62MM MS" all map to product_key = "ms_wire_2.62mm". Build the product master from this normalised key.

**Q: The CRM order book doesn't have line-item product details — just total SO quantity. How do I link orders to products for the capacity planner?**
A: Phase 1: use the SO number to look up the full SO detail from the ERP (if API access is available) or from the manually exported quote history. Phase 2: request that the CRM daily export includes line-item detail. Until then, the capacity planner works at SO level with manual product entry.

**Q: How do I calculate the dispatch ETA?**
A: Step 1: check FG stock for the product. Step 2: if FG covers the order, ETA = today + 1–2 days (packing/logistics). Step 3: if FG is insufficient, calculate MT needed from production. Step 4: find the machine(s) that can make this product and are not fully booked. Step 5: ETA = today + (MT needed / daily throughput for that product on that machine) + 2 days buffer. Round up to nearest day. If RM is insufficient, add RM procurement lead time (typically 2–5 days from order to delivery).

**Q: How do I know which machine makes which product if there's no formal mapping?**
A: Use the diameter range rule: a machine with min_dia 0.9mm and max_dia 2.5mm can make any product with size in that range, of the compatible type (MS drawing machine makes MS wire, HC drawing makes HC wire, galvanising makes GI wire). Build a `can_produce(machine_id, product_id)` function that checks type compatibility + diameter range. For Phase 1, assume all machines of the right type within a unit can be used interchangeably for capacity calculation.

**Q: The AI quote suggestion — what if the model hallucinates a price?**
A: The system is designed so Claude never invents numbers. Every number in the prompt (RM cost, last price, market range, utilisation) is pulled from the database. Claude's job is to reason over provided numbers, not generate them. Instruct Claude explicitly: "Use only the numbers provided in this prompt. Do not invent or estimate any figures." Claude then outputs a range and reasoning based purely on what was given.

**Q: What happens when there is no quote history for a product yet?**
A: The system degrades gracefully. Signal panel shows "No history available for this product." Price suggestion falls back to: cost-plus pricing (RM cost + conversion cost + 15% margin) with a note: "No historical data — suggestion based on cost-plus only. Verify against current market before quoting."

**Q: How should won/lost be tracked if we don't have it in the current data?**
A: Phase 1: any SO that reached "PENDING FOR INVOICE" status and has dispatch qty > 0 is marked "won". SOs with status "SO CANCELLED" or "SO REJECTED" are marked "lost". SOs with zero dispatch and status still "PENDING" are marked "pending". This is imperfect but sufficient for Phase 1. Phase 2: add a manual won/lost toggle on the quote history screen.

**Q: Can the same product be made at multiple units simultaneously?**
A: Yes. The capacity planner should check all units capable of making the product and recommend the one with the most available capacity. It should also support splitting an order across units if no single unit can fulfil it in the required timeline.

**Q: How do I handle the OFC product type which uses KME (kilo metres) as the unit?**
A: Store the unit in the `products` table and in every quote/order record. All capacity calculations must be unit-aware. For KME products, machine throughput is also stored in KME/day rather than MT/day. The UI shows the native unit for each product — never converts silently.

**Q: What about GST? Should prices be shown inclusive or exclusive?**
A: All prices are stored and displayed exclusive of GST. GST (18% for most wire products, HSN 722990; 18% for OFC, HSN 90011000) is shown separately in the quote output, matching the ERP format.

**Q: How is the "non-moving" inventory category handled?**
A: Non-moving stock (products sitting for >30 days without dispatch) is flagged in the FG inventory view with an amber badge. In the quote intelligence, if the product has non-moving stock, the AI is informed: "Note: [X] MT of this product is classified as non-moving inventory — consider offering a slight discount to clear it." This nudges the system to be more aggressive on price for slow-moving SKUs.

---

## 13. Phased delivery plan

### Phase 1 (build now)
- FastAPI backend with PostgreSQL on Railway
- React frontend (desktop + mobile)
- Daily Excel upload portal (manual)
- Data parsers for: Sayli MIS, Veritas Unit 1–4 MIS, CRM order book
- All four dashboard modules with synthetic data pre-loaded
- Claude-powered quote intelligence (live API call)
- Synthetic quote history (150 rows, realistic data)
- Estimated conversion cost (hardcoded by product type)

### Phase 2 (next sprint)
- Google Drive / OneDrive auto-pickup for daily files
- GRN data import → real RM prices
- Full SO line-item detail from ERP export
- Won/lost tracking on quote history
- Trend charts (30-day production, efficiency, scrap trends)
- Email or WhatsApp notification for critical alerts (stock below threshold, order overdue)

### Phase 3 (future)
- Direct ERP API integration (replace manual exports)
- ML-based pricing model (trained on accumulated quote history)
- Customer credit risk scoring
- Automated dispatch planning and allocation
- Mobile app (React Native, wrapping the same API)

---

## 14. Key constraints and assumptions

1. All monetary values in Indian Rupees (INR). No multi-currency support needed in Phase 1.
2. All weights in metric tonnes (MT) internally. Display in native unit per product (MT / MTS / KME).
3. Financial year runs April–March (e.g. FY 26-27 = April 2026 – March 2027). SO numbers follow this: SO/26-27/XXXXX.
4. Shifts are A shift and B shift (typically 12 hours each). Some machines run single shift.
5. The dashboard is read-only for operations data — no one edits production data through the dashboard. Uploads only.
6. The quote suggestion is advisory only — no approval workflow or logging in Phase 1.
7. All times in IST (Indian Standard Time, UTC+5:30).
8. The system should gracefully handle missing data — show "N/A" or "No data" rather than crashing or showing zero incorrectly.
9. Authentication: simple username/password for Phase 1 (5–10 users). No SSO or complex RBAC needed yet.
10. The product OFC 2F 4.5mm DIA FRP & YARN (and similar OFC products) is NOT currently tracked in the plant MIS — it may be sourced rather than manufactured in-house, or tracked in a system not yet shared. Do not attempt to calculate capacity for OFC from MIS data until confirmed.
