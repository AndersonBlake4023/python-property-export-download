import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from property_export import (  # noqa: E402
    InspectionReminder,
    MaintenanceRequest,
    TenantDocument,
    csv_for_property,
)


def test_export_contains_each_property_record_type():
    csv_text = csv_for_property(
        [MaintenanceRequest("MR-1", "2A", "open")],
        [TenantDocument("TEN-1", "lease")],
        [InspectionReminder("2A", "2026-12-01")],
    )

    lines = csv_text.splitlines()
    assert lines[0] == "kind,identifier,unit,value"
    assert "maintenance,MR-1,2A,open" in lines
    assert "tenant_document,TEN-1,,lease" in lines
    assert "inspection_reminder,2026-12-01,2A,due" in lines
