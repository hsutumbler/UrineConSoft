import sys
from ui.qc.lj_chart import LJChartPage
from services.qc_service import QCBatchService

all_batches = QCBatchService.get_all()
all_flattened_batches = []
for b in all_batches:
    for sub in b.get("sub_lots", []):
        combined = dict(b)
        combined.update(sub)
        all_flattened_batches.append(combined)

display_batch = next((b for b in all_flattened_batches if b["level_name"] == "Level 1" and b["lot_number"] == "D252880"), None)
print(display_batch.get("batch_id"), display_batch.get("lot_number"))
