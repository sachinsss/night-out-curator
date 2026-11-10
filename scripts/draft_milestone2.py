"""Generate an explicitly preliminary report from measured artifacts, not invented results."""
import argparse
import html
import json
import pathlib
import subprocess
import tempfile
from datetime import date

from docx import Document
from docx.shared import Inches, Pt
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "artifacts"
REPORTS = ROOT / "reports"


def architecture():
    image = Image.new("RGB", (1400, 950), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("C:/Windows/Fonts/calibri.ttf", 27)
    small = ImageFont.truetype("C:/Windows/Fonts/calibri.ttf", 22)
    nodes = [
        (60, "Discovery", "Venue search; catalog radius filter"),
        (190, "Enrichment", "Approved URL lookup; page facts; LLM or mock extractor"),
        (320, "Weather", "Bundled hourly conditions"),
        (450, "Planner", "Structured LLM proposal or deterministic mock policy"),
        (580, "Transit", "All-leg walking checks; unverified transit observations"),
        (710, "Critic", "Deterministic constraint checks; bounded replan")]
    for position, title, description in nodes:
        draw.rectangle((100, position, 1100, position + 80), fill="#eaf2f0", outline="#24725c", width=3)
        draw.text((120, position + 7), title, fill="#172624", font=font)
        draw.text((120, position + 43), description, fill="#172624", font=small)
        if position < 710:
            draw.line((600, position + 80, 600, position + 130), fill="#24725c", width=3)
            draw.polygon([(593, position + 121), (607, position + 121), (600, position + 130)], fill="#24725c")
    draw.line([(1100, 750), (1250, 750), (1250, 490), (1100, 490)], fill="#a13b36", width=4)
    draw.text((1130, 610), "retry", fill="#a13b36", font=font)
    draw.text((100, 825), "Shared state: constraints, candidates, evidence, plan, trace, attempts, checks", fill="#172624", font=small)
    draw.text((100, 865), "Implemented sequential LangGraph nodes; not five independent LLM agents.", fill="#172624", font=small)
    draw.text((100, 900), "Pending: global web search, verified transit, preference memory, alternatives.", fill="#a13b36", font=small)
    path = ARTIFACTS / "architecture.png"
    image.save(path)
    return path


def evidence_page(artifact):
    cases = [next(row for row in artifact["runs"] if row["system"] == "multi_agent" and row["repeat"] == 0
                  and row["scenario"] == name) for name in ["recover_bad_proposal", "impossible_budget"]]
    sections = []
    for case in cases:
        events = [event for event in case["trace"] if event["node"] in {"planner", "transit", "critic"}]
        if case["scenario"] == "impossible_budget":
            events = events[-3:]
        content = (f'Status: {case["status"]}; attempts: {case["attempts"]}\n'
               f'Independent ground-truth checks: {json.dumps(case["checks"])}\n\n'
               + '\n\n'.join(event["node"].upper() + '\n' + json.dumps(event["observation"])
                      for event in events))
        sections.append(f'<section id="{case["scenario"]}"><h2>{html.escape(case["scenario"])}</h2>'
                        f'<pre>{html.escape(content)}</pre></section>')
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Actual pilot execution evidence</title>'
            '<style>body{font-family:Consolas,monospace;margin:28px;color:#172624;background:#f4f7f6}'
            'h1{font-size:24px}h2{font-size:20px}pre{white-space:pre-wrap;font-size:14px;line-height:1.4}'
            'section{padding:20px;background:white;border:1px solid #a8b8b3;margin:24px 0;max-width:1100px}'
            '</style></head><body><h1>Night-Out Curator: saved integration-run evidence</h1>'
            '<p>MOCK MODE: deterministic test policy, no LLM calls. Rendered from artifacts/pilot_results.json.</p>'
            + ''.join(sections) + '</body></html>')
    (ARTIFACTS / "execution_evidence.html").write_text(page, encoding="utf-8")
    for name, content in zip(["recovery", "failure"], sections):
        standalone = page.replace(''.join(sections), content)
        (ARTIFACTS / f"{name}_evidence.html").write_text(standalone, encoding="utf-8")


