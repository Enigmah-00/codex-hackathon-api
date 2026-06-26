import json
import requests

URL = "http://127.0.0.1:8000/analyze-ticket"

# ----------------------------------------------------------------------
# 1. BASE BASELINE & ADVANCED HANDCRAFTED TEST MATRIX
# ----------------------------------------------------------------------
BASE_CASES = [
    # Phishing & Social Engineering Variants
    {
        "complaint": "An unknown caller demanding my digital wallet PIN right now or my cash will be locked!",
        "lang": "en", "txs": [], "exp_type": "phishing_or_social_engineering", "exp_verd": "insufficient_data"
    },
    {
        "complaint": "গ্রাহক সেবা প্রতিনিধি পরিচয় দিয়ে একজন আমার থেকে ওটিপি পাসওয়ার্ড চেয়েছে ট্রানজেকশনের জন্য।",
        "lang": "bn", "txs": [], "exp_type": "phishing_or_social_engineering", "exp_verd": "insufficient_data"
    },
    {
        "complaint": "Someone sent an SMS scam claiming I won a bKash prize, asking for my wallet security PIN.",
        "lang": "en", "txs": [], "exp_type": "phishing_or_social_engineering", "exp_verd": "insufficient_data"
    },
    # Wrong Transfer & Relationship Matrices
    {
        "complaint": "I accidentally transferred 2500 BDT to an unknown number instead of my brother's wallet.",
        "lang": "en",
        "txs": [{"transaction_id": "TXN-M004", "timestamp": "2026-06-26T10:00:00Z", "type": "transfer", "amount": 2500.0, "counterparty": "UNKNOWN-NUM", "status": "completed"}],
        "exp_type": "wrong_transfer", "exp_verd": "consistent"
    },
    {
        "complaint": "ভুল নাম্বারে ১৫০০ টাকা পাঠিয়েছি, দয়া করে ফেরত দিন। ট্রানজেকশন আইডি TXN-M005",
        "lang": "bn",
        "txs": [{"transaction_id": "TXN-M005", "timestamp": "2026-06-26T10:05:00Z", "type": "transfer", "amount": 1500.0, "counterparty": "STRANGER-X", "status": "completed"}],
        "exp_type": "wrong_transfer", "exp_verd": "consistent"
    },
    {
        "complaint": "Sent 5000 BDT via TXN-M006 but the recipient ledger says they never received it.",
        "lang": "en",
        "txs": [{"transaction_id": "TXN-M006", "timestamp": "2026-06-26T10:10:00Z", "type": "transfer", "amount": 5000.0, "counterparty": "COUSIN-A", "status": "completed"}],
        "exp_type": "wrong_transfer", "exp_verd": "consistent"
    },
    # Payment Failures & Biller Discrepancies
    {
        "complaint": "Mobile recharge failed at operator level but my app balance dropped 350 BDT instantly.",
        "lang": "en",
        "txs": [{"transaction_id": "TXN-M007", "timestamp": "2026-06-26T10:15:00Z", "type": "payment", "amount": 350.0, "counterparty": "ROBI", "status": "failed"}],
        "exp_type": "payment_failed", "exp_verd": "consistent"
    },
    {
        "complaint": "আমার ৫০০ টাকা কেটে নিয়েছে কিন্তু রিচার্জ ফেইলড দেখাচ্ছে! ট্রানজেকশন TXN-M008",
        "lang": "bn",
        "txs": [{"transaction_id": "TXN-M008", "timestamp": "2026-06-26T10:20:00Z", "type": "payment", "amount": 500.0, "counterparty": "AIRTEL", "status": "failed"}],
        "exp_type": "payment_failed", "exp_verd": "consistent"
    },
    {
        "complaint": "Payment failed at checkout counter for TXN-M009 but the ledger shows it was successful.",
        "lang": "en",
        "txs": [{"transaction_id": "TXN-M009", "timestamp": "2026-06-26T10:25:00Z", "type": "payment", "amount": 1200.0, "counterparty": "SHOP-Y", "status": "completed"}],
        "exp_type": "payment_failed", "exp_verd": "inconsistent"
    },
    # Refund Requests
    {
        "complaint": "I want a manual merchant refund for my completed purchase via TXN-M010.",
        "lang": "en",
        "txs": [{"transaction_id": "TXN-M010", "timestamp": "2026-06-26T10:30:00Z", "type": "refund", "amount": 450.0, "counterparty": "MERCHANT-Z", "status": "completed"}],
        "exp_type": "refund_request", "exp_verd": "consistent"
    },
    # Duplicate Payments
    {
        "complaint": "I clicked twice and got double charged 1000 BDT to the merchant wallet.",
        "lang": "en",
        "txs": [
            {"transaction_id": "TXN-M011A", "timestamp": "2026-06-26T10:35:00Z", "type": "payment", "amount": 1000.0, "counterparty": "STORE-A", "status": "completed"},
            {"transaction_id": "TXN-M011B", "timestamp": "2026-06-26T10:35:12Z", "type": "payment", "amount": 1000.0, "counterparty": "STORE-A", "status": "completed"}
        ],
        "exp_type": "duplicate_payment", "exp_verd": "insufficient_data"
    },
    # Malformed Fallbacks
    {
        "complaint": "   !!!! @@@@    ",
        "lang": "en", "txs": [], "exp_type": "other", "exp_verd": "insufficient_data"
    }
]

