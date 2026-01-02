# Supabase Handoff Guide

This folder is for the data/persistence workstream. The API currently runs on local JSON files via `DataService`. Switch to Supabase by implementing `SupabaseDataService` to mirror the same method signatures.

## Owned files (Data/Persistence)
- `app/services/data_service.py` — current JSON implementation (parity target).
- `app/services/storage_factory.py` — backend selector (`USE_LOCAL_STORAGE` flag).
- `app/services/supabase_service.py` — stub to implement.
- `app/db_schema.sql` — canonical schema.
- `supabase/` — this guide + migrations (add here).
- `data/*.json` — demo data source for seeding/parity tests.

## Schema
- SQL lives in `app/db_schema.sql`; tables: `agent_info`, `user_info`, `user_events`, `agent_events`, `weekly_pnl`.
- Align column names with the JSON structure so the API stays unchanged.

## Backend toggle
- Env flag `USE_LOCAL_STORAGE=false` tells `app/services/storage_factory.py` to return `SupabaseDataService`.
- Implement `SupabaseDataService` in `app/services/supabase_service.py` (currently stubs).
- Inject a Supabase client (`create_client(SUPABASE_URL, SUPABASE_KEY)`) in the constructor or inside the factory once ready.

## Suggested steps
1) Create migrations from `app/db_schema.sql` (or adapt to Supabase migrations).
2) Implement `SupabaseDataService` methods to mirror `DataService` behavior:
   - `sync_agent_catalog` -> upsert into `agent_info`.
   - `create_user` / `get_user` / `list_users` -> `user_info`.
   - `record_agent_selection` / `record_agent_drop` / `get_user_agents` -> `user_events` (use `agent_ids` array for selects, `agent_id` for drops).
   - `record_trade` / `get_agent_trades` -> `agent_events`.
   - `get_standings` / `get_user_pnl` -> recompute on read (can use SQL or Python aggregation).
   - `record_weekly_snapshot` / `list_snapshots` -> `weekly_pnl`.
3) Add a small integration test that spins up against a local Supabase or uses `supabase-py` with a mock.
4) Document any divergence from the local JSON behavior so the API remains backwards compatible.

## Seed/validation ideas
- Import existing JSON demo data (`data/*.json`) into Supabase tables to parity-test endpoints.
- Run `uvicorn server:app --reload` with `USE_LOCAL_STORAGE=false` and hit `/api/*` to confirm responses match the JSON mode.***
