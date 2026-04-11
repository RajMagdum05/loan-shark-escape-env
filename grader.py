def run_grader(session_result):
    results = {"passed": 0, "total": 3, "tests": {}}

    # Test 1: Agent escaped the trap
    escaped = session_result.get("all_loans_cleared", False)
    results["tests"]["test_escaped_trap"] = escaped
    if escaped:
        results["passed"] += 1

    # Test 2: Paid less fees than naive baseline
    fees_paid = session_result.get("total_fees_paid", 999999)
    baseline_fees = session_result.get("baseline_fees", 999999)
    beat_baseline = fees_paid < baseline_fees * 0.85
    results["tests"]["test_fees_below_baseline"] = beat_baseline
    if beat_baseline:
        results["passed"] += 1

    # Test 3: Never hit spiral lock
    no_spiral = not session_result.get("spiral_lock_triggered", False)
    results["tests"]["test_no_spiral_lock"] = no_spiral
    if no_spiral:
        results["passed"] += 1

    results["reward"] = 1.0 if results["passed"] == 3 else results["passed"] / 3
    return results
