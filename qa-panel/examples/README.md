Synthetic reports for trying `qa_panel.py consolidate`. They describe a nonexistent `example/app.py`; they are not findings about this repo. Only 2 of 25 agents are present, so `gate` fails on completeness unless `--allow-partial` is used.

    python3 qa_panel.py consolidate --reports qa-panel/examples --base-sha c7d4f39 --out /tmp/qa-demo
