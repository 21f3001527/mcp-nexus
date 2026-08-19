import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.messages import HumanMessage
from agent.orchestrator import build_agent


_test_file = sys.argv[1] if len(sys.argv) > 1 else "test_cases.json"

TEST_CASES_PATH = Path(__file__).parent / _test_file

RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_PATH = RESULTS_DIR / "latest.json"
SUMMARY_PATH = RESULTS_DIR / "summary.json"


def extract_tool_calls(messages) -> list[str]:
    """Extract the names of all tools actually called during the agent run."""
    called = []

    for msg in messages:
        tool_calls = getattr(msg, "tool_calls", None)

        if tool_calls:
            for tc in tool_calls:
                called.append(
                    tc.get("name")
                    if isinstance(tc, dict)
                    else tc.name
                )

    return called


def check_response(
    response: str,
    test_case: dict,
    called_tools: list[str],
) -> tuple[bool, list[str]]:

    failures = []

    response_lower = response.lower()

    # must_contain checks
    for phrase in test_case.get("must_contain", []):

        if phrase.lower() not in response_lower:

            failures.append(
                f"missing expected phrase: '{phrase}'"
            )

    # must_not_contain checks
    for phrase in test_case.get("must_not_contain", []):

        if phrase.lower() in response_lower:

            failures.append(
                f"contains forbidden phrase: '{phrase}'"
            )

    # expected tool checks
    for tool_name in test_case.get("expected_tools", []):

        if tool_name not in called_tools:

            failures.append(
                f"expected tool '{tool_name}' was not actually called "
                f"(called: {called_tools})"
            )

    # forbidden tool checks
    for tool_name in test_case.get("forbidden_tools", []):

        if tool_name in called_tools:

            failures.append(
                f"forbidden tool '{tool_name}' was called but should not "
                f"have been (called: {called_tools})"
            )

    return len(failures) == 0, failures


def classify_error(exc: Exception) -> str:
    """Classify infrastructure/API errors separately from agent failures."""

    error_text = str(exc).lower()

    if "429" in error_text or "rate_limit" in error_text:
        return "rate_limit"

    if "timeout" in error_text:
        return "timeout"

    if "connection" in error_text:
        return "connection_error"

    return "runtime_error"


def extract_error_message(exc: Exception) -> str:
    return str(exc)


def calculate_summary(
    results: list[dict],
    total_tests: int,
) -> dict:

    passed_count = sum(
        1
        for r in results
        if r["status"] == "PASS"
    )

    failed_count = sum(
        1
        for r in results
        if r["status"] == "FAIL"
    )

    error_count = sum(
        1
        for r in results
        if r["status"] == "ERROR"
    )

    completed_count = passed_count + failed_count

    if completed_count:

        behavioral_pass_rate = (
            passed_count / completed_count
        ) * 100

    else:

        behavioral_pass_rate = 0.0

    return {
        "total": total_tests,
        "completed": completed_count,
        "remaining": total_tests - completed_count,
        "passed": passed_count,
        "failed": failed_count,
        "errors": error_count,
        "behavioral_pass_rate": round(
            behavioral_pass_rate,
            2,
        ),
    }


