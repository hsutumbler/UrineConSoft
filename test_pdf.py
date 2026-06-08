from PyQt6.QtWidgets import QApplication
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QTextDocument, QPageLayout
from PyQt6.QtCore import QMarginsF, QSizeF

app = QApplication([])
doc = QTextDocument()
doc.setHtml("<h1>Test</h1>")
doc.setDocumentMargin(0)

printer = QPrinter()
printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
printer.setOutputFileName("test.pdf")
printer.setPageMargins(QMarginsF(5, 10, 5, 10), QPageLayout.Unit.Millimeter)

# test how to set page size
rect = printer.pageRect(QPrinter.Unit.Point)
print(rect.width(), rect.height())
doc.setPageSize(QSizeF(rect.width(), rect.height()))
doc.print(printer)
print("Done")
