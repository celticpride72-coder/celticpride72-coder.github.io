# Report data ledgers

The ServiceTitan/Power BI exports on SharePoint (`Documents/PBI/2025/4DX/`) became **rolling 7-day windows** on 2026-09-03.
Full history for reporting lives here instead:

| Ledger | Source file | Key | Window column |
|---|---|---|---|
| data/booking.json.gz | Booking PBI 4DX.xlsx | Job # + Created Date + Scheduled Date | Created Date |
| data/sales4dx.json.gz | Sales4dx.xlsx | Estimate Id | Sold On |
| data/completed.json.gz | PBI Completed YTD 4dx.xlsx | Job # + Completion Date + Invoice # | Completion Date |
| data/project_detail.json.gz | Project Detail Report.xlsx | Project Number | (none — upsert) |

Format: gzip JSON `{source, slug, key[], windowCol, header[], rows[][], updated, lastMerge}` — rows are the original
spreadsheet cells (dates are Excel serials; convert with `new Date(1899,11,30+serial)`). The `Summary` column is omitted.

Seeded 2026-09-03 from the last full SharePoint versions (2026-09-02). Refreshed every weekday ~7:50 AM by the
`ledger-merge-weekday` scheduled task: it downloads each 7-day file, writes a delta, and runs `tools/merge_ledger.py`
(rows inside the delta's date window are replaced wholesale; Project Detail is upserted by key).

Read in the browser:
```js
const L = await fetch("https://raw.githubusercontent.com/celticpride72-coder/celticpride72-coder.github.io/main/data/booking.json.gz?t="+Date.now())
  .then(r=>r.body.pipeThrough(new DecompressionStream("gzip"))).then(s=>new Response(s).json());
const rows=[L.header,...L.rows];  // same shape as XLSX.utils.sheet_to_json(ws,{header:1,raw:true})
```
