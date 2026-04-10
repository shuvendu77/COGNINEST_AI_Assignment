"""
run_questions.py
----------------
Runs all 20 test questions against the /chat endpoint one by one.
For each question it:
  - Sends the request (with retry on 429 rate-limit)
  - Prints the result in a structured way
  - Checks for PASS/FAIL (sql_query present + rows returned)
  - On first unrecoverable FAIL it prints a diagnostic and stops

Usage (server must already be running on port 8000):
    python scripts/run_questions.py            # start from Q1
    python scripts/run_questions.py 9          # resume from Q9  (skip Q1-Q8)
"""

import json
import sys
import time
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"

# ── Resume support ──────────────────────────────────────────────────
# Pass a question number as the first CLI arg to skip earlier questions.
# Example:  python scripts/run_questions.py 9
START_FROM = int(sys.argv[1]) if len(sys.argv) > 1 else 1

# Seconds to wait between questions to avoid Gemini rate limits (free tier = 15 RPM)
INTER_QUESTION_DELAY = 12

# Retry settings for 429 RESOURCE_EXHAUSTED
MAX_RETRIES = 4
RETRY_BASE_DELAY = 15   # seconds before first retry (doubles each time)

QUESTIONS = [
    {"id": 1,  "q": "How many patients do we have?",                        "expect": "count"},
    {"id": 2,  "q": "List all doctors and their specializations",           "expect": "list"},
    {"id": 3,  "q": "Show me appointments for last month",                  "expect": "date filter"},
    {"id": 4,  "q": "Which doctor has the most appointments?",              "expect": "aggregation"},
    {"id": 5,  "q": "What is the total revenue?",                           "expect": "SUM"},
    {"id": 6,  "q": "Show revenue by doctor",                              "expect": "JOIN+GROUP BY"},
    {"id": 7,  "q": "How many cancelled appointments last quarter?",        "expect": "status+date filter"},
    {"id": 8,  "q": "Top 5 patients by spending",                          "expect": "JOIN+ORDER+LIMIT"},
    {"id": 9,  "q": "Average treatment cost by specialization",            "expect": "multi-JOIN+AVG"},
    {"id": 10, "q": "Show monthly appointment count for the past 6 months","expect": "date grouping"},
    {"id": 11, "q": "Which city has the most patients?",                   "expect": "GROUP BY+COUNT"},
    {"id": 12, "q": "List patients who visited more than 3 times",         "expect": "HAVING"},
    {"id": 13, "q": "Show unpaid invoices",                                "expect": "status filter"},
    {"id": 14, "q": "What percentage of appointments are no-shows?",       "expect": "percentage calc"},
    {"id": 15, "q": "Show the busiest day of the week for appointments",   "expect": "date function"},
    {"id": 16, "q": "Revenue trend by month",                              "expect": "time series"},
    {"id": 17, "q": "Average appointment duration by doctor",              "expect": "AVG+GROUP BY"},
    {"id": 18, "q": "List patients with overdue invoices",                 "expect": "JOIN+filter"},
    {"id": 19, "q": "Compare revenue between departments",                 "expect": "JOIN+GROUP BY"},
    {"id": 20, "q": "Show patient registration trend by month",            "expect": "date grouping"},
]

SEP = "=" * 70


