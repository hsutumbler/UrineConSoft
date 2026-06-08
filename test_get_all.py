import sys
import os
sys.path.append(os.getcwd())
from services.qc_service import QCBatchService

batches = QCBatchService.get_all()
for b in batches:
    print(b['lot_number'], b.get('is_active'), b.get('is_archived'))
