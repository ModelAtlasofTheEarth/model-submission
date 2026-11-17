# Agent Guide for Model Submission repo

This file captures repo-specific workflow and commands so that agents operate effectively and efficiently.

## Setup
- Requires Python >=3.7
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

## Core pipeline entrypoints
- `.github/scripts/` contains the parsing, crosswalk and RO-Crate writers:
  - `crosswalks.py` & `ro_crate_utils.py` implement metadata mapping
  - `write_repo_contents.py` orchestrates final RO-Crate output
- `.github/debug/submission_workflow.ipynb` mirrors the CI parse/rebuild steps and is for local debugging only

## Workflow overview (GitHub Issues + Labels)
1. **New model request**: open a GitHub Issue via the "New model request" template → `new model` label triggers parsing
2. **Edit & review**: update the first comment to correct any parsing errors → add `review requested` label to signal readiness
3. **Approval & repo creation**: reviewers add `model approved` label → new model repository is created (template-based) with `ro-crate-metadata.json`
4. **NCI upload**: add `upload to NCI` label to request data transfer (for >100 MB files)
5. **Publication**: once DOI and hosting are complete, `model published` label marks final state

## Local validation commands
- Run full parse & RO-Crate generation locally:
  ```bash
  jupyter nbconvert --execute .github/debug/submission_workflow.ipynb
  ```
- Inspect script CLI options:
  ```bash
  python .github/scripts/write_repo_contents.py --help
  ```

## Repository layout
- `.github/workflows/` – CI definitions linking Labels → parse/build jobs
- `.github/scripts/` – core metadata pipeline modules
- `.github/debug/` – interactive notebook for issue parsing
- `requirements.txt` – Python dependencies for the pipeline
- `README.md` – project overview and issue-based workflow

## Quirks & gotchas
- Metadata parsing is driven by GitHub Issue markdown; developers can debug this with `.github/debug/submission_workflow.ipynb`
- The RO-Crate file must be named exactly `ro-crate-metadata.json` at repository root
- Any changes to the Issue template or workflow filenames require updates in both `.github/workflows/` and the debug notebook

## Future work
- Remove the `.metadata_trail` bits, and stop creating the legacy files `issue_body.md` and `.website_material/index.json` in new model repositories.
- Add the M@TE submission URL (the issue URL) to all new RO-Crates.
