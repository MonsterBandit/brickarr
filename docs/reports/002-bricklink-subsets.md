# Report 002 — BrickLink Subsets response shape

## Assumption
`GET /items/SET/{set_no}/subsets?break_minifigs=false` returns (after envelope
unwrap) a list of groups, where each group has:

```
{
  "match_no": <int>,
  "entries": [
    {
      "item": { "type": "PART" | "MINIFIG", "no": "<string>" },
      "color_id": <int>,
      "quantity": <int>,
      "extra_quantity": <int>,
      "is_alternate": <bool>,
      "is_counterpart": <bool>
    }
  ]
}
```

Minifig lines have `color_id = 0`. `match_no = 0` denotes the regular line; any
non-zero match groups alternates.

## Why I can't verify now
No network access to api.bricklink.com and no credentials in this environment.

## How I would verify
1. Pick a real set with known alternates (e.g. `60198-1`).
2. Run `bricklink_call(db, "GET", "/items/SET/60198-1/subsets", params={"break_minifigs": "false"})`.
3. Diff the keys at each level against the loader in `catalog_mirror.py::mirror_subsets`.
4. Adjust `mirror_subsets` for any renamed fields (e.g. `is_extra` vs
   `extra_quantity`, `color_id` vs `colorID`, nested `item` vs flat `item_no`).
