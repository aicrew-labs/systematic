import requests

base_url = "http://localhost:8000"

resp_admin = requests.post(f"{base_url}/api/v1/auth/login", json={"user_id": "admin", "password": "admin123"})
if resp_admin.status_code == 200:
    admin_token = resp_admin.json()["access_token"]
    print("Admin login success")
else:
    print("Admin login failed", resp_admin.text)
    exit(1)

headers = {"Authorization": f"Bearer {admin_token}"}

endpoints = [
    "/api/v1/customers",
    "/api/v1/config/product-costs",
    "/api/v1/locations",
    "/api/v1/rates"
]

for ep in endpoints:
    r = requests.get(base_url + ep, headers=headers)
    print(f"{ep}: {r.status_code}")
    if r.status_code != 200:
        print(f"Error for {ep}: {r.text}")
