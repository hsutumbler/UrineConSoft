from PyQt6.QtWidgets import QApplication
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QTextDocument, QPageLayout, QPageSize
from PyQt6.QtCore import QMarginsF, QSizeF

app = QApplication([])
doc = QTextDocument()
html = """
<html><body style="margin:0; padding:0; border: 1px solid red;">
<h2 style="text-align:center;">Title</h2>
<table width="100%" border="1" cellspacing="0">
<tr><th>A</th><th>B</th></tr>
<tr><td>1</td><td>2</td></tr>
</table>
</body></html>
"""
doc.setHtml(html)
doc.setDocumentMargin(0)

printer = QPrinter()
printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
printer.setOutputFileName("test2.pdf")
printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
printer.setPageMargins(QMarginsF(8, 10, 8, 10), QPageLayout.Unit.Millimeter)

rect = printer.pageRect(QPrinter.Unit.Point)
doc.setPageSize(QSizeF(rect.width(), rect.height()))
doc.print(printer)
print("Done")
