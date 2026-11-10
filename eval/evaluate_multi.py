"""Two-dataset pilot. Mock results are not evidence of LLM performance."""
import argparse
import json
import pathlib
import statistics
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from dotenv import load_dotenv

load_dotenv()
from eval.itinerary import verify
from multi_agent import MultiAgentRunner, Plan, deterministic_plan


def baseline(scenario, mode, mock):
    runner = MultiAgentRunner(mock=mock)
    state = {"scenario": scenario, "trace": []}
    state.update(runner.discovery(state))
    state.update(runner.enrichment(state))
    state.update(runner.weather(state))
    constraints = scenario["constraints"]
    if mode == "greedy":
        plan = deterministic_plan(state["facts"], constraints, greedy=True)
    elif mock:
        sparse = {venue["id"]: venue for venue in state["candidates"]}
        plan = deterministic_plan(sparse, constraints, greedy=True)
    else:
        plan = runner.call_model(Plan, "Produce an itinerary from this request and supplied venue evidence. "
                                 "Respect requested categories, budget, diet, times and walking limits. "
                                 "Return empty stops if unsupported. No tools or retries are available.",
                                 {"scenario": scenario, "facts": state["facts"]})
    state["plan"] = plan
    state.update(runner.transit(state))
    state["metrics"] = runner.usage
    state["status"] = "candidate"
    state["report"] = verify(state["plan"], constraints, state["facts"])
    return state


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--output", default="artifacts/pilot_results.json")
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error("repeats must be positive")
    datasets = json.loads((ROOT / "eval" / "pilot_scenarios.json").read_text())
    systems = ["multi_agent", "greedy", "sparse_mock" if args.mock else "single_call"]
    rows = []
    for dataset, scenarios in datasets.items():
        for system in systems:
            for scenario in scenarios:
                for repeat in range(args.repeats):
                    started = time.perf_counter()
                    try:
                        result = (MultiAgentRunner(mock=args.mock).run(scenario) if system == "multi_agent"
                                  else baseline(scenario, system, args.mock))
                        report = verify(result["plan"], scenario["constraints"])
                        row = {"dataset": dataset, "system": system, "scenario": scenario["name"],
                               "repeat": repeat, "valid": report["valid"], "score": report["score"],
                               "checks": report["checks"], "status": result["status"],
                               "attempts": result.get("attempts", 1), "usage": result["metrics"],
                               "trace": result["trace"], "plan": result["plan"],
                               "expected_infeasible": scenario.get("expected_infeasible", False),
                               "infeasible_abstention": bool(scenario.get("expected_infeasible", False)
                                                            and result["status"] == "unresolved")}
                    except Exception as error:
                        row = {"dataset": dataset, "system": system, "scenario": scenario["name"],
                               "repeat": repeat, "valid": False, "score": 0, "error": type(error).__name__}
                    row["latency_seconds"] = time.perf_counter() - started
                    rows.append(row)
    summaries = []
    for dataset in datasets:
        for system in systems:
            group = [row for row in rows if row["dataset"] == dataset and row["system"] == system]
            latency = sorted(row["latency_seconds"] for row in group)
            infeasible = [row for row in group if row.get("expected_infeasible")]
            feasible = [row for row in group if not row.get("expected_infeasible")]
            summaries.append({"dataset": dataset, "system": system, "runs": len(group),
                              "mean_score": statistics.mean(row["score"] for row in group),
                              "valid_plan_rate": statistics.mean(row["valid"] for row in group),
                              "feasible_valid_rate": statistics.mean(row["valid"] for row in feasible),
                              "infeasible_abstention_rate": statistics.mean(row.get("infeasible_abstention", False)
                                                                           for row in infeasible) if infeasible else None,
                              "median_seconds": statistics.median(latency),
                              "p95_seconds": latency[max(0, int(len(latency) * .95 + .999) - 1)],
                              "errors": sum("error" in row for row in group)})
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    artifact = {"mode": "mock_deterministic_integration_NOT_LLM" if args.mock else "real_llm_pilot",
                "dataset_note": "Two small authored scenario collections over the same 13-venue annotated snapshot; "
                                "enrichment text is synthetic and correlated with evaluation labels, not a holdout benchmark.",
                "repeats": args.repeats, "summaries": summaries, "runs": rows}
    output.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print(json.dumps({"mode": artifact["mode"], "summaries": summaries}, indent=2))


if __name__ == "__main__":
    main()
