import re

file_path = "backend/app/database.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Remove any existing update_user_feedback blocks
content = re.sub(r'def update_user_feedback.*?return False\n?', '', content, flags=re.DOTALL)

# Append clean version
new_func = """
def update_user_feedback(user_id: str, feedback: str) -> bool:
    try:
        data = {
            "feedback": feedback,
            "feedback_status": "Open",
            "feedback_dev_comments": None
        }
        res = supabase.table("app_users").update(data).eq("user_id", user_id).execute()
        return bool(res.data)
    except Exception as e:
        print(f"Error updating feedback for {user_id}: {e}")
        return False
"""
content += new_func

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
