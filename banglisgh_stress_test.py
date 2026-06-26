import json
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Target URL for the locally running FastAPI application
API_URL = "http://127.0.0.1:8000/analyze-ticket"

# ----------------------------------------------------------------------
# BANGLISH STRESS TEST CASES
# ----------------------------------------------------------------------
STRESS_CASES = [
    {
        "ticket_id": "STRESS-BNG-001",
        "complaint": "vai ami bhul number e 5000 tk send money korechi target number chilo 01712345678. please help me get my money.",
        "transaction_history": [
            {
                "transaction_id": "TXN-9101",
                "timestamp": "2026-04-14T14:08:22Z",
                "type": "transfer",
                "amount": 5000.0,
                "counterparty": "+8801719876543",
                "status": "completed"
            }
        ],
        "expected_case": "wrong_transfer",
        "expected_verdict": "consistent"
    },
    {
        "ticket_id": "STRESS-BNG-002",
        "complaint": "amar payment korar shomoy double charge hoye gese 850 taka kete nise twice.",
        "transaction_history": [
            {
                "transaction_id": "TXN-10001",
                "timestamp": "2026-04-14T08:15:30Z",
                "type": "payment",
                "amount": 850.0,
                "counterparty": "BILLER-DESCO",
                "status": "completed"
            },
            {
                "transaction_id": "TXN-10002",
                "timestamp": "2026-04-14T08:15:42Z",
                "type": "payment",
                "amount": 850.0,
                "counterparty": "BILLER-DESCO",
                "status": "completed"
            }
        ],
        "expected_case": "duplicate_payment",
        "expected_verdict": "consistent"
    },
    {
        "ticket_id": "STRESS-BNG-003",
        "complaint": "bhai payment korar shomoy failed dekhisilo kintu balance kete nise please return my taka.",
        "transaction_history": [
            {
                "transaction_id": "TXN-9301",
                "timestamp": "2026-04-14T16:00:00Z",
                "type": "payment",
                "amount": 1200.0,
                "counterparty": "MERCHANT-MOBILE-OP",
                "status": "failed"
            }
        ],
        "expected_case": "payment_failed",
        "expected_verdict": "consistent"
    },
    {
        "ticket_id": "STRESS-BNG-004",
        "complaint": "ekjon phone kore amake bollo bKash theke boltise ebong amar pin r otp chaitese.",
        "transaction_history": [],
        "expected_case": "phishing_or_social_engineering",
        "expected_verdict": "insufficient_data"
    },
    {
        "ticket_id": "STRESS-BNG-005",
        "complaint": "bhai ami agent cash in korsi 2000 tk kintu balance e jog hoyni.",
        "transaction_history": [
            {
                "transaction_id": "TXN-9701",
                "timestamp": "2026-04-14T09:30:00Z",
                "type": "cash_in",
                "amount": 2000.0,
                "counterparty": "AGENT-318",
                "status": "pending"
            }
        ],
        "expected_case": "agent_cash_in_issue",
        "expected_verdict": "consistent"
    }
]

def send_request(case_data):
    """Sends a single POST request to the API and measures response timing."""
    payload = {
        "ticket_id": case_data["ticket_id"],
        "complaint": case_data["complaint"],
        "transaction_history": case_data["transaction_history"]
    }
    start_time = time.perf_counter()
    try:
        response = requests.post(API_URL, json=payload, timeout=3.0)
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        
        if response.status_code == 200:
            res_json = response.json()
            # Perform assertions against expected taxonomy mappings
            case_match = res_json.get("case_type") == case_data["expected_case"]
            verdict_match = res_json.get("evidence_verdict") == case_data["expected_verdict"]
            is_reply_bangla = any(char in res_json.get("customer_reply", "") for char in "কখগঘঙ")
            
            return {
                "success": True,
                "status_code": 200,
                "latency_ms": latency_ms,
                "case_type": res_json.get("case_type"),
                "evidence_verdict": res_json.get("evidence_verdict"),
                "reply": res_json.get("customer_reply"),
                "passed_validation": (case_match and verdict_match and is_reply_bangla)
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "latency_ms": latency_ms,
                "error": response.text
            }
    except Exception as e:
        end_time = time.perf_counter()
        return {
            "success": False,
            "status_code": 0,
            "latency_ms": (end_time - start_time) * 1000,
            "error": str(e)
        }

