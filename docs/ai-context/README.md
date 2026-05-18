# AI Context Tracking Directory (Method B)

This directory is the single source of truth for the AI (Antigravity/Gemini/Claude) to understand the project's background, active tasks, architectural decisions, and current progress.

---

> [!IMPORTANT]
> ### 🚨 CRITICAL AI AGENT BOOTSTRAP RULE (MANDATORY ON FIRST PROMPT)
> You are pair-programming in a shared, multi-developer context. To keep all chat histories and context synced across platforms without violating OS sandbox security:
> 1. **RUN GIT PULL IN THE BACKGROUND:** Immediately run `git pull` silently in the background to fetch your partner's latest code and chat transcripts.
> 2. **READ THE LATEST CHAT TRANSCRIPT:** Search the `docs/ai-context/chats/` folder and read the most recent `.md` file to fully synchronize your memory of the previous session.
> 3. **SUMMARIZE AND REPORT:** Welcome the developer, summarize the state of the project, and outline the immediate next steps from the active roadmap.

---

## 🤖 Instructions for the AI Agent

> [!IMPORTANT]
> You are in a collaborative, version-controlled git environment. Two developers are working on this project together with your assistance. To preserve context between sessions:
>
> 1. **Read Existing Context:** Before doing *any* work or proposing code changes, search for and read `docs/ai-context/active_task.md` to understand where the last session left off.
> 2. **Check recent walkthroughs:** Look inside the `docs/ai-context/walkthroughs/` folder for the most recent session reports to see what code was written and how it was verified.
> 3. **Keep the Checklist Updated:** When working, update `docs/ai-context/active_task.md` to mark items as in-progress or completed.
> 4. **SAVE SESSION TRANSCRIPT ON CLOSE:** When the developer indicates they are ending their session or closing the chat, you must:
>    * Generate a beautiful, chronological markdown summary of the chat and save it in `docs/ai-context/chats/chat_YYYYMMDD_[short_task_name].md`.
>    * Commit and push all changes (code and transcripts) to GitHub using `git push`.
> 5. **Update Handoff Status:** Before ending your turn, update the "Last Handoff & Where We Left Off" section in `docs/ai-context/active_task.md`.

---

## 📁 Directory Structure

```text
docs/ai-context/
├── README.md             <-- (This file) Guidelines for the AI agent
├── active_task.md        <-- The current active task, TODO list, and handoff status
├── chats/                <-- Chronological markdown transcripts of all active sessions
│   └── chat_20260518_context_setup.md
└── walkthroughs/         <-- History of completed session reports and verification details
    └── walkthrough_20260518_setup_git_context.md
```

---

## 🛠️ How to Bootstrap a New Session

When a developer starts a new chat, they will run this command or paste this instruction:
> *"Initialize session: Read `docs/ai-context/README.md` and our latest chat transcript in `docs/ai-context/chats/`. Run git pull to sync, summarize where we left off, and let's start the next task."*
