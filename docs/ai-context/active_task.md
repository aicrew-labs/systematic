# Active Task & Context Status

**Project Name:** Quote Intelligence (Systematic)  
**Last Updated:** 2026-05-18 (22:42 PM local time)  

---

## 📌 Project Overview
Quote Intelligence is a real-time, data-driven pricing and quote suggestion system. It integrates locally cached ERP data (invoices, sales orders, finished goods inventory, and machine drawing loads) with daily Raw Material (RM) price inputs (MS Steel, HC Steel, Zinc) to generate automated, highly accurate quote recommendations and dynamic pricing ranges for the sales team.

---

## 🗺️ Shared Roadmap & Current Checklist

- `[x]` **Core ERP Database Schema:** Models for `Customer`, `Product`, `QuoteHistory`, `FGInventory`, `Machine`, and `RMPrice` defined in SQLAlchemy.
- `[x]` **Quote Intelligence Backend Engine:** `backend/app/services/quote_engine.py` complete with cost floor, conversion costs, machine drawing utilisation check, FG stock availability, and outcome analysis.
- `[x]` **Daily RM Rates Backend API:** API endpoints to get and set current daily steel and zinc prices.
- `[x]` **Daily Rates Frontend Modal:** `DailyRatesModal.jsx` component completed in React, connected to API client for setting dynamic rates in the database.
- `[ ]` **Trigger Daily Rates Modal:** Connect the modal to the main dashboard's configuration/settings trigger.
- `[ ]` **Frontend Quoting Form Integration:** Connect the React frontend form inputs to the FastAPI quote engine endpoint.
- `[ ]` **Replace Stubbed AI Reasoning with Live Claude API:** Integrate actual Anthropic Claude API for reasoning generation in `quote_engine.py` (currently using sophisticated mock-context generation).
- `[ ]` **End-to-End Dynamic Cost Flow Testing:** Validate that updating RM Rates in the frontend immediately shifts the generated suggested pricing range for new quotes.

---

## 💻 Tech Stack & Architecture
* **Backend:** FastAPI + SQLAlchemy (SQLite/PostgreSQL database)
* **Frontend:** Vite + React + Tailwind CSS
* **Intelligence Layer:** Rule-based cost heuristics + Claude API reasoning (currently stubbed)
* **Hosting/Deploy:** Netlify (for frontend) and production FastAPI hosting

---

## 📢 Last Handoff & Where We Left Off

### Status of Last Session (2026-05-18):
- Completed the core infrastructure for Method B (Git-Based AI Context Sync).
- Created `docs/ai-context/README.md` to guide future AI agents.
- Initialized `docs/ai-context/active_task.md` (this file) with the exact state of the backend quote suggestion engine and the frontend `DailyRatesModal`.
- **Ready for Next Developer:** The project is primed to wire the `DailyRatesModal` trigger button on the dashboard, connect the React quoting form to the backend pricing engine, or configure the Claude API key for live AI quote reasoning.

---

## 💡 Quick Tips for Future Sessions
* When resuming, tell me:  
  > *"Read `docs/ai-context/active_task.md` to get up to speed, and let's tackle the next uncompleted items on the checklist."*
* Always commit updates to this `docs/ai-context/` directory along with your code changes.
