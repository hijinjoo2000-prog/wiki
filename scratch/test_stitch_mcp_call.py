import requests
import json

url = "https://stitch.googleapis.com/mcp"
headers = {
    "X-Goog-Api-Key": "AQ.Ab8RN6IlVsIf0hQnEdf0ltX0MydJR8dpje9eO9mF2q-MiLM5Og",
    "Content-Type": "application/json"
}

payload = {
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
        "name": "list_screens",
        "arguments": {
            "projectId": "1517492827801598489"
        }
    },
    "id": 2
}

try:
    res = requests.post(url, headers=headers, json=payload)
    print("Status:", res.status_code)
    data = res.json()
    print("JSON Response:")
    print(json.dumps(data, indent=2, ensure_ascii=False)[:1500])
except Exception as e:
    print("Error:", e)
