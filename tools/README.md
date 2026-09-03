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

## Proposed: pull the ServiceTitan report emails directly (not built yet — Charles to decide)

Findings from 2026-09-03 testing, all done from the normal Outlook web login (https://outlook.cloud.microsoft), no Power Automate:

- **Emails:** ServiceTitan scheduled reports arrive in Charles's work inbox daily 6:05–7:51 AM CT, from an address containing `servicetitan`, each with one .xlsx attachment.
  Subject → attachment (range) → current 4DX file:
  - `Completed` (7:51, non-L7) → `Completed Jobs-CH PBI_Dated 01_01_26 - <today>.xlsx` (**YTD**, ~8 MB) → PBI Completed YTD 4dx.xlsx
  - `Completed` (7:35) → `Completed Jobs-CH PBI L7_Dated …` (last 7 d) — ignore when the YTD one exists
  - `PBI Sales Report` → `Estimates - Sold By_Dated 01_01_26 - <today>.xlsx` (**YTD**) → Sales4dx.xlsx
  - `SalesPBI` → `SalesPBI_Dated …` (last 7 d)
  - `PBI Bookings L7` → `Bookings PBI_Dated …` (last 7 d only) → Booking PBI 4DX.xlsx
  - `Project Details` → `Project Detail Report ch_Dated …` (last 7 d) → Project Detail Report.xlsx
  - `CC Sales` (YTD) / `CCL7` (7 d) → CC Sales 4dx.xlsx · `Hold Jobs` → Kody Hold Jobs.xlsx · `Scheduled Install` → Kody Scheduled Install.xlsx · `install jobs need to schedule (year to date)` → Install - Need to Schedule.xlsx
- **Headers:** Sales, Bookings, Project Detail attachments match the ledgers exactly. Completed differs only in 5 unused trailing note columns (Hatch / HAPPY CALL NOTES / SALES FOLLOW UP NOTES vs blanks + Prevailing Wage) → merge_ledger.py should fill missing non-key columns with null instead of aborting, and the 31-day window guard must be raised (~400 d) so a YTD file replaces all current-year rows.
- **Access (tested OK):** in the Outlook tab, MSAL caches tokens under `localStorage`/`sessionStorage` key `msal.3.token.keys.9199bf20-a13f-4107-85dc-02114787ef48`; each entry has `target`, `expiresOn`, `secret`. Tokens refresh on page load (~60–70 min validity).
  - List/download: `https://outlook.office.com/api/v2.0/me/messages?$filter=ReceivedDateTime ge <iso> and HasAttachments eq true and contains(From/EmailAddress/Address,'servicetitan')` → `/messages/{id}/attachments` → `/attachments/{id}/$value` with the token whose target includes `outlook.office.com/Mail.Read`.
  - Upload: SharePoint REST `POST {site}/_api/web/getfolderbyserverrelativeurl('<folder>')/Files/add(url='<name>',overwrite=true)` with the token whose target includes `turnpoint112358-my.sharepoint.com/Files.ReadWrite` (8 MB in one POST worked). Graph `PUT /me/drive/root:<path>:/content` (+ upload session >4 MB) also worked.
  - **Outlook page CSP blocks non-Microsoft origins** (GitHub API, raw.githubusercontent, cdn.sheetjs) — so the attachment must hop through OneDrive/SharePoint (either the real 4DX files, or a scratch staging folder that is cleaned up) and be parsed/uploaded from a SharePoint tab (blank.gif) as the merge task does today.
- **Options:** (A) overwrite the existing 4DX files (identical to today's manual paste; keeps Power BI/anything else that reads them fed); (B) stage in `4DX/inbox/` (or similar) and go straight to the ledgers, leaving the spreadsheets untouched — then repoint the two State Fair tasks (they read the live Booking/Sales files) to the ledgers.
- Scratch folder `Documents/PBI/2025/4DX/inbox/` currently holds test uploads from 2026-09-03 (completed_ytd, sales_ytd, booking_l7, project_detail, test_sp_upload) — safe to delete.
