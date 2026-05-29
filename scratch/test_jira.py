import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

url = os.getenv('JIRA_URL')
email = os.getenv('JIRA_EMAIL')
api_token = os.getenv('JIRA_API_TOKEN')

if not all([url, email, api_token]):
    print("Missing Jira credentials in .env")
    exit(1)

# Ensure URL doesn't end with a slash for clean concatenation
if url.endswith('/'):
    url = url[:-1]

api_url = f"{url}/rest/api/3/project"

auth = HTTPBasicAuth(email, api_token)
headers = {
    "Accept": "application/json"
}

print(f"Connecting to {api_url}...")
response = requests.request(
    "GET",
    api_url,
    headers=headers,
    auth=auth
)

if response.status_code == 200:
    print("Successfully connected to Jira!")
    projects = response.json()
    print("Found projects:")
    for p in projects:
        print(f" - {p.get('name')} (Key: {p.get('key')})")
else:
    print(f"Failed to connect: {response.status_code}")
    print(response.text)
