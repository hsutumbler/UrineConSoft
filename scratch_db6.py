import sys
import os
from datetime import date
sys.path.append(os.path.abspath('.'))
from services.qc_service import QCResultService

results = QCResultService.get_results(23, date(2026, 5, 1), date(2026, 6, 30))
print("Results for IQI 23:")
for r in results:
    print(f"{r['result_date']} - val: {r['measured_value']}")
