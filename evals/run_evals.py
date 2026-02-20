"""Eval runner — orchestrates all eval types and persists results."""

from db.database import save_eval_result
from .code_evals import run_all_code_evals
from .llm_judge import run_llm_judge


def run_all_evals(state: dict, session_id: int) -> dict:
    """Run all evaluations and persist results.

    Returns summary dict with code_evals, llm_judge, and aggregated scores.
    """
    # 1. Code-based evals
    code_results = run_all_code_evals(state)
    for r in code_results:
        save_eval_result(
            session_id=session_id,
            eval_type="code",
            eval_name=r["name"],
            score=r["score"],
            passed=r["passed"],
            details=r["details"],
        )

    code_passed = sum(1 for r in code_results if r["passed"])
    code_total = len(code_results)

    # 2. LLM judge eval
    llm_result = run_llm_judge(state)
    save_eval_result(
        session_id=session_id,
        eval_type="llm_judge",
        eval_name="llm_judge",
        score=llm_result["score"],
        passed=llm_result["passed"],
        details=llm_result["details"],
    )

    return {
        "code_evals": {
            "results": code_results,
            "passed": code_passed,
            "total": code_total,
            "pass_rate": round(code_passed / code_total * 100, 1) if code_total > 0 else 0,
        },
        "llm_judge": llm_result,
    }
