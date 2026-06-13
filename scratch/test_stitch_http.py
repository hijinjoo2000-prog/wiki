import requests
import json

url = "https://stitch.googleapis.com/mcp"
headers = {
    "X-Goog-Api-Key": "AQ.Ab8RN6IlVsIf0hQnEdf0ltX0MydJR8dpje9eO9mF2q-MiLM5Og",
    "Content-Type": "application/json"
}

# Try standard JSON-RPC tools/list
payload = {
    "jsonrpc": "2.0",
    "method": "tools/list",
    "params": {},
    "id": 1
}

try:
    print("Sending tools/list to", url)
    res = requests.post(url, headers=headers, json=payload)
    print("Status:", res.status_code)
    print("Headers:", res.headers)
    print("Body:", res.text[:2000])
except Exception as e:
    print("Error:", e)
