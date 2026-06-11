# slideforge-data-survey

Surveys a messy/huge Excel or CSV diligence model and hands SlideForge the exact
clean column-array JSON its charts and tables expect under `slide.data[data_key]`.

Adapted from the retention-analysis skill's two-pass survey flow, but **generic**:
it knows nothing about retention/ARR/TAM — it profiles columns and lets the
calling agent map them onto whatever the target chart template needs.

## Files

- `SKILL.md` — the workflow: pin target template → survey → map → confirm → assemble payload → generate.
- `scripts/survey.py` — streaming (read-only) two-pass workbook profiler. Stdlib + openpyxl.

## Try it

```bash
python3 scripts/survey.py --self-test                 # built-in end-to-end checks
python3 scripts/survey.py "/path/to/model.xlsx"        # JSON column profile
python3 scripts/survey.py "/path/to/model.xlsx" --text # human-readable
```

Requires `openpyxl` (`pip install openpyxl`).
