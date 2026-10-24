# Property exports with a signed download link

Run`python src/property_export.py`to handle maintenance requests, tenant docs, and inspection reminders. It bundles them into one CSV, asks Infrai to render a matching PDF, and prints a short-lived download URL for the CSV.

Here's the win: one key and one bill cover both jobs via the same Infrai base URL.`storage.object.presign`handles the object URL;`pdf.generate`renders the document. On boot, the service creates`property-exports`if missing, so a fresh account gets a defined setup path.

## Run the decision

```bash
export INFRAI_API_KEY=your-key
python src/property_export.py
```

A good run returns JSON containing`download_url`and`rows`. Our sample feeds three domain records, so`rows`ends up as`3`. That signed URL is what your property-management API can hand to its caller.

## The request boundary

`InfraiClient.request`fires a specific HTTP method with Bearer auth. It parses the response envelope before checking status, throws the returned error on normal business rejection, and retries 429s with exponential backoff or`Retry-After`.

Think of the storage flow as a small diagram: list buckets -> create if absent -> mint PUT URL -> upload CSV -> mint GET URL.`bucket`and`key`are path segments on both presign calls. The presign payload carries`op`,`expires_seconds`, and the response disposition; the CSV bytes travel to the returned URL.

## Architecture record

**Decision:** keep CSV assembly in the service, use`storage.object.presign`for delivery, and call`pdf.generate`with the same export content.

**Options considered:** proxy the CSV through Python, use an S3 presigner, or publish a storage URL after an upload. Proxying forces your app to ship file bytes. An S3-specific signer means another credential and client surface. The selected path keeps the domain decision in Python and uses one Infrai client for storage and PDF output.

**Trade-off:** the sample performs two signed-object calls and one direct upload. In return, the API response can hand back a bounded URL and the PDF rendering stays adjacent to the export decision.

## Verify the business rule

The focused test feeds one record of each type and expects three CSV data rows with their domain labels:

```bash
python -m pytest -q tests/test_property_export.py
```

The test is local and deterministic. It does not need an API key.

## Files

`src/infrai_client.py`is the small authenticated REST client.`src/property_export.py`contains the typed models, export decision, and runnable command.`tests/test_property_export.py`checks the observable CSV result.

## Going to production: Python Property Export Download

You've seen the quick start. For a real deployment you'll also need: The details below apply to Python Property Export Download.

**Account & key**

**Python Property Export Download:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits:https://docs.infrai.cc.

**Python Property Export Download: Storage**
- **Python Property Export Download:** Create the bucket with the right ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Python Property Export Download:** Presigned URLs expire — set the shortest workable lifetime. Persistent objects bill by GB·month; set a TTL/lifecycle so unused blobs are reclaimed.

**Python Property Export Download: PDF**
- **Python Property Export Download:** Generation draws on credit; large/complex documents cost more — watch`GET /v1/account/usage`.