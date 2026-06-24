# Report 003 — Brickset `getSets` envelope and field names

## Assumption
`GET https://brickset.com/api/v3.asmx/getSets?apiKey=...&userHash=...&params=...`
returns JSON shaped:

```
{ "status": "success", "sets": [ {
    "setID": <int>,
    "number": "43022-1",
    "name": "...",
    "year": <int>,
    "theme": "...",
    "subtheme": "...",
    "pieces": <int>,
    "minifigs": <int>,
    "USretailPrice": <float>,
    "launchDate": "YYYY-MM-DD",
    "exitDate": "YYYY-MM-DD",
    "ageMin": <int>, "ageMax": <int>,
    "rating": <float>,
    "image": { "thumbnailURL": "..." }
} ] }
```

`params` is a stringified JSON object (Brickset's documented quirk).

## Why I can't verify now
No outbound network access and no Brickset API key in this sandbox.

## How I would verify
1. Configure the API key at Settings -> Data Sources, click Test.
2. Hit `/getSets` with `{"setNumber":"43022-1"}` and dump the raw JSON.
3. Reconcile every field consumed in `catalog_mirror.enrich_from_brickset`
   against the response and rename as needed. The currency on `USretailPrice`
   needs translating to the instance's base currency.
