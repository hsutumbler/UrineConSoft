import sys
import os
from datetime import date
sys.path.append(os.path.abspath('.'))
from services.qc_service import QCResultService, QCBatchService

all_batches = QCBatchService.get_all()
batch_id_to_lot = {b["batch_id"]: b["lot_number"] for b in all_batches}
selected_lots = ["UQC060101"]

from_date = date(2026, 5, 2)
to_date = date(2026, 6, 2)

results = QCResultService.get_results(23, from_date, to_date)
results = [r for r in results if batch_id_to_lot.get(r["qc_batch_id"]) in selected_lots]

valid_dates = []
for r in results:
    if r["measured_value"] is not None:
        valid_dates.append(r["result_date"])

print("Valid dates for IQI 23 UQC060101:")
for d in valid_dates:
    print(d)
