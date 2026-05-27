"""
Seed script: Create default admin user in app_users table.
Run once after migration 012_app_users.sql.
"""
import os
import sys
from passlib.context import CryptContext
from supabase import create_client

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY env vars required.")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

DEFAULT_USERS = [
    {
        "user_id": "admin",
        "password": pwd_context.hash("admin123"),
        "full_name": "Admin User",
        "email": "admin@systematicltd.com",
        "role": "admin",
        "is_active": True,
    },
]

def seed():
    for user in DEFAULT_USERS:
        # Check if user already exists
        existing = (
            supabase.table("app_users")
            .select("id")
            .eq("user_id", user["user_id"])
            .execute()
        )
        if existing.data:
            print(f"User '{user['user_id']}' already exists, skipping.")
            continue

        res = supabase.table("app_users").insert(user).execute()
        if res.data:
            print(f"Created user '{user['user_id']}' successfully.")
        else:
            print(f"Failed to create user '{user['user_id']}'.")

if __name__ == "__main__":
    seed()
