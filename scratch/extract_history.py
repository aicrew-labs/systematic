import json
import os

input_file = r"C:\Users\dkgl1\.gemini\antigravity-ide\brain\924d7f0f-e102-4025-8d03-cf3698b06852\.system_generated\logs\transcript.jsonl"
output_file = r"c:\Personal\Projects\systematic\systematic\chat_history.md"

with open(input_file, 'r', encoding='utf-8') as fin, open(output_file, 'w', encoding='utf-8') as fout:
    fout.write("# Chat History\n\n")
    for line in fin:
        if not line.strip(): continue
        try:
            data = json.loads(line)
        except:
            continue
            
        source = data.get("source")
        type_ = data.get("type")
        content = data.get("content")
        
        if not content: continue
        
        if source == "USER_EXPLICIT" and type_ == "USER_INPUT":
            # Extract only the user request part if it has xml tags
            if "<USER_REQUEST>" in content:
                content = content.split("<USER_REQUEST>")[1].split("</USER_REQUEST>")[0].strip()
            fout.write(f"## User\n\n{content}\n\n")
        elif source == "MODEL" and type_ == "PLANNER_RESPONSE":
            fout.write(f"## Assistant\n\n{content}\n\n")

print(f"History written to {output_file}")
