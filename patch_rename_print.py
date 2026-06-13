import glob

files_to_check = [
    "ui/qc/qc_batch.py",
    "ui/qc/reagent_batch.py",
    "ui/inquiry/report_inquiry.py",
    "ui/inquiry/comprehensive_inquiry.py",
    "ui/inquiry/qc_target_history_inquiry.py",
    "ui/inquiry/raw_qc_inquiry.py"
]

for file in files_to_check:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace the two variants
    content = content.replace('QPushButton("🖨️ 列印 / 匯出 PDF")', 'QPushButton("🖨️ 列印")')
    content = content.replace('QPushButton("列印 / 匯出 PDF")', 'QPushButton("列印")')
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