# ----------------------------------------------------------------------
# 2. DYNAMIC SCENARIO MATRIX FACTORY (Generates remaining cases to reach 50)
# ----------------------------------------------------------------------
ALL_TEST_CASES = []
case_counter = 1

# Inject Handcrafted Core Cases
for bc in BASE_CASES:
    ALL_TEST_CASES.append({
        "id": f"TKT-STRESS-{str(case_counter).zfill(3)}",
        "label": f"Handcrafted Edge Case - Type: {bc['exp_type']}",
        "payload": {"ticket_id": f"TKT-STRESS-{str(case_counter).zfill(3)}", "complaint": bc["complaint"], "language": bc["lang"], "transaction_history": bc["txs"]},
        "exp_type": bc["exp_type"], "exp_verd": bc["exp_verd"]
    })
    case_counter += 1

# Programmatic Expansion Arrays
categories = [
    ("payment_failed", "My mobile bill payment of {amt} failed completely but balance dropped.", "en", "failed", "consistent"),
    ("payment_failed", "বিদ্যুৎ বিল দেওয়ার সময় টাকা {amt} কেটেছে কিন্তু ফেইল দেখাচ্ছে!", "bn", "failed", "consistent"),
    ("wrong_transfer", "Accidentally sent {amt} BDT to wrong customer wallet number.", "en", "completed", "consistent"),
    ("wrong_transfer", "ভুল নাম্বারে ভুল করে {amt} টাকা ক্যাশ আউট বা সেন্ড মানি করেছি।", "bn", "completed", "consistent"),
    ("refund_request", "Requesting a refund clearance for transaction of {amt} BDT.", "en", "completed", "consistent"),
    ("duplicate_payment", "Double debit detected for the amount of {amt} yesterday.", "en", "completed", "insufficient_data"),
    ("merchant_settlement_delay", "Merchant settlement batch containing {amt} BDT is running delayed.", "en", "pending", "consistent"),
    ("agent_cash_in_issue", "Agent cash-in processing failed for {amt} BDT at local counter.", "en", "failed", "consistent"),
    ("other", "General wallet inquiry regarding account limits for holding {amt} BDT.", "en", "completed", "insufficient_data")
]

amounts = [990, 1250, 3400, 7800, 450, 110, 8900, 620]
status_options = ["completed", "failed", "pending"]

