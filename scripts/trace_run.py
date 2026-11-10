"""Run the baseline and print the FULL agent loop: every tool call (name+args),
every tool result, and the final answer. For verifying the agent actually uses
its tools. Usage:  python scripts/trace_run.py [--live]
"""
import argparse, json, pathlib, sys, textwrap

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv; load_dotenv()
from tools import set_live
from agent import build_agent
from eval.evaluate import check_plan, GT
from run_baseline import extract_plan


def short(x, n=300):
    s = x if isinstance(x, str) else json.dumps(x)
    return textwrap.shorten(s, width=n, placeholder=" …")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--live", action="store_true"); a = ap.parse_args()
    set_live(a.live)
    scen = json.loads((ROOT / "examples/test1.json").read_text()); c = scen["constraints"]
    msg = (f"{scen['request']}\n\nHard constraints: budget_pp=${c['budget_pp']}, vegan_required={c['vegan_required']}, "
           f"target_hour={c['target_hour']} (24h), max_walk_m={c['max_walk_m']}, party_size={c['party_size']}, "
           f"search near lat={c['area']['lat']}, lon={c['area']['lon']}.")

    print("=" * 78); print(f"AGENT TRACE  (mode={'LIVE' if a.live else 'offline'})"); print("=" * 78)
    print("USER:", scen["request"])
    print("-" * 78)

    agent = build_agent()
    result = agent.invoke({"messages": [("user", msg)]})

    step = 0
    for m in result["messages"]:
        t = m.__class__.__name__
        if t == "AIMessage":
            if getattr(m, "tool_calls", None):
                for tc in m.tool_calls:
                    step += 1
                    print(f"\n[step {step}] 🤖 THINK → CALL TOOL: {tc['name']}")
                    print(f"          args: {short(tc['args'], 200)}")
            if m.content:
                print(f"\n🤖 FINAL ANSWER:\n{textwrap.indent(m.content.strip(), '    ')}")
        elif t == "ToolMessage":
            print(f"          ↳ 🔧 {m.name} RETURNED: {short(m.content, 320)}")

    print("\n" + "=" * 78); print("OBJECTIVE CONSTRAINT CHECK"); print("=" * 78)
    plan = extract_plan(result["messages"][-1].content)
    for s in plan.get("stops", []):
        s["name"] = (GT.get(s.get("venue_id")) or {}).get("name", "(unknown)")
    r = check_plan(plan, c)
    for k, ok in r["checks"].items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {k:9}: {r['details'][k]}")
    print(f"\n  plan: " + " -> ".join(f"{s['name']} ({s['type']})" for s in plan.get("stops", [])))
    print(f"  score={r['score']}  valid={r['valid']}")

    used = [tc["name"] for m in result["messages"] if m.__class__.__name__ == "AIMessage"
            for tc in (getattr(m, "tool_calls", None) or [])]
    print(f"\n  tools called ({len(used)}): {used}")


if __name__ == "__main__":
    main()
