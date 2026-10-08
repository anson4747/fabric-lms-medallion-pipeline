"""Static checks on the Fabric Git items, run in CI before anything is synced to a workspace.

- every item folder has a valid .platform file
- every JSON definition parses
- every notebook is valid Python
- pipelines reference notebooks that exist in the repo
- no pipeline passes a hard-coded workspace name to a notebook
"""

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "fabric"
errors = []

items = [p for p in ROOT.iterdir() if p.is_dir()]
logical_ids = {}
for item in items:
    platform = item / ".platform"
    if not platform.exists():
        errors.append(f"{item.name}: missing .platform")
        continue
    meta = json.loads(platform.read_text())
    logical_ids[meta["config"]["logicalId"]] = item.name

for path in ROOT.rglob("*"):
    if path.suffix in {".json", ".pbir", ".pbism"} or path.name == ".platform":
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path.relative_to(ROOT)}: invalid JSON ({exc})")
    if path.name == "notebook-content.py":
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            errors.append(f"{path.relative_to(ROOT)}: syntax error line {exc.lineno}")


def walk(activities):
    for act in activities:
        yield act
        yield from walk(act.get("typeProperties", {}).get("activities", []))


for pipeline in ROOT.glob("*.DataPipeline/pipeline-content.json"):
    for act in walk(json.loads(pipeline.read_text())["properties"]["activities"]):
        props = act.get("typeProperties", {})
        ref = props.get("notebookId") or props.get("pipelineId")
        if ref and ref not in logical_ids:
            errors.append(f"{pipeline.parent.name}/{act['name']}: references unknown item {ref}")
        ws = props.get("parameters", {}).get("workspace", {}).get("value")
        if isinstance(ws, str):
            errors.append(f"{pipeline.parent.name}/{act['name']}: hard-coded workspace '{ws}'")

print(f"Checked {len(items)} Fabric items")
if errors:
    print("\n".join(f"  FAIL {e}" for e in errors))
    sys.exit(1)
print("All Fabric item checks passed")