def save_results(
    results: list[dict],
    test_cases: list[dict],
):

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary = calculate_summary(
        results,
        len(test_cases),
    )

    timestamp = datetime.now(
        timezone.utc
    ).isoformat()

    # --------------------------------------------------
    # Save detailed results
    # --------------------------------------------------

    output = {
        "timestamp": timestamp,
        "summary": summary,
        "tests": results,
    }

    RESULTS_PATH.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    # --------------------------------------------------
    # Save separate summary
    # --------------------------------------------------

    summary_output = {
        "timestamp": timestamp,
        "summary": summary,
    }

    SUMMARY_PATH.write_text(
        json.dumps(
            summary_output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def load_previous_results() -> list[dict]:

    if not RESULTS_PATH.exists():
        return []

    try:

        data = json.loads(
            RESULTS_PATH.read_text(
                encoding="utf-8"
            )
        )

        return data.get("tests", [])

    except (json.JSONDecodeError, OSError):

        print(
            "Warning: Could not read previous results. "
            "Starting fresh."
        )

        return []


async def run_all():

    test_cases = json.loads(
        TEST_CASES_PATH.read_text(
            encoding="utf-8"
        )
    )

    RESULTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------
    # Load previous results
    # --------------------------------------------------

    previous_results = load_previous_results()

    # Map test ID -> previous result
    previous_by_id = {
        result["id"]: result
        for result in previous_results
    }

    # Keep completed results
    results = []

    for case in test_cases:

        previous = previous_by_id.get(
            case["id"]
        )

        if previous and previous["status"] in {
            "PASS",
            "FAIL",
        }:

            results.append(previous)

    completed_ids = {
        result["id"]
        for result in results
    }

    total_tests = len(test_cases)

    print(
        f"Running {total_tests} evaluation test cases...\n"
    )

    if completed_ids:

        print(
            f"Resuming evaluation: "
            f"{len(completed_ids)} completed test(s) "
            f"will be skipped.\n"
        )

    # --------------------------------------------------
    # Build agent
    # --------------------------------------------------

    agent = await build_agent(
        base_dir=None
    )

    # --------------------------------------------------
    # Run tests
    # --------------------------------------------------

    for index, case in enumerate(
        test_cases,
        start=1,
    ):

        test_id = case["id"]

        # ----------------------------------------------
        # Skip already completed tests
        # ----------------------------------------------

        if test_id in completed_ids:

            previous = previous_by_id[test_id]

            print(
                f"[{index}/{total_tests}] "
                f"[{test_id}] "
                f"SKIP ({previous['status']})"
            )

            continue

        # ----------------------------------------------
        # Run test
        # ----------------------------------------------

        print(
            f"[{index}/{total_tests}] "
            f"[{test_id}] "
            f"{case['query']}"
        )

        response = ""
        called_tools = []
        failures = []
        error = None
        error_type = None

        status = "ERROR"

        try:

            result = await agent.ainvoke(
                {
                    "messages": [
                        HumanMessage(
                            content=case["query"]
                        )
                    ]
                }
            )

            response = result[
                "messages"
            ][-1].content

            called_tools = extract_tool_calls(
                result["messages"]
            )

            passed, failures = check_response(
                response,
                case,
                called_tools,
            )

            status = (
                "PASS"
                if passed
                else "FAIL"
            )

        except Exception as exc:

            error_type = classify_error(
                exc
            )

            error = extract_error_message(
                exc
            )

            status = "ERROR"

        print(
            f"  -> {status}"
        )

        if called_tools:

            print(
                f"     tools called: "
                f"{called_tools}"
            )

        if failures:

            for failure in failures:

                print(
                    f"     - {failure}"
                )

        if error:

            print(
                f"     - {error_type}: "
                f"{error}"
            )

        if response and status != "PASS":

            print(
                f"     response was: "
                f"{response[:300]}"
            )

        print()

        # ----------------------------------------------
        # Remove old result for this test if present
        # ----------------------------------------------

        results = [
            r
            for r in results
            if r["id"] != test_id
        ]

        # ----------------------------------------------
        # Store new result
        # ----------------------------------------------

        results.append(
            {
                "id": test_id,
                "query": case["query"],
                "description": case[
                    "description"
                ],
                "status": status,
                "passed": status == "PASS",
                "response": response,
                "called_tools": called_tools,
                "failures": failures,
                "error": error,
                "error_type": error_type,
            }
        )

        # ----------------------------------------------
        # Save immediately
        # ----------------------------------------------

        save_results(
            results,
            test_cases,
        )

        # ----------------------------------------------
        # Stop on rate limit
        # ----------------------------------------------

        if error_type == "rate_limit":

            print(
                "\nRate limit detected."
            )

            print(
                "Progress has been saved."
            )

            print(
                "Run the evaluator again after "
                "the limit resets to resume."
            )

            return results

    # --------------------------------------------------
    # Final summary
    # --------------------------------------------------

    print("=" * 60)

    summary = calculate_summary(
        results,
        total_tests,
    )

    print(
        "Evaluation Summary"
    )

    print("-" * 60)

    print(
        f"Total tests:             "
        f"{summary['total']}"
    )

    print(
        f"Completed:               "
        f"{summary['completed']}"
    )

    print(
        f"Remaining:               "
        f"{summary['remaining']}"
    )

    print(
        f"Passed:                  "
        f"{summary['passed']}"
    )

    print(
        f"Failed:                  "
        f"{summary['failed']}"
    )

    print(
        f"Infrastructure errors:  "
        f"{summary['errors']}"
    )

    print(
        f"Behavioral pass rate:    "
        f"{summary['behavioral_pass_rate']:.2f}%"
    )

    print()

    for result in results:

        print(
            f"  [{result['status']}] "
            f"{result['id']}"
        )

    # Final save
    save_results(
        results,
        test_cases,
    )

    print()

    print(
        f"Detailed results saved to: "
        f"{RESULTS_PATH}"
    )

    print(
        f"Summary saved to: "
        f"{SUMMARY_PATH}"
    )

    return results


if __name__ == "__main__":
    asyncio.run(run_all())