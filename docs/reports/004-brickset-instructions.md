# Report 004 — Brickset instructions endpoint + PDF URL field

## Assumption
`GET https://brickset.com/api/v3.asmx/getInstructions?apiKey=...&userHash=...&setID=<id>`
returns:

```
{ "status": "success", "instructions": [
    { "URL": "https://.../instr.pdf", "description": "Book 1" }
] }
```

The PDF URL is in the `URL` field (capitalised) and is directly fetchable with a
plain HTTP GET (no signed query, no referer requirement).

## Why I can't verify now
No outbound network access and no Brickset API key in this sandbox.

## How I would verify
1. Take a known multi-booklet set (e.g. `10307-1`).
2. Call `getInstructions` with its Brickset `setID` and dump the response.
3. Fetch one of the returned `URL`s with `curl -I` to confirm it serves
   `application/pdf` without auth.
4. Patch `catalog_mirror.enrich_from_brickset` and the download job to use the
   correct field name and confirm byte-progress arrives.