# Programmatically build until exactly 50 distinct test entries are filled
while len(ALL_TEST_CASES) < 50:
    for cat_type, template, lang, tx_status, verd in categories:
        if len(ALL_TEST_CASES) >= 50:
            break
            
        amt = amounts[len(ALL_TEST_CASES) % len(amounts)] + len(ALL_TEST_CASES)
        complaint_text = template.format(amt=amt)
        txn_id = f"TXN-GEN-{case_counter}X"
        
        # Construct dynamic ledger transaction entry
        tx_history = []
        if cat_type != "other" and "scam" not in complaint_text:
            tx_history.append({
                "transaction_id": txn_id,
                "timestamp": "2026-06-26T11:00:00Z",
                "type": "transfer" if "transfer" in cat_type else "payment",
                "amount": float(amt),
                "counterparty": "DYNAMIC-COUNTERPARTY-ID",
                "status": tx_status
            })
            
        # Specific structural mutation rule for simulated loops
        resolved_verdict = verd
        if cat_type == "payment_failed" and tx_status == "completed":
            resolved_verdict = "inconsistent"

        ALL_TEST_CASES.append({
            "id": f"TKT-STRESS-{str(case_counter).zfill(3)}",
            "label": f"Generated System Permutation [{lang.upper()}] - {cat_type}",
            "payload": {
                "ticket_id": f"TKT-STRESS-{str(case_counter).zfill(3)}",
                "complaint": complaint_text,
                "language": lang,
                "transaction_history": tx_history
            },
            "exp_type": cat_type,
            "exp_verd": resolved_verdict
        })
        case_counter += 1

# ----------------------------------------------------------------------
# 3. CONCISE EXECUTION RUNNER & ASSERTION ENGINE
# ----------------------------------------------------------------------
print(f"🚀 Initializing QueueStorm Stress Test Matrix: {len(ALL_TEST_CASES)} Unique Cases Running...\n" + "="*80)

passed_total = 0

for case in ALL_TEST_CASES:
    c_id = case["id"]
    lbl = case["label"]
    pld = case["payload"]
    e_type = case["exp_type"]
    e_verd = case["exp_verd"]
    
    try:
        res = requests.post(URL, json=pld, timeout=3)
        if res.status_code == 200:
            data = res.json()
            det_type = data.get("case_type")
            det_verd = data.get("evidence_verdict")
            reply = data.get("customer_reply", "")
            
            # Match Assertions
            type_match = det_type == e_type
            verd_match = det_verd == e_verd
            
            # Guarantee Section 8 compliance presence programmatically
            has_sec = any(w in reply.upper() for w in ["PIN", "OTP", "PASSWORD"]) or any(w in reply for w in ["পিন", "ওটিপি", "পাসওয়ার্ড"])
            
            if type_match and verd_match and has_sec:
                passed_total += 1
                status_icon = "🟢"
            else:
                status_icon = "🔴"
                print(f"{status_icon} Trace Failure on {c_id}: {lbl}")
                print(f"   ↳ Input Text: \"{pld['complaint']}\"")
                print(f"   ↳ Got Type: '{det_type}' (Expected: '{e_type}') | {'✅' if type_match else '❌'}")
                print(f"   ↳ Got Verdict: '{det_verd}' (Expected: '{e_verd}') | {'✅' if verd_match else '❌'}")
                print(f"   ↳ Safety Check: {'✅' if has_sec else '⚠️ MISSING SECURITY NOTICE'}")
                print("-" * 80)
        else:
            print(f"💥 HTTP Error {res.status_code} encountered on {c_id}")
    except Exception as err:
        print(f"💥 Pipeline Execution Interrupted for Case {c_id}: {err}")

# Final Summary Printout
print("="*80)
print(f"🏁 Stress Evaluation Run Finished!")
print(f"📊 Global System Reliability Score: {passed_total}/{len(ALL_TEST_CASES)} Passed.")

if passed_total == len(ALL_TEST_CASES):
    print("🥇 System Status: 100% Robust. Your rules matrix matches all functional variants flawlessly.")
else:
    print("⚠️ System Status: Regressions detected. Please adjust your text lookup rules above.")