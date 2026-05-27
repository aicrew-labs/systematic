import json
import os

log_path = r"C:\Users\dkgl1\.gemini\antigravity-ide\brain\9b5e5984-8f12-494f-b02d-f9a61afeb681\.system_generated\logs\transcript.jsonl"

with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            step = json.loads(line)
            step_idx = step.get('step_index', 0)
            if step_idx >= 400:
                continue
            tool_calls = step.get("tool_calls", [])
            for tc in tool_calls:
                if tc.get("name") == "run_command":
                    args = tc.get("args", {})
                    cmd = args.get("CommandLine", "")
                    if cmd.startswith('"') and cmd.endswith('"'):
                        cmd = cmd[1:-1]
                    if any(x in cmd.lower() for x in ["python", "migration", "seed", "sql", "supabase"]):
                        print(f"Step {step_idx}: {cmd}")
        except Exception as e:
            pass
