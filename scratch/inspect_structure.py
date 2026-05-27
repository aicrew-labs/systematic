import json
import sys

log_path = r"C:\Users\dkgl1\.gemini\antigravity-ide\brain\9b5e5984-8f12-494f-b02d-f9a61afeb681\.system_generated\logs\transcript.jsonl"

with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            step = json.loads(line)
            tool_calls = step.get("tool_calls", [])
            for tc in tool_calls:
                if tc.get("name") == "run_command":
                    print("Tool call structure:")
                    print(json.dumps(tc, indent=2))
                    sys.exit(0)
        except Exception as e:
            pass
