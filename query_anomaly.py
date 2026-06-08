import sys
sys.path.append("/Users/hsutumbler/Project/UrineConSoft")
from services.anomaly_service import AnomalyService

records = AnomalyService.get_all_records('2026-05-01', '2026-06-08', 1)
print("With instrument_id=1, found", len(records), "records")

records2 = AnomalyService.get_all_records('2026-05-01', '2026-06-08', None)
print("With instrument_id=None, found", len(records2), "records")
