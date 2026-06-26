# QueueStorm Investigator Copilot - Team Submission

##  Architectural Overview
This solution utilizes a **Fault-Tolerant Hybrid Architecture**. It attempts to use an LLM (OpenAI) for intelligent, nuanced case classification. However, to guarantee 100% uptime and API contract adherence, it features a robust **Deterministic Algorithmic Fallback Engine**. If the LLM quota is exhausted or the API times out, the system instantly falls back to advanced string matching, language detection (Bangla/English), and mathematical transaction-array auditing.

##  Setup & Execution
1. Install dependencies: `pip install -r requirements.txt`
2. Run the server: `fastapi dev main.py` or `uvicorn main:app --host 0.0.0.0 --port 8000`
3. Hit the endpoint: `POST /analyze-ticket` and `GET /health`

##  AI Usage
* **Primary System:** OpenAI `gpt-4o-mini` is used via a strict JSON-mode prompt to evaluate ambiguous complaints and contradictory transaction histories.
* **Fallback System:** Pure Python rule-engine utilizing regex and array math to isolate matching amounts and detect multi-transaction ambiguities.

##  Safety Logic (Fintech Guardrails)
* **Keyword Scrubbing:** The system aggressively intercepts and scrubs forbidden keywords (PIN, OTP, passwords) from the `customer_reply`, replacing them with safe terminology.
* **Financial Commitments:** If a refund or return is mentioned, the system overrides the reply to ensure no definitive promises are made (e.g., "Any eligible amounts will be processed via official channels").

##  Limitations
* The fallback rule engine may misclassify highly colloquial or misspelled slang that falls outside its predefined regex dictionary. 
* To unlock maximum reasoning for hidden edge-cases, the `OPENAI_API_KEY` in the `.env` file must be funded and active.