def capture_evidence():
    browser = pathlib.Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
    if not browser.exists():
        raise FileNotFoundError("Set a local Chromium browser path before capturing report evidence")
    with tempfile.TemporaryDirectory(prefix="nightout-screenshot-", ignore_cleanup_errors=True) as profile:
        for name in ["recovery", "failure"]:
            subprocess.run([str(browser), "--headless", "--disable-gpu", "--hide-scrollbars",
                            "--window-size=1200,900", f"--user-data-dir={profile}",
                            f"--screenshot={ARTIFACTS / (name + '_screenshot.png')}",
                            (ARTIFACTS / f"{name}_evidence.html").as_uri()],
                           check=True, capture_output=True, timeout=60)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--template", default=r"C:\Users\Sachin SS\Downloads\CSE598-capstone-milestone2-template.docx")
    parser.add_argument("--capture", action="store_true")
    args = parser.parse_args()
    artifact = json.loads((ARTIFACTS / "pilot_results.json").read_text())
    ARTIFACTS.mkdir(exist_ok=True)
    REPORTS.mkdir(exist_ok=True)
    evidence_page(artifact)
    if args.capture:
        capture_evidence()
    figure = architecture()
    document = Document(args.template) if pathlib.Path(args.template).exists() else Document()
    for element in list(document.element.body):
        if element.tag.split('}')[-1] != "sectPr":
            document.element.body.remove(element)
    section = document.sections[0]
    section.top_margin = section.bottom_margin = Inches(.65)
    document.styles["Normal"].font.name = "Calibri"
    document.styles["Normal"].font.size = Pt(11)
    document.styles["Normal"].paragraph_format.space_after = Pt(6)
    markdown = []

    def heading(text, level=1):
        document.add_heading(text, level)
        markdown.append("#" * level + " " + text + "\n")

    def paragraph(text):
        document.add_paragraph(text)
        markdown.append(text + "\n")

    def table(headers, rows):
        output = document.add_table(rows=1, cols=len(headers))
        output.style = "Table Grid"
        for cell, value in zip(output.rows[0].cells, headers):
            cell.text = value
        for row in rows:
            for cell, value in zip(output.add_row().cells, row):
                cell.text = str(value)
        markdown.append("| " + " | ".join(headers) + " |\n| " + " | ".join(["---"] * len(headers)) + " |")
        markdown.extend("| " + " | ".join(map(str, row)) + " |" for row in rows)
        markdown.append("")

    def new_page():
        document.add_page_break()

    heading("Night-Out Curator - Milestone 2 Preliminary Draft")
    paragraph(f"Generated {date.today().isoformat()}. This is an evidence-based working draft, not a submission-ready claim of completed LLM evaluation.")
    paragraph("Team: Sachin Shivanand Shankarikoppa; Sushanth Urubailu Vasudeva; Vivek Vidyadhar Kamath; Naga Sai Rama Srikar Vinjanampati; Sri Sai Chetana Reddy Janagan.")
    paragraph("Stakeholder: Mitul Krishna Balamurugan, as named in the submitted Milestone 1 report. Milestone 2 follow-up date and attendance: pending actual meeting.")
    heading("Section 1. Stakeholder Follow-Up and Final Deliverables")
    paragraph("Milestone 1 documented an initial meeting on October 3, 2026 and a proposed Phoenix-area multi-stop planner. Its architecture section described specialized nodes, but its final sentence also reserved multi-agent work for the future. This prototype implements a bounded hybrid graph as the next step; scope changes require stakeholder confirmation.")
    paragraph("No new stakeholder meeting or approval is evidenced in the current repository. At follow-up, present the invalid-proposal recovery trace, the page-timeout case, and the standard/stress pilot table. Record which behaviors are useful and which remain unmet before replacing this pending section with actual notes.")
    table(["Milestone 1 need / proposed review", "Team response", "Next action"], [
        ["User-requested multi-stop plan", "Supports 1-4 explicit stop categories", "Confirm supported categories and pilot limit"],
        ["Verify and re-plan", "Deterministic Critic plus bounded graph loop", "Review recovery trace with stakeholder"],
        ["Better venue information", "Fixture extraction and approved-page retrieval", "Collect independent dated evidence"],
        ["Reliable affordable output", "Trace and token fields; real costs pending", "Run real model and review thresholds"]])
    paragraph("Expected final deliverables proposed for confirmation: runnable hybrid planner, independent scenario/evidence sets, two real baseline comparisons, human ratings, reproducible traces and setup instructions, report, presentation and demo. Meeting notes, participants, feedback and explicit scope approval remain to be supplied.")

    new_page()
    heading("Section 2. Implemented Agentic System")
    paragraph("The new LangGraph StateGraph runs Discovery -> Enrichment -> Weather -> Planner -> Transit -> Critic. The Critic conditionally returns to Planner until a plan passes or the default eight-attempt budget is exhausted. Specialist discovery, weather and transit nodes execute tools deterministically. Enrichment and Planner have structured LLM paths, but the measured runs used deterministic test doubles. This is a hybrid architecture, not five autonomous LLM agents.")
    document.add_picture(str(figure), width=Inches(6.3))
    paragraph("Figure 1. Implemented sequential graph and retry edge; the final line identifies pending components. Every node updates shared per-request LangGraph state.")
    paragraph("State holds the scenario, venue candidates, extracted facts, source labels, weather, plan, legs, checks, rejected itineraries, trace and attempt count. Actions are tool calls, proposals and re-plans; observations are tool results and constraint failures. A runner-local evidence cache avoids fetching a page twice. No database or persistent preference memory is used.")
    paragraph("Discovery searches supported categories within the requested radius. Enrichment looks up approved official URLs and extracts price, closing hour, diet and mood clues. The implemented web_search is a catalog lookup, not general web search. Offline text is synthetic annotation correlated with ground truth. Optional live retrieval blocks redirects, limits size and times out after ten seconds; it has not been live-tested.")
    paragraph("The Planner accepts 1-4 supported requested stop types and uses only supplied venue IDs. The Critic checks count/category/uniqueness, total annotated price, vegan suitability at every stop, closing time at each scheduled arrival, and all route legs. Unknown facts cannot pass the relevant checks. Arrival times use a fixed two-hour spacing by default; weekday/opening-time logic and travel-adjusted schedules are not implemented.")
    paragraph("The Transit node records straight-line walking estimates and optional unverified transit observations. Unverified estimates cannot satisfy a transit constraint. On rejection the Critic stores failed checks and rejected venue sequences for the next proposal. Exhausted retries return unresolved, not proven infeasible. Page errors are disclosed and leave facts unknown; approved URL restrictions and treating pages as data limit unsafe retrieval. Booking and payment are excluded.")
    paragraph("Frameworks: Python 3.13.5, LangGraph, LangChain and Pydantic; exact installed versions are pinned in requirements-milestone2.txt. Real model selection remains environment-based in src/llm.py. Real enrichment/planning calls and usage parsing are implemented; a scripted response test checks that boundary. No hosted model, live API or OpenTripPlanner was evaluated in this pilot.")

    new_page()
    heading("Section 3. Preliminary Evaluation Results and Analysis")
    paragraph("Two authored pilot scenario collections share the existing 13-venue Tempe catalog. Standard has four unique requests: vegan dinner/dessert, budget dinner/bar, three stops, and dinner only. Stress has four unique requests: impossible budget, too-late dessert, an injected invalid proposal, and an injected page timeout. Scenarios and constraints are in eval/pilot_scenarios.json. This is not a public benchmark, independent holdout, or larger Phoenix dataset.")
    paragraph("Each system was evaluated on the same eight scenarios three times, yielding 12 runs per system/dataset and 72 total. No train/test split was performed. The fixture text and scorer labels originate from the same annotations, so favorable results cannot establish factual generalization. Dataset labels mark two stress requests infeasible relative to the bundled catalog and fixed arrival schedule only.")
    paragraph("Comparison systems: hybrid graph in mock mode; greedy price/mood policy with enriched fixture facts but no critique or retries; sparse-catalog deterministic policy without enrichment during selection. Both baselines are genuinely executed deterministic references, not the original ReAct baseline or a single-call LLM. The sparse policy receives the same catalog IDs but fewer selection facts; therefore comparisons conflate evidence access and policy. Routes and final scoring are common. The bad-proposal injection targets the graph's critic only, so it is a mechanism test, not a fair model-quality stress comparison.")
    paragraph("Scores are the mean of five boolean checks: structure, budget, all-stop diet, closing-time schedule and travel. Valid means every check passes. Feasible-only validity excludes the two catalog-infeasible cases. Infeasible abstention means returning unresolved rather than claiming validity; it is not proof of infeasibility. Repeats are deterministic and do not measure model variability.")
    rows = [[row["dataset"], row["system"], row["runs"], f'{row["mean_score"]:.2f}',
             f'{row["valid_plan_rate"]:.0%}', f'{row["feasible_valid_rate"]:.0%}',
             f'{row["median_seconds"]:.3f}', f'{row["p95_seconds"]:.3f}'] for row in artifact["summaries"]]
    table(["Dataset", "System", "Runs", "Score", "Valid", "Feasible valid", "Median s", "P95 s"], rows)
    paragraph("Table 1. Actual deterministic integration measurements from artifacts/pilot_results.json. All systems made zero LLM calls; token usage and model cost are zero only because no model ran. These sub-second times do not predict hosted-model latency. Full traces include node observations, attempts, errors and routes. There were no uncaught execution errors in the 72 runs.")
    paragraph("The graph passes all standard requests and both feasible stress cases. On stress, its overall validity is 50% because two requests are infeasible in this fixture. It abstains on all six repeated infeasible runs; the baselines present candidate plans instead. The graph's stress mean score equals the baselines' 0.85 despite a better valid-plan rate, illustrating why partial scores and abstention should be reported separately.")
    paragraph("The original Phase-0 ReAct and real single-call comparisons remain pending credentials. Human mood/usefulness scores, independently checked factual accuracy/source coverage, live tool reliability and dollar cost are not measured. Milestone 1's 95% constraint satisfaction, 85% validity, 100% dietary correctness, 95% factual accuracy, 90% evidence coverage, 4/5 human rating, 45s median/90s P95 and $0.10 limits cannot be declared met from this pilot.")

    new_page()
    heading("Section 4. Demo or Case Study")
    demo = next(row for row in artifact["runs"] if row["system"] == "multi_agent" and row["scenario"] == "recover_bad_proposal" and row["repeat"] == 0)
    paragraph("Input: dinner, dessert and a bar starting at 19:00 near ASU, $50/person, maximum walk 1200m. Expected fixture outcome: three distinct requested categories, arrivals at 19:00/21:00/23:00, total budget and all travel checks passing. The actual demo uses mock mode and deliberately injects an invalid first proposal.")
    paragraph("Discovery selects catalog candidates. Enrichment extracts venue facts from synthetic page text; Weather supplies its bundled hourly sample. The first proposal contains only Snooze, demonstrating count/category failure and a venue closed for dinner. The Critic rejects it and writes failed checks and the rejected itinerary to shared state. The graph returns to Planner, and Transit records every leg of the replacement itinerary.")
    paragraph("Final venue IDs: " + " -> ".join(stop["venue_id"] for stop in demo["plan"]["stops"]) +
              f'. Attempts: {demo["attempts"]}; independent score: {demo["score"]:.2f}; all checks pass: {demo["valid"]}.')
    screenshot = ARTIFACTS / "recovery_screenshot.png"
    if screenshot.exists():
        document.add_picture(str(screenshot), width=Inches(6.1))
        paragraph("Figure 2. Browser screenshot of the saved actual mock-run trace, showing invalid first proposal, failed critic checks, replan, route observations and final passing checks. This is rendered execution evidence, not a conceptual diagram or live-model screenshot.")
    else:
        paragraph("Screenshot pending: open artifacts/execution_evidence.html and capture #recover_bad_proposal to artifacts/recovery_screenshot.png, then regenerate this draft. JSON evidence alone does not fulfill the template's screenshot requirement.")

    new_page()
    heading("Section 5. Failure Analysis and Current Limitations")
    paragraph("Observed failure 1: impossible_budget requires dinner and dessert for $5/person. The graph exhausts eight proposals and returns unresolved. The trace shows budget checks failing. This correctly avoids claiming a valid plan, but does not prove no plan exists globally. Proposed improvement: distinguish catalog-provable infeasibility from retry exhaustion, and test both against independently labeled cases.")
    paragraph("Observed partial failure 2: the page_timeout case injects a timeout for Pita Jungle. Enrichment records TimeoutError, marks that venue's facts unknown, and finds another valid fixture itinerary. The recovery is demonstrated in saved logs; live website timeouts, rate limits and retries have not been evaluated. Proposed improvement: bounded retries and independent cached snapshots, validated through repeatable HTTP-failure tests.")
    paragraph("Observed data limitation: some synthetic pages do not state a precise closing hour (for example 'open late'). Such candidates cannot pass the hour verifier. This is conservative, but may exclude real feasible outings. Precise hours, weekday rules and menu evidence must be collected instead of guessed.")
    paragraph("Broader limitations: only 13 potentially stale curated venue entries; no independent factual benchmark; fixed arrival spacing and straight-line travel; no party-capacity/tax-tip verification; no general search engine; no conversational constraint parser; sequential rather than parallel specialist nodes; only Enrichment/Planner use an LLM; real-model paths remain untested against an external provider. Alternatives, persistent memory, self-hosted transit and cities outside Phoenix are pending, not implemented claims.")
    failure_screenshot = ARTIFACTS / "failure_screenshot.png"
    if failure_screenshot.exists():
        document.add_picture(str(failure_screenshot), width=Inches(6.1))
        paragraph("Figure 3. Rendered actual saved terminal outcome for the impossible-budget fixture: unresolved after bounded attempts with budget failure. Screenshot comes from the saved run, not fabricated output.")

    new_page()
    heading("Section 6. Remaining Work Before Final Submission")
    table(["Priority / current gap", "Planned work", "Owner", "Completion evidence"], [
        ["Required: no real model runs", "Configure one provider privately; run graph, ReAct and single-call", "Team assignment pending", "Paired results on both datasets; cost/tokens/latency"],
        ["Required: correlated fixture labels", "Collect independent dated sources; broaden venues/scenarios", "Team assignment pending", "Reviewed labels and provenance; holdout evaluation"],
        ["Required: no follow-up", "Meet Mitul with demos/results; confirm scope and thresholds", "Team assignment pending", "Actual notes and approval"],
        ["Required: time/travel gaps", "Opening-day/time and travel-aware schedule; verified transit", "Team assignment pending", "Targeted regression tests and live examples"],
        ["Required: subjective metrics", "Human mood/usefulness ratings; factual-claim audit", "Team assignment pending", "Rubric, counts and ratings"],
        ["Required: submission evidence", "Confirm contributions; pin commit; finalize screenshots/presentation", "All members, confirm roles", "Accessible repository links and reproducible demo"],
        ["Optional", "Alternative itineraries, consented memory, other cities", "Team assignment pending", "Stakeholder-approved extension tests"]])
    paragraph("Do not treat passing mock tests as completion of the real agentic demonstration. Required work takes priority over memory, alternative recommendations and geographic expansion.")

    new_page()
    heading("Section 7. GitHub Repository and Team Contributions")
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    paragraph("Repository: https://github.com/sachinsss/night-out-curator. Grader access must be confirmed by the team.")
    paragraph(f"Current branch: {branch}. Starting HEAD: {commit}. Prototype/report changes are uncommitted and therefore NOT included in that HEAD. No commit or branch was created automatically; record the eventual submission commit after team review.")
    table(["Team member", "GitHub / actual contributions"], [
        ["Sachin Shivanand Shankarikoppa", "Repo owner: sachinsss; verify personal contributions and commit/PR links"],
        ["Sushanth Urubailu Vasudeva", "Username, code/data/evaluation/writing contributions and links pending"],
        ["Vivek Vidyadhar Kamath", "Username, code/data/evaluation/writing contributions and links pending"],
        ["Naga Sai Rama Srikar Vinjanampati", "Username, code/data/evaluation/writing contributions and links pending"],
        ["Sri Sai Chetana Reddy Janagan", "Username, code/data/evaluation/writing contributions and links pending"]])
    paragraph("Implementation and draft were generated with GitHub Copilot assistance in the shared workspace. Team members should review and document their actual contributions, including stakeholder communication and non-code work; commit counts alone are not evidence of roles.")
    paragraph("Setup: pip install -r requirements-milestone2.txt. Test: python -m unittest eval.test_itinerary eval.test_multi_agent -v. Mock demo: python run_multi_agent.py --mock. Pilot: python -m eval.evaluate_multi --mock --repeats 3. Real model: configure one provider in .env and omit --mock. Report regeneration: python scripts/draft_milestone2.py.")
    paragraph("Evidence files: artifacts/pilot_results.json; artifacts/demo.json; artifacts/execution_evidence.html; screenshots when captured. Repeat counts and deterministic mode must remain visible in any submitted tables.")
    document.save(REPORTS / "milestone2_draft.docx")
    (REPORTS / "milestone2_draft.md").write_text("\n".join(markdown), encoding="utf-8")
    print("Generated reports/milestone2_draft.docx and reports/milestone2_draft.md")


if __name__ == "__main__":
    main()
