import csv
import io
import json
from dataclasses import dataclass
from typing import Any

from infrai_client import InfraiClient


@dataclass(frozen=True)
class MaintenanceRequest:
    request_id: str
    unit: str
    status: str


@dataclass(frozen=True)
class TenantDocument:
    tenant_id: str
    document_type: str


@dataclass(frozen=True)
class InspectionReminder:
    unit: str
    due_on: str


@dataclass(frozen=True)
class PropertyExport:
    csv_text: str
    download_url: str
    pdf_data: Any


BUCKET = "property-exports"


def csv_for_property(
    requests: list[MaintenanceRequest],
    documents: list[TenantDocument],
    reminders: list[InspectionReminder],
) -> str:
    rows = []
    for item in requests:
        rows.append({"kind": "maintenance", "identifier": item.request_id, "unit": item.unit, "value": item.status})
    for item in documents:
        rows.append({"kind": "tenant_document", "identifier": item.tenant_id, "unit": "", "value": item.document_type})
    for item in reminders:
        rows.append({"kind": "inspection_reminder", "identifier": item.due_on, "unit": item.unit, "value": "due"})
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=["kind", "identifier", "unit", "value"])
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _ensure_bucket(client: InfraiClient) -> None:
    listing = client.bucket_list() or {}
    items = listing.get("items", []) if isinstance(listing, dict) else []
    if not any(item.get("name") == BUCKET for item in items):
        client.bucket_create(BUCKET)


def create_export(
    client: InfraiClient,
    requests: list[MaintenanceRequest],
    documents: list[TenantDocument],
    reminders: list[InspectionReminder],
    export_key: str,
) -> PropertyExport:
    _ensure_bucket(client)
    csv_text = csv_for_property(requests, documents, reminders)
    pdf_data = client.pdf_generate(
        {
            "markdown": "# Property export\n\n" + csv_text.replace("\n", "  \n"),
            "page_size": "A4",
            "orientation": "landscape",
            "store": True,
        }
    )
    signed = client.object_presign(
        BUCKET,
        export_key,
        {"op": "put", "expires_seconds": 900, "content_type": "text/csv", "idempotency_key": export_key},
    )
    client.put_bytes(signed["url"], csv_text.encode("utf-8"), "text/csv")
    download = client.object_presign(
        BUCKET,
        export_key,
        {"op": "get", "expires_seconds": 900, "response_disposition": "attachment"},
    )
    return PropertyExport(csv_text, download["url"], pdf_data)


def demo_input() -> tuple[list[MaintenanceRequest], list[TenantDocument], list[InspectionReminder]]:
    return (
        [MaintenanceRequest("MR-104", "3B", "open")],
        [TenantDocument("TEN-22", "lease")],
        [InspectionReminder("3B", "2026-11-01")],
    )


if __name__ == "__main__":
    client = InfraiClient()
    result = create_export(client, *demo_input(), "exports/property-2026-11-01.csv")
    print(json.dumps({"download_url": result.download_url, "rows": result.csv_text.count("\n") - 1}))
