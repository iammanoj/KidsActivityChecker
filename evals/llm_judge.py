"""LLM-as-judge evaluation using OpenAI GPT-4o."""

import json
import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from .rubric import JUDGE_SYSTEM_PROMPT, JUDGE_USER_TEMPLATE


def format_activities_for_judge(categorized: dict) -> str:
    """Format categorized activities into readable text for the judge."""
    lines = []
    for cat, events in categorized.items():
        lines.append(f"\n## {cat}")
        for i, e in enumerate(events, 1):
            cost_str = "FREE" if e.get("is_free") else f"${e.get('cost', 0):.2f}"
            lines.append(
                f"  {i}. {e.get('name', 'Unknown')} | {cost_str} | "
                f"★{e.get('rating', 'N/A')} | {e.get('age_suitability', '?')} | "
                f"{e.get('distance_miles', '?')} mi"
            )
            lines.append(f"     Why: {e.get('why_recommended', 'N/A')}")
    return "\n".join(lines)


def run_llm_judge(state: dict) -> dict:
    """Run GPT-4o judge on the agent's output.

    Returns dict with scores and reasoning.
    """
    categorized = state.get("categorized_output", {})
    location = state.get("location", {})
    weather = state.get("weather", {})
    mode = state.get("mode", "outdoor")
    time_mode = state.get("time_mode", "today")

    if not categorized:
        return {
            "name": "llm_judge",
            "eval_type": "llm_judge",
            "passed": False,
            "score": 0,
            "details": "No activities to evaluate",
        }

    activities_text = format_activities_for_judge(categorized)

    mode_description = "outdoor activities" if mode == "outdoor" else "indoor activities"
    user_msg = JUDGE_USER_TEMPLATE.format(
        city=location.get("city", "Los Altos"),
        state=location.get("state", "California"),
        temp_f=weather.get("temp_f", "N/A"),
        condition=weather.get("condition", "N/A"),
        mode=mode,
        mode_description=mode_description,
        time_mode=time_mode,
        activities_text=activities_text,
    )

    llm = ChatOpenAI(
        model="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.1,
        max_tokens=1000,
    )

    try:
        response = llm.invoke([
            SystemMessage(content=JUDGE_SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ])

        text = response.content.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
            text = text.rsplit("```", 1)[0]

        scores = json.loads(text)
        overall = scores.get("overall_score", 0)

        return {
            "name": "llm_judge",
            "eval_type": "llm_judge",
            "passed": overall >= 3.5,
            "score": overall,
            "details": json.dumps(scores),
            "breakdown": scores,
        }

    except Exception as e:
        return {
            "name": "llm_judge",
            "eval_type": "llm_judge",
            "passed": False,
            "score": 0,
            "details": f"Judge error: {e}",
        }
