import json
import requests

# URL of your running FastAPI application
URL = "http://127.0.0.1:8000/analyze-ticket"
FILE_NAME = "SUST_Preli_Sample_Cases.json"

try:
    with open(FILE_NAME, "r", encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"Error: Could not find '{FILE_NAME}' in this folder. Make sure it is spelled correctly.")
    exit()

print(f"🚀 Starting automation testing for {len(data['cases'])} sample cases...\n" + "="*60)

for case in data["cases"]:
    case_id = case["id"]
    label = case["label"]
    payload = case["input"]
    
    print(f"⏳ Testing {case_id}: {label}")
    
    try:
        response = requests.post(URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            res_data = response.json()
            print(f"✅ Success! Status: 200 OK")
            print(f"   ↳ Case Type Detected: {res_data.get('case_type')}")
            print(f"   ↳ Evidence Verdict:  {res_data.get('evidence_verdict')}")
            print(f"   ↳ AI Reply:          {res_data.get('customer_reply')}")
        else:
            print(f"❌ Failed! Status Code: {response.status_code}")
            print(f"   ↳ Error Response: {response.text}")
            
    except Exception as e:
        print(f"💥 Critical Crash while contacting API: {e}")
        
    print("-" * 60)

print("\n🏁 Test run finished!")