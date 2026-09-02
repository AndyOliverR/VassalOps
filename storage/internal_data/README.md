# Internal catalog (company inventory)

Drop **CSV, Excel (.xlsx), Word (.docx), PDF, JSON, or text** here. VassalOps crawls this folder (and `local/`) when you paste a client booking request in chat.

Examples:

- `Check availability: hotel in Italy 12–15 June`
- `Client needs a villa in Spain 2026-09-10 to 2026-09-14`

Put live dumps in `local/` (gitignored). Optional: set `runtime_boundaries.internal_data_path` or `internal_data_extra_roots` (e.g. Google Drive for Desktop).

Google Sheets: add `{ "name": "Availability", "url": "https://docs.google.com/spreadsheets/d/…" }` under `internal_sheets`, or paste the sheet URL in chat. Reading a signed-in sheet uses Chrome/Edge after **Approve** (copy grid, not passwords).
