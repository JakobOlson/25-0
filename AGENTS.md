# AGENTS.md

## Project context
- This repository is a small web/data project for a CS player simulation game.
- The main Python logic currently lives in [backend/app/validate_data.py](backend/app/validate_data.py) and the source data is in [backend/app/data/players.json](backend/app/data/players.json).
- The frontend and data-pipeline folders are currently minimal, so keep changes focused and easy to review.

## Preferred interaction style
- Prefer short pseudo-code or a small step-by-step plan before writing full implementations.
- When suggesting code, keep it incremental: one small function, one branch, or one refactor at a time.
- Avoid long autocomplete blocks or large code dumps unless the user explicitly asks for a full solution.
- If a change is broad, ask for confirmation before generating a larger patch.

## Coding guidance
- Favor clear, readable Python over clever abstractions.
- Keep edits small and reversible, especially when working with validation logic or data files.
- Preserve the existing style of the file you are editing unless there is a strong reason to change it.
- For validation and data-related work, prefer explicit checks and helpful error messages.
