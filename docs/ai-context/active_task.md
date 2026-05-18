# Active Task & Context Status

**Project Name:** Quote Intelligence (Systematic)  
**Last Updated:** 2026-05-18 (22:42 PM local time)  

---

## 📌 Project Overview
Quote Intelligence is a real-time, data-driven pricing and quote suggestion system. It integrates locally cached ERP data (invoices, sales orders, finished goods inventory, and machine drawing loads) with daily Raw Material (RM) price inputs (MS Steel, HC Steel, Zinc) to generate automated, highly accurate quote recommendations and dynamic pricing ranges for the sales team.

---

## 🗺️ Shared Roadmap & Current Checklist

- `[x]` **Core ERP Database Schema:** Migrated 599 customers, 1,145 enquiries, and FG inventory to Supabase PostgreSQL.
- `[x]` **Quote Intelligence Backend Engine:** `backend/supabase_etl.py` built for syncing ERP data to Supabase.
- `[x]` **Dashboard Integration:** Connected `poc_mobile.html` directly to Supabase JS client to pull live market signals, machine utilization, and history dynamically.
- `[x]` **Cloud Infrastructure:** Configured and deployed to Railway, serving the FastAPI backend and static HTML frontend under one unified domain.
- `[ ]` **Daily Rates Editor:** Build a UI in the live dashboard to allow the admin to update Daily RM Rates and write them back to Supabase.
- `[ ]` **Replace Stubbed AI Reasoning with Live Claude API:** Integrate actual Anthropic Claude API for reasoning generation in the pricing engine.
- `[ ]` **Auth & Security:** Transition dashboard from `anon` public access to Row Level Security (RLS) authenticated user access.

---

## 💻 Tech Stack & Architecture
* **Backend:** FastAPI + Python (ETL and proxy)
* **Database:** Supabase (PostgreSQL) + `supabase-js`
* **Frontend:** HTML5 + Vanilla JS + Tailwind CSS (`poc_mobile.html` served as `static/index.html`)
* **Hosting/Deploy:** Railway (via Nixpacks) connected to GitHub
* **Intelligence Layer:** Rule-based cost heuristics (Claude API reasoning pending)

---

## 📢 Last Handoff & Where We Left Off

### Status of Last Session (2026-05-18):
- **Massive Milestone:** Fully migrated the local Quote Intelligence POC to a production-ready cloud architecture.
- Pushed the entire ERP dataset into a live Supabase project.
- Connected the mobile dashboard to fetch live data asynchronously from Supabase.
- Connected the GitHub repository (`aicrew-labs/systematic`) to Railway for automatic CI/CD deployments.
- Fixed Railway Nixpacks build issues by reorganizing `requirements.txt` to the root directory.
- **Ready for Next Developer:** The live dashboard is up! The next primary task is allowing the admin to update today's steel and zinc prices directly from the dashboard UI, and refining the AI commentary engine.

---

## 💡 Quick Tips for Future Sessions
* When resuming, tell me:  
  > *"Read `docs/ai-context/active_task.md` to get up to speed, and let's tackle the next uncompleted items on the checklist."*
* Always commit updates to this `docs/ai-context/` directory along with your code changes.
