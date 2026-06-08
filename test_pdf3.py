from PyQt6.QtWidgets import QApplication
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QTextDocument, QPageLayout, QPageSize
from PyQt6.QtCore import QMarginsF

app = QApplication([])
doc = QTextDocument()
html = """
<html><head><style>
body { font-family: sans-serif; font-size: 10pt; margin: 0; padding: 0; }
th, td { border: 1px solid #aaa; white-space: nowrap; }
</style></head>
<body>
<h2 align="center">Title</h2>
<table align="center" width="100%">
<tr><th>Long Header 1</th><th>Long Header 2</th><th>Long Header 3</th><th>Long Header 4</th><th>Long Header 5</th></tr>
<tr><td>1234567890</td><td>1234567890</td><td>1234567890</td><td>1234567890</td><td>1234567890</td></tr>
</table>
</body></html>
"""
doc.setHtml(html)

printer = QPrinter()
printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
printer.setOutputFileName("test3.pdf")
printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
printer.setPageMargins(QMarginsF(8, 10, 8, 10), QPageLayout.Unit.Millimeter)

doc.print(printer)
print("Done test3")
