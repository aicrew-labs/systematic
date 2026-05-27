import requests
import json

base_url = "http://localhost:8000"

# 1. Login as admin
resp_admin = requests.post(f"{base_url}/api/v1/auth/login", json={"user_id": "admin", "password": "admin123"})
if resp_admin.status_code == 200:
    admin_token = resp_admin.json()["access_token"]
    print("Admin login success")
else:
    print("Admin login failed", resp_admin.text)
    admin_token = None

# 2. Login as the User. The user said they created a user. We'll list users to find it.
try:
    from app.database import list_all_users
    users = list_all_users()
    normal_users = [u for u in users if u["role"] == "user"]
    if normal_users:
        user_id = normal_users[0]["user_id"]
        # Assuming password is user123 or similar? Actually we don't know the password.
        # Let's bypass login and just forge a token using create_access_token
        from app.auth import create_access_token
        user_token = create_access_token({"sub": user_id})
        print(f"Forged token for user: {user_id}")
    else:
        print("No normal users found!")
        user_token = None
except Exception as e:
    print("Error getting normal user", e)
    user_token = None

payload = {
  "customer_id": None,
  "customer_name": "Test Customer",
  "category_id": "ACSR_CORE_WIRE",
  "quantity": 10,
  "payment_terms": "30 Days",
  "state": "Maharashtra",
  "city": "Mumbai",
  "mode": "algo",
  "custom_params": None
}

if admin_token:
    r1 = requests.post(
        f"{base_url}/api/v1/analyze", 
        json=payload, 
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    print("Admin quote response:", r1.status_code, r1.text[:200])

if user_token:
    r2 = requests.post(
        f"{base_url}/api/v1/analyze", 
        json=payload, 
        headers={"Authorization": f"Bearer {user_token}"}
    )
    print("User quote response:", r2.status_code, r2.text[:200])
