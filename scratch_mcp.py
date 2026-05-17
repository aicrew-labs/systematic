import urllib.request
import json

url = "https://stitch.googleapis.com/mcp"
headers = {
    "X-Goog-Api-Key": "AQ.Ab8RN6L-13gTimE1rWwAqsuwKh3Hdznvgj1jUYKzroUopraJyg",
    "Content-Type": "application/json"
}
data = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).encode('utf-8')

req = urllib.request.Request(url, data=data, headers=headers, method='POST')
try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        with open("mcp_tools.json", "w") as f:
            json.dump(result, f, indent=2)
except Exception as e:
    print(f"Error: {e}")
