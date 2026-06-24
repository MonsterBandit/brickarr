# Report 001 — BrickLink OAuth1 signing edge cases

## Assumption
I am using `requests_oauthlib.OAuth1` with `signature_type="auth_header"` and
applying the signed `Authorization` header on a `requests.Request.prepare()`
object, then forwarding the headers (and the JSON body) to `httpx`. I assume:

- BrickLink accepts an `Authorization: OAuth ...` header for `GET` and `POST`.
- Query parameters are included in the signature base string as `requests`
  prepares them (sorted, percent-encoded per RFC 5849).
- JSON request bodies are **not** included in the OAuth1 signature base string
  (BrickLink follows the convention of signing only form-encoded bodies).
- The envelope returned is `{"meta": {...}, "data": ...}` and I extract `.data`.
- Calling `GET /items/SET/1-1` is a safe, low-cost ping.

## Why I can't verify now
No outbound network access to api.bricklink.com from this build environment, and
no test credentials available.

## How I would verify
1. Configure real OAuth1 creds at Settings -> Data Sources and click Test.
2. Capture the raw `Authorization` header and request URL with `httpx`'s event
   hooks; compare the OAuth1 base string against a known-good signer (e.g.
   `oauth2` CLI from BrickLink docs or a Python `oauthlib` reference call).
3. Hit `/items/SET/1-1` and confirm the JSON envelope shape; if it does not
   match `{meta, data}`, change `bricklink_call` accordingly.
4. Send a `POST` with a JSON body to a write endpoint we may add later and
   verify the server accepts it (proving body exclusion from signature).