def run_stress_test(total_requests=100, max_workers=20):
    """Executes multiple API requests concurrently to simulate high load."""
    print("=" * 70)
    print(f"🔥 Starting Banglish Stress Test Suite")
    print(f"   Target URL: {API_URL}")
    print(f"   Total Requests: {total_requests} | Concurrency: {max_workers} workers")
    print("=" * 70)
    
    # Check if target server is live first
    try:
        health = requests.get(API_URL.replace("/analyze-ticket", "/health"), timeout=2.0)
        if health.status_code != 200:
            raise Exception("Health endpoint did not return OK status")
    except Exception as e:
        print(f"❌ Server is offline or inaccessible! Reason: {e}")
        print("   Make sure 'fastapi dev main.py' is running before executing this script.")
        return

    latencies = []
    success_count = 0
    passed_validation_count = 0
    failures = []
    
    start_suite = time.perf_counter()
    
    # Distribute the stress test scenarios evenly across requested load size
    tasks = [STRESS_CASES[i % len(STRESS_CASES)] for i in range(total_requests)]
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(send_request, task): task for task in tasks}
        
        for future in as_completed(futures):
            res = future.result()
            latencies.append(res["latency_ms"])
            if res["success"]:
                success_count += 1
                if res.get("passed_validation"):
                    passed_validation_count += 1
            else:
                failures.append(res)
                
    end_suite = time.perf_counter()
    total_duration_sec = end_suite - start_suite
    
    # Calculate Latency Metrics
    latencies.sort()
    avg_latency = sum(latencies) / len(latencies)
    p50_latency = latencies[int(len(latencies) * 0.50)]
    p95_latency = latencies[int(len(latencies) * 0.95)]
    p99_latency = latencies[int(len(latencies) * 0.99)]
    throughput = total_requests / total_duration_sec

    # ----------------------------------------------------------------------
    # PRINT PERFORMANCE SUMMARY
    # ----------------------------------------------------------------------
    print("\n" + "📊 STRESS TEST RESULTS" + "\n" + "=" * 70)
    print(f"⏱️ Total Duration:       {total_duration_sec:.2f} seconds")
    print(f"📈 Throughput:           {throughput:.2f} req/sec")
    print(f"✅ Success Rate:          {success_count}/{total_requests} ({(success_count/total_requests)*100:.1f}%)")
    print(f"🎯 Rule Accuracy:        {passed_validation_count}/{total_requests} ({(passed_validation_count/total_requests)*100:.1f}%)")
    print("-" * 70)
    print(f"⚡ Average Latency:      {avg_latency:.2f} ms")
    print(f"⚡ Median (p50) Latency:  {p50_latency:.2f} ms")
    print(f"⚡ p95 Tail Latency:     {p95_latency:.2f} ms")
    print(f"⚡ p99 Tail Latency:     {p99_latency:.2f} ms")
    print("=" * 70)

    # Output Sample Response to showcase clean Banglish translation to Bangla script
    print("\n🔍 SAMPLE INTERPRETED RESPONSE (SAMPLE-01 Wrong Transfer):")
    sample_response = send_request(STRESS_CASES[0])
    if sample_response["success"]:
        print(f"   ↳ Case Type: {sample_response['case_type']}")
        print(f"   ↳ Verdict:   {sample_response['evidence_verdict']}")
        print(f"   ↳ Reply:     {sample_response['reply']}")
    print("=" * 70)

    if failures:
        print(f"\n❌ Failures Encountered ({len(failures)}):")
        for idx, fail in enumerate(failures[:5]):
            print(f"   [{idx+1}] Status: {fail['status_code']} | Latency: {fail['latency_ms']:.1f}ms | Error: {fail.get('error')}")

if __name__ == "__main__":
    # Feel free to adjust the load metrics here (e.g., 500 total requests, 50 concurrency)
    run_stress_test(total_requests=100, max_workers=20)