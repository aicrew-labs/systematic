import re

file_path = "backend/app/database.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Update update_user_feedback to accept status and not wipe dev_comments
old_func = r"""def update_user_feedback\(user_id: str, feedback: str\) -> bool:
    try:
        data = {
            "feedback": feedback,
            "feedback_status": "Open",
            "feedback_dev_comments": None
        }
        res = supabase\.table\("app_users"\)\.update\(data\)\.eq\("user_id", user_id\)\.execute\(\)"""

new_func = """def update_user_feedback(user_id: str, feedback: str, status: str = None) -> bool:
    try:
        data = {"feedback": feedback}
        if status:
            data["feedback_status"] = status
        else:
            # If no status provided, just default to Open if we are creating new feedback
            # but usually it's better to leave the status alone if they don't change it.
            # However, the requirement is they can change it. Let's just set it to Open if None.
            data["feedback_status"] = "Open"
            
        res = supabase.table("app_users").update(data).eq("user_id", user_id).execute()"""

content = re.sub(old_func, new_func, content, flags=re.DOTALL)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated database.py")
