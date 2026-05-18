# AI Context Tracking Directory (Method B)

This directory is the single source of truth for the AI (Antigravity/Gemini or any future assistant) to understand the project's background, active tasks, architectural decisions, and current progress.

---

## 🤖 Instructions for the AI Agent

> [!IMPORTANT]
> You are in a collaborative, version-controlled git environment. Two developers are working on this project together with your assistance. To preserve context between sessions:
>
> 1. **Read Existing Context:** Before doing *any* work or proposing code changes, search for and read `docs/ai-context/active_task.md` to understand where the last session left off.
> 2. **Check recent walkthroughs:** Look inside the `docs/ai-context/walkthroughs/` folder for the most recent session reports to see what code was written and how it was verified.
> 3. **Keep the Checklist Updated:** When working, update `docs/ai-context/active_task.md` to mark items as in-progress or completed.
> 4. **Generate a Session Walkthrough:** When closing a session or completing a significant milestone, generate a standard markdown walkthrough report inside `docs/ai-context/walkthroughs/` with a filename like `walkthrough_YYYYMMDD_[task_name].md`. Summarize what you changed, how it was verified, and what the immediate next steps are.
> 5. **Update Handoff Status:** Before ending your turn, update the "Last Handoff & Where We Left Off" section in `docs/ai-context/active_task.md`.

---

## 📁 Directory Structure

```text
docs/ai-context/
├── README.md             <-- (This file) Guidelines for the AI agent
├── active_task.md        <-- The current active task, TODO list, and handoff status
└── walkthroughs/         <-- History of completed session reports and verification details
    └── (Example: walkthrough_20260518_daily_rates_modal.md)
```

---

## 🛠️ How to Bootstrap a New Session

When a developer starts a new chat, they will run this command or paste this instruction:
> *"Initialize session: Read `docs/ai-context/README.md` and `docs/ai-context/active_task.md`. Give me a brief summary of where we left off and what is next."*
