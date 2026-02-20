"""Quick live test of the full pipeline."""

import json
from dotenv import load_dotenv
load_dotenv()

from agent.graph import run_activity_tracker
from evals.run_evals import run_all_evals
from db.database import init_db, save_session, save_activities

init_db()

print("=" * 60)
print("KIDS ACTIVITY TRACKER — LIVE TEST")
print("=" * 60)

# Run with default (Los Altos) location, today mode
print("\n[1/3] Running pipeline (location + weather + search + rank)...")
result = run_activity_tracker(
    time_mode="today",
    location_override={"city": "Los Altos", "state": "California", "lat": 37.3685, "lon": -122.0977},
)

print(f"\n  Location: {result.get('location', {}).get('city')}, {result.get('location', {}).get('state')}")
print(f"  Weather: {result.get('weather', {}).get('temp_f')}°F, {result.get('weather', {}).get('description')}")
print(f"  Mode: {result.get('mode', 'N/A').upper()}")
print(f"  Events found: {len(result.get('ranked_events', []))}")
print(f"  Categories: {list(result.get('categorized_output', {}).keys())}")

# Show a few events
print("\n[2/3] Sample activities:")
for cat, events in result.get("categorized_output", {}).items():
    print(f"\n  --- {cat} ---")
    for e in events[:2]:
        cost_str = "FREE" if e.get("is_free") else f"${e.get('cost', 0):.2f}"
        print(f"    {e.get('name')} | {cost_str} | ★{e.get('rating', 'N/A')} | {e.get('age_suitability')}")
        print(f"      {e.get('why_recommended', '')[:80]}")

# Save to DB and run evals
print("\n[3/3] Running evals...")
session_id = save_session(
    result.get("location", {}),
    result.get("weather", {}),
    result.get("mode", "outdoor"),
    "today",
)
save_activities(session_id, result.get("ranked_events", []))
eval_results = run_all_evals(result, session_id)

# Code evals summary
code = eval_results["code_evals"]
print(f"\n  Code Evals: {code['passed']}/{code['total']} passed ({code['pass_rate']}%)")
for r in code["results"]:
    icon = "✅" if r["passed"] else "❌"
    print(f"    {icon} {r['name']}: {r['details'][:60]}")

# LLM judge summary
judge = eval_results["llm_judge"]
print(f"\n  LLM Judge Score: {judge['score']}/5 ({'PASS' if judge['passed'] else 'FAIL'})")
if judge.get("breakdown"):
    bd = judge["breakdown"]
    for k in ["relevance", "age_appropriateness", "diversity", "description_quality"]:
        if isinstance(bd.get(k), dict):
            print(f"    {k}: {bd[k].get('score', '?')}/5 — {bd[k].get('reasoning', '')[:60]}")

print("\n" + "=" * 60)
print("LIVE TEST COMPLETE")
print("=" * 60)
