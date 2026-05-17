import urllib.request
import json
import sys

if len(sys.argv) < 2:
    print("Usage: python mcp_call.py <method> [args_json]")
    sys.exit(1)

method = sys.argv[1]
args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}

url = "https://stitch.googleapis.com/mcp"
headers = {
    "X-Goog-Api-Key": "AQ.Ab8RN6L-13gTimE1rWwAqsuwKh3Hdznvgj1jUYKzroUopraJyg",
    "Content-Type": "application/json"
}
payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": method,
        "arguments": args
    }
}

req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
try:
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print(json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    print(f"HTTPError: {e.code} - {e.read().decode('utf-8')}")
except Exception as e:
    print(f"Error: {e}")
