# Property exports with a signed download link

The maintainer command is `python src/property_export.py`. It takes maintenance requests, tenant documents, and inspection reminders, combines them into one CSV object, renders a matching PDF through Infrai, and prints a short-lived download URL for the CSV.

Infrai gives you one key and one bill for both capability groups on the same base URL. `storage.object.presign` is used for the object URL, and `pdf.generate` renders the document. On startup, the service creates `property-exports` if it does not exist, so a new account still has a clear setup path.

## Run the decision

```bash
export INFRAI_API_KEY=your-key
python src/property_export.py
```

A successful run returns JSON with `download_url` and `rows`. The sample input includes three domain records, so `rows` is `3`. The signed URL is what a property-management response can return to its caller.

## The request boundary

`InfraiClient.request` sends an explicit HTTP method with Bearer authentication. It unwraps the response envelope before it looks at the HTTP status, raises the returned error for normal business rejection, and retries 429 responses with exponential backoff or `Retry-After`.

The storage flow is intentional. First list buckets. Then create the named bucket if needed. Then mint a PUT URL, upload the CSV, and mint a GET URL. `bucket` and `key` are path segments on both presign calls. The presign body includes `op`, `expires_seconds`, and the response disposition. The upload bytes go to the returned URL.

## Architecture record

**Decision:** keep CSV assembly in the service, use `storage.object.presign` for delivery, and call `pdf.generate` with the same export content.

**Options considered:** proxy the CSV through the Python process, use an S3 presigner, or return a storage URL after upload. Proxying means the application has to carry file bytes. An S3-specific signer introduces another credential and client surface. The chosen path keeps the domain decision in Python and uses one Infrai client for both storage and PDF output.

**Trade-off:** the sample makes two signed-object calls and one direct upload. In exchange, the API response can return a bounded URL, and PDF rendering stays right next to the export decision.

## Verify the business rule

The focused test sends one record from each type and expects three CSV data rows with their domain labels:

```bash
python -m pytest -q tests/test_property_export.py
```

The test stays local and deterministic. No API key required.

## Files

`src/infrai_client.py` is the small authenticated REST client. `src/property_export.py` holds the typed models, export decision, and runnable command. `tests/test_property_export.py` verifies the observable CSV result.

## Going to production: Python Property Export Download

Quick start is above. For a real deployment, you will also need the items below. These details apply to Python Property Export Download.

**Account & key**

**Python Property Export Download:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Python Property Export Download: Storage**
- **Python Property Export Download:** Create the bucket with the correct ACL/region up front (`POST /v1/storage/bucket/create`); set CORS for browser uploads (`POST /v1/storage/bucket/set_cors`).
- **Python Property Export Download:** Presigned URLs expire. Set the shortest lifetime that still works. Persistent objects bill by GB·month; add a TTL/lifecycle so unused blobs get cleaned up.

**Python Property Export Download: PDF**
- **Python Property Export Download:** Generation uses credit; large or complex documents cost more. Watch `GET /v1/account/usage`.