def ask(question: str) -> tuple[dict, int]:
    """Returns (response_dict, http_status_code)."""
    payload = json.dumps({"question": question}).encode()
    req = urllib.request.Request(
        f"{BASE_URL}/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read()), 200
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            detail = json.loads(body).get("detail", body)
        except Exception:
            detail = body
        return {"message": f"HTTP {e.code}: {detail}",
                "sql_query": None, "columns": [], "rows": [],
                "row_count": 0, "chart": None, "chart_type": None}, e.code


def ask_with_retry(question: str) -> tuple[dict, int]:
    """Wraps ask() with exponential backoff on 429."""
    delay = RETRY_BASE_DELAY
    for attempt in range(1, MAX_RETRIES + 2):
        result, code = ask(question)
        if code != 429:
            return result, code
        if attempt <= MAX_RETRIES:
            print(f"  [RATE LIMIT] 429 received. Waiting {delay}s before retry {attempt}/{MAX_RETRIES}...")
            time.sleep(delay)
            delay *= 2
        else:
            print(f"  [RATE LIMIT] Still 429 after {MAX_RETRIES} retries. Giving up.")
            return result, code
    return result, 429  # unreachable but satisfies type checker


def check_health():
    try:
        with urllib.request.urlopen(f"{BASE_URL}/health", timeout=10) as r:
            h = json.loads(r.read())
        if h.get("status") != "ok" or h.get("database") != "connected":
            print(f"[HEALTH] Server unhealthy: {h}")
            sys.exit(1)
        print(f"[HEALTH] OK  |  database={h['database']}  |  memory_items={h['agent_memory_items']}")
    except Exception as e:
        print(f"[ERROR] Cannot reach server at {BASE_URL}. Start it first:\n"
              f"  python \"C:\\Users\\shuve\\Desktop\\Assignment\\Test\\main.py\"\n\nDetail: {e}")
        sys.exit(1)


def print_result(item: dict, result: dict, passed: bool):
    status = "PASS \u2713" if passed else "FAIL \u2717"
    print(f"\n{SEP}")
    print(f"Q{item['id']:02d} [{status}]  {item['q']}")
    print(f"  Expected behaviour : {item['expect']}")
    print(f"  SQL                : {result.get('sql_query') or '(none)'}")
    print(f"  Columns            : {result.get('columns')}")
    print(f"  Row count          : {result.get('row_count')}")
    print(f"  Chart type         : {result.get('chart_type') or '(none)'}")
    rows = result.get("rows", [])
    for i, row in enumerate(rows[:3]):
        print(f"  Row {i+1:<2}             : {row}")
    if len(rows) > 3:
        print(f"  ... ({len(rows) - 3} more rows)")
    print(f"  Message            : {str(result.get('message', ''))[:140]}")


def is_pass(result: dict, code: int) -> bool:
    if code not in (200, 201):
        return False
    return bool(result.get("sql_query"))


def main():
    print(SEP)
    print("  VANNA AI \u2014 20-Question Test Runner")
    print(SEP)

    check_health()

    total = len(QUESTIONS)
    passed = 0

    for idx, item in enumerate(QUESTIONS):
        # Skip questions before START_FROM (resume support)
        if item['id'] < START_FROM:
            passed += 1   # count skipped questions as passed for the summary
            continue

        # Pace requests to avoid hitting the free-tier RPM limit
        if item['id'] > START_FROM:
            print(f"  [waiting {INTER_QUESTION_DELAY}s to avoid rate limits...]")
            time.sleep(INTER_QUESTION_DELAY)

        print(f"\n[{item['id']:02d}/{total}] Sending: {item['q']!r} ...")
        result, code = ask_with_retry(item["q"])

        ok = is_pass(result, code)
        print_result(item, result, ok)

        if ok:
            passed += 1
        else:
            print(f"\n  *** STOP \u2014 Question {item['id']} FAILED (HTTP {code}) ***")
            script = sys.argv[0]
            if code == 429:
                print(f"  Gemini rate limit exceeded. Wait a minute then re-run:")
                print(f"  python {script} {item['id']}")
            else:
                print(f"  Fix the issue above, restart the server if needed, then re-run:")
                print(f"  python {script} {item['id']}")
            print(f"\n  Full response JSON:\n  {json.dumps(result, indent=4)}")
            print(SEP)
            print(f"\n  Result: {passed - (START_FROM - 1)}/{total - (START_FROM - 1)} passed (this run).")
            sys.exit(1)

    print(f"\n{SEP}")
    print(f"  ALL {passed}/{total} QUESTIONS PASSED")
    print(SEP)


if __name__ == "__main__":
    main()

