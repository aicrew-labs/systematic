with open("backend/app/database.py", "a", encoding="utf-8") as f:
    f.write('''

def update_user_feedback(user_id: str, feedback: str) -> bool:
    try:
        res = supabase.table("app_users").update({"feedback": feedback}).eq("user_id", user_id).execute()
        return bool(res.data)
    except Exception as e:
        print(f"Error updating feedback for {user_id}: {e}")
        return False
''')
