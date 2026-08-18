import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.messages import HumanMessage
from agent.orchestrator import build_agent

TEST_CASES_PATH = Path(__file__).parent / "test_cases.json"


def check_response(response: str, test_case: dict) -> tuple[bool, list[str]]:
    failures = []
    response_lower = response.lower()

    for phrase in test_case.get("must_contain", []):
        if phrase.lower() not in response_lower:
            failures.append(f"missing expected phrase: '{phrase}'")

    for phrase in test_case.get("must_not_contain", []):
        if phrase.lower() in response_lower:
            failures.append(f"contains forbidden phrase: '{phrase}'")

    return (len(failures) == 0, failures)


async def run_all():
    test_cases = json.loads(TEST_CASES_PATH.read_text(encoding="utf-8"))
    agent = await build_agent(base_dir=None)

    results = []
    print(f"Running {len(test_cases)} evaluation test cases...\n")

    for case in test_cases:
        print(f"[{case['id']}] {case['query']}")
        try:
            result = await agent.ainvoke(
                {"messages": [HumanMessage(content=case["query"])]}
            )
            response = result["messages"][-1].content
            passed, failures = check_response(response, case)
        except Exception as e:
            passed = False
            failures = [f"agent raised an exception: {e}"]
            response = ""

        status = "PASS" if passed else "FAIL"
        print(f"  -> {status}")
        if not passed:
            for f in failures:
                print(f"     - {f}")
            print(f"     response was: {response[:300]}")
        print()

        results.append({
            "id": case["id"],
            "description": case["description"],
            "passed": passed,
            "failures": failures,
        })

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    print("=" * 50)
    print(f"Summary: {passed_count}/{total} passed")
    for r in results:
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"  [{mark}] {r['id']}")

    return results


if __name__ == "__main__":
    asyncio.run(run_all())