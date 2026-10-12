# AGENTS.md

CRM Lite: a Streamlit app for companies, contacts and interactions, stored in SQLite through SQLAlchemy.

## Architecture rules

- Layers, top to bottom: UI (`app.py`, `pages/`) → `src/services.py` → `src/repository.py` → `src/models.py` and `src/db.py`.
- A lower layer never imports an upper one. Nothing in `src/` imports `streamlit`.
- Validation lives in `src/services.py`. A new or changed write path that accepts user input must validate through a service function. The UI may read through `src/repository.py` directly.
- Services raise `ValueError` with a user-facing message. The UI catches it and shows it with `st.error`.
- Only `src/db.py` calls `create_engine` or `sessionmaker`. Everything else uses `get_engine()` and `get_session_factory()`.
- Repository and service functions take a `Session` argument and never create one.