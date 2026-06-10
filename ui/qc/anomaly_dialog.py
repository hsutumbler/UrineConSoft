from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QFrame, QMessageBox, QTextEdit, QComboBox, QWidget, QCheckBox, QListWidget
)
from PyQt6.QtCore import Qt
import json
from services.anomaly_service import AnomalyService
from ui.base_page import COLORS

class AnomalyRecordDialog(QDialog):
    def __init__(self, parent, user_data, result_data, level_name):
        super().__init__(parent)
        self.user_data = user_data
        self.result_data = result_data
        self.level_name = level_name
        self.setWindowTitle("品管異常紀錄表")
        self.setMinimumWidth(900)
        self.setMinimumHeight(550)
        
        self.record = AnomalyService.get_record_by_result_id(result_data["result_id"])
        
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        
        split_layout = QHBoxLayout()
        main_layout.addLayout(split_layout)
        
        # 左半部：唯讀資訊
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 10, 0) # 右邊留點空隙
        
        info_frame = QFrame()
        info_frame.setObjectName("info_frame")
        info_frame.setStyleSheet(f"QFrame#info_frame {{ background-color: {COLORS.get('bg_input', '#FFFFFF')}; border-radius: 8px; border: 1px solid {COLORS.get('border', '#CCCCCC')}; }} QLabel {{ color: #333333; }}")
        info_layout = QFormLayout(info_frame)
        info_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        info_layout.setContentsMargins(15, 20, 15, 20)
        info_layout.setVerticalSpacing(15)
        
        r = self.result_data
        val = r.get("measured_value")
        if val is None: val = r.get("qualitative_result", "無")
        
        dt_str = ""
        if r.get("result_date"):
            dt_str = r.get("result_date").strftime("%Y-%m-%d") if hasattr(r.get("result_date"), "strftime") else str(r.get("result_date"))
        
        # 假設 lj_chart 有丟這些屬性進去，如果沒有就留白
        # 實作上需要由 lj_chart 把完整資訊包裝在 dict 中傳入
        
        self.anomaly_data = str(val)
        self.occurrence_time = dt_str
        self.violated_rule = r.get("westgard_flag") or "無"
        self.instrument_name = r.get("instrument_name", "未知")
        self.qc_lot_number = r.get("lot_number", "未知")
        
        # 紀錄單號
        self.serial_number = self.record['serial_number'] if self.record and self.record.get('serial_number') else "（儲存後自動產生）"
        
        lbl_serial = QLabel(self.serial_number)
        lbl_serial.setStyleSheet("font-weight: bold; color: #9B7E23;")
        info_layout.addRow("紀錄單號：", lbl_serial)
        
        info_layout.addRow("機器：", QLabel(self.instrument_name))
        info_layout.addRow("品管液批號：", QLabel(self.qc_lot_number))
        info_layout.addRow("Level：", QLabel(self.level_name))
        info_layout.addRow("發生時間：", QLabel(self.occurrence_time))
        info_layout.addRow("異常數據：", QLabel(self.anomaly_data))
        
        rule_lbl = QLabel(self.violated_rule)
        if self.violated_rule != "無":
            rule_lbl.setStyleSheet("color: red; font-weight: bold;")
        info_layout.addRow("違反規則：", rule_lbl)
        
        left_layout.addWidget(info_frame)
        
        # 確認清單
        check_group = QWidget()
        check_layout = QVBoxLayout(check_group)
        check_layout.setContentsMargins(5, 15, 5, 0)
        check_layout.setSpacing(8)
        
        lbl_check = QLabel("請檢查下方無誤後，選取方塊：")
        lbl_check.setStyleSheet("font-weight: bold; color: #6B6444;")
        
        header_layout = QHBoxLayout()
        header_layout.addWidget(lbl_check)
        header_layout.addStretch()
        
        self.chk_all = QCheckBox("全選")
        self.chk_all.setStyleSheet("font-weight: bold; color: #9B7E23;")
        self.chk_all.stateChanged.connect(self._on_check_all_changed)
        header_layout.addWidget(self.chk_all)
        
        check_layout.addLayout(header_layout)
        
        self.chk_machine = QCheckBox("機器：機器情況")
        self.chk_reagent = QCheckBox("試劑：開封效期、試劑量")
        self.chk_calibrator = QCheckBox("校正液：開封效期、校正液量")
        self.chk_qc = QCheckBox("品管液：開封效期、品管液量")
        
        # 載入已儲存狀態
        check_state = []
        if self.record and self.record.get("check_items"):
            try:
                check_state = json.loads(self.record["check_items"])
            except:
                pass
                
        is_readonly = self.record is not None
        
        for i, chk in enumerate([self.chk_machine, self.chk_reagent, self.chk_calibrator, self.chk_qc]):
            chk.setStyleSheet("color: #333333;")
            if str(i) in check_state:
                chk.setChecked(True)
            chk.stateChanged.connect(self._on_single_check_changed)
            if is_readonly:
                chk.setEnabled(False)
            check_layout.addWidget(chk)
            
        self._on_single_check_changed() # 初始化「全選」狀態
        if is_readonly:
            self.chk_all.setEnabled(False)
            
        left_layout.addWidget(check_group)
        left_layout.addStretch() # 把資訊框往上推
        
        # 右半部：手動填寫區 + 片語
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        self.fields = {}
        
        self._add_text_area(right_layout, "異常原因(醫檢師)", "anomaly_cause")
        self._add_text_area(right_layout, "矯正措施/矯正結果(醫檢師)", "corrective_action")
        self._add_text_area(right_layout, "預防措施(組長)", "preventive_action")
        
        split_layout.addWidget(left_widget, 3) # 左邊佔比 3
        split_layout.addWidget(right_widget, 7) # 右邊佔比 7
        
        # 填入現有資料
        if self.record:
            self.fields["anomaly_cause"]["edit"].setPlainText(self.record.get("anomaly_cause", ""))
            
            ca = self.record.get("corrective_action", "")
            cr = self.record.get("corrective_result", "")
            if cr and cr not in ca:
                ca = ca + "\n\n[原矯正結果]\n" + cr if ca else cr
            self.fields["corrective_action"]["edit"].setPlainText(ca)
            
            self.fields["preventive_action"]["edit"].setPlainText(self.record.get("preventive_action", ""))

        # 按鈕列
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("儲存紀錄")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self._save_record)
        
        btn_cancel = QPushButton("取消" if not is_readonly else "關閉")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        if not is_readonly:
            btn_layout.addWidget(btn_save)
        else:
            btn_print = QPushButton("🖨️ 列印紀錄")
            btn_print.clicked.connect(self._print_record)
            
            btn_export = QPushButton("💾 匯出 PDF")
            btn_export.setObjectName("btn_primary")
            btn_export.clicked.connect(self._export_pdf)
            
            btn_layout.addWidget(btn_print)
            btn_layout.addWidget(btn_export)
        
        main_layout.addSpacing(10)
        main_layout.addWidget(self._make_divider())
        main_layout.addLayout(btn_layout)

    def _add_text_area(self, parent_layout, label_text, category):
        wrap = QWidget()
        vbox = QVBoxLayout(wrap)
        vbox.setContentsMargins(0, 0, 0, 0)
        
        header = QHBoxLayout()
        lbl = QLabel(label_text + "：")
        lbl.setStyleSheet("font-weight: bold;")
        
        cmb = QComboBox()
        cmb.addItem("--- 載入片語 ---", "")
        phrases = AnomalyService.get_phrases(category)
        for p in phrases:
            cmb.addItem(p["text"][:15] + "...", p["text"])
            
        cmb.currentIndexChanged.connect(lambda: self._load_phrase(category))
        
        btn_save_phrase = QPushButton("存為片語")
        btn_save_phrase.clicked.connect(lambda: self._save_phrase(category))
        
        btn_manage_phrase = QPushButton("⚙️ 片語管理")
        btn_manage_phrase.clicked.connect(lambda: self._open_phrase_manager(label_text, category))
        
        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(cmb)
        header.addWidget(btn_save_phrase)
        header.addWidget(btn_manage_phrase)
        
        edit = QTextEdit()
        
        is_readonly = self.record is not None
        if is_readonly:
            cmb.hide()
            btn_save_phrase.hide()
            btn_manage_phrase.hide()
            edit.setReadOnly(True)
            edit.setStyleSheet(f"background-color: {COLORS.get('bg_input', '#FFFFFF')}; color: #333333; border: 1px solid {COLORS.get('border', '#CCCCCC')}; border-radius: 4px;")
            
        vbox.addLayout(header)
        vbox.addWidget(edit)
        
        parent_layout.addWidget(wrap)
        
        self.fields[category] = {"edit": edit, "cmb": cmb}

    def _on_check_all_changed(self, state):
        is_checked = (state == 2) # Qt.CheckState.Checked
        for chk in [self.chk_machine, self.chk_reagent, self.chk_calibrator, self.chk_qc]:
            chk.blockSignals(True)
            chk.setChecked(is_checked)
            chk.blockSignals(False)

    def _on_single_check_changed(self):
        all_checked = all(chk.isChecked() for chk in [self.chk_machine, self.chk_reagent, self.chk_calibrator, self.chk_qc])
        self.chk_all.blockSignals(True)
        self.chk_all.setChecked(all_checked)
        self.chk_all.blockSignals(False)

    def _load_phrase(self, category):
        cmb = self.fields[category]["cmb"]
        edit = self.fields[category]["edit"]
        text = cmb.currentData()
        if text:
            current = edit.toPlainText()
            if current:
                edit.setPlainText(current + "\n" + text)
            else:
                edit.setPlainText(text)
            cmb.setCurrentIndex(0) # reset

    def _save_phrase(self, category):
        text = self.fields[category]["edit"].toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "錯誤", "內容空白無法儲存片語")
            return
            
        AnomalyService.add_phrase(category, text, self.user_data["user_id"])
        QMessageBox.information(self, "成功", "片語已儲存")
        
        # 重新整理下拉選單
        cmb = self.fields[category]["cmb"]
        cmb.blockSignals(True)
        cmb.clear()
        cmb.addItem("--- 載入片語 ---", "")
        phrases = AnomalyService.get_phrases(category)
        for p in phrases:
            cmb.addItem(p["text"][:15] + "...", p["text"])
        cmb.blockSignals(False)

    def _open_phrase_manager(self, label_text, category):
        dialog = PhraseManagementDialog(self, label_text, category)
        dialog.exec()
        
        # 重新整理下拉選單
        cmb = self.fields[category]["cmb"]
        cmb.blockSignals(True)
        cmb.clear()
        cmb.addItem("--- 載入片語 ---", "")
        phrases = AnomalyService.get_phrases(category)
        for p in phrases:
            cmb.addItem(p["text"][:15] + "...", p["text"])
        cmb.blockSignals(False)

    def _save_record(self):
        check_state = []
        for i, chk in enumerate([self.chk_machine, self.chk_reagent, self.chk_calibrator, self.chk_qc]):
            if chk.isChecked():
                check_state.append(str(i))
                
        data = {
            "result_id": self.result_data["result_id"],
            "anomaly_data": self.anomaly_data,
            "occurrence_time": self.occurrence_time,
            "instrument_name": self.instrument_name,
            "qc_lot_number": self.qc_lot_number,
            "qc_level": self.level_name,
            "violated_rule": self.violated_rule,
            "anomaly_cause": self.fields["anomaly_cause"]["edit"].toPlainText().strip(),
            "corrective_action": self.fields["corrective_action"]["edit"].toPlainText().strip(),
            "corrective_result": "",
            "preventive_action": self.fields["preventive_action"]["edit"].toPlainText().strip(),
            "check_items": json.dumps(check_state),
            "created_by": self.user_data["user_id"]
        }
        
        AnomalyService.save_record(data)
        QMessageBox.information(self, "成功", "異常紀錄已儲存")
        self.accept()

    def _make_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {COLORS.get('grid', '#EEEEEE')};")
        return line

    def _get_print_html(self):
        check_state = []
        if self.record and self.record.get("check_items"):
            try: check_state = json.loads(self.record["check_items"])
            except: pass
            
        checks = [
            "[X]" if "0" in check_state else "[ ]",
            "[X]" if "1" in check_state else "[ ]",
            "[X]" if "2" in check_state else "[ ]",
            "[X]" if "3" in check_state else "[ ]"
        ]
        
        ca = ""
        if self.record:
            ca = self.record.get("corrective_action", "")
            cr = self.record.get("corrective_result", "")
            if cr and cr not in ca:
                ca = ca + "\n\n[原矯正結果]\n" + cr if ca else cr
                
        html = f"""
        <div style="font-family: sans-serif; color: #000;">
            <h1 style="font-size: 16pt; text-align: center; margin-top: 0; margin-bottom: 5px; font-weight: bold;">品管異常紀錄單</h1>
            <p style="font-size: 10pt; text-align: right; margin-top: 0; margin-bottom: 10px;">文件編號：___________________</p>
            
            <table width="100%" cellpadding="8" cellspacing="0" style="font-size: 11pt; border: 2px solid #000; border-collapse: collapse;">
                <!-- Basic Info -->
                <tr>
                    <td width="50%" style="border-bottom: 1px dotted #ccc; border-right: none;"><b>紀錄單號：</b> {self.serial_number}</td>
                    <td width="50%" style="border-bottom: 1px dotted #ccc; border-left: none;"><b>儀器：</b> {self.instrument_name}</td>
                </tr>
                <tr>
                    <td style="border-bottom: 1px dotted #ccc; border-right: none;"><b>品管液批號：</b> {self.qc_lot_number}</td>
                    <td style="border-bottom: 1px dotted #ccc; border-left: none;"><b>Level：</b> {self.level_name}</td>
                </tr>
                <tr>
                    <td style="border-bottom: 1px solid #000; border-right: none;"><b>發生時間：</b> {self.occurrence_time}</td>
                    <td style="border-bottom: 1px solid #000; border-left: none;"><b>異常數據：</b> {self.anomaly_data} {f'(<span style="color:red;">{self.violated_rule}</span>)' if self.violated_rule and self.violated_rule != '無' else ''}</td>
                </tr>
                
                <!-- Checks -->
                <tr>
                    <td colspan="2" style="border-bottom: 1px solid #000;">
                        <h3 style="font-size: 12pt; margin: 5px 0;">檢查項目</h3>
                        <p style="margin: 5px 0; line-height: 1.5;">
                            {checks[0]} 機器：機器情況<br>
                            {checks[1]} 試劑：開封效期、試劑量<br>
                            {checks[2]} 校正液：開封效期、校正液量<br>
                            {checks[3]} 品管液：開封效期、品管液量
                        </p>
                    </td>
                </tr>
                
                <!-- Cause & Corrective Action -->
                <tr>
                    <td colspan="2" style="border-bottom: 1px solid #000; vertical-align: top;">
                        <h3 style="font-size: 12pt; margin: 5px 0;">異常原因</h3>
                        <p style="margin: 5px 0 15px 0;">{self.record.get('anomaly_cause', '').replace(chr(10), '<br>')}</p>
                        
                        <h3 style="font-size: 12pt; margin: 5px 0;">矯正措施/矯正結果 (醫檢師)</h3>
                        <p style="margin: 5px 0 15px 0;">{ca.replace(chr(10), '<br>')}</p>
                        
                        <div style="text-align: right; margin-top: 20px;">醫檢師：______________________</div>
                    </td>
                </tr>
                
                <!-- Preventive Action -->
                <tr>
                    <td colspan="2" style="border-bottom: 1px solid #000; vertical-align: top;">
                        <h3 style="font-size: 12pt; margin: 5px 0;">預防措施 (組長)</h3>
                        <p style="margin: 5px 0 15px 0;">{self.record.get('preventive_action', '').replace(chr(10), '<br>')}</p>
                        
                        <div style="text-align: right; margin-top: 20px;">組長：______________________</div>
                    </td>
                </tr>
                
                <!-- Tracking -->
                <tr>
                    <td colspan="2" style="border-bottom: 1px solid #000; vertical-align: middle; padding: 0;">
                        <table width="100%" border="0" cellpadding="8" cellspacing="0">
                            <tr>
                                <td width="50%" style="vertical-align: middle;">
                                    <p style="margin: 5px 0; line-height: 1.8;">
                                        &#9744; 追蹤，請於 &nbsp;&nbsp;&nbsp;年 &nbsp;&nbsp;&nbsp;月 &nbsp;&nbsp;&nbsp;日回覆<br>
                                        &#9744; 無需追蹤
                                    </p>
                                </td>
                                <td width="50%" style="vertical-align: bottom; text-align: right;">
                                    <div>技術主任：______________________</div>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                
                <!-- Follow up -->
                <tr>
                    <td colspan="2" style="vertical-align: top;">
                        <p style="margin: 5px 0;">當事人回覆追蹤情況(如果需要)與蓋章</p>
                        <br><br><br>
                    </td>
                </tr>
            </table>
        </div>
        """
        return html

    def _print_record(self):
        try:
            from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
        except ImportError:
            QMessageBox.critical(self, "錯誤", "缺少列印支援套件。")
            return
            
        from PyQt6.QtGui import QTextDocument
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            doc = QTextDocument()
            doc.setHtml(self._get_print_html())
            doc.print(printer)

    def _export_pdf(self):
        try:
            from PyQt6.QtPrintSupport import QPrinter
        except ImportError:
            QMessageBox.critical(self, "錯誤", "缺少列印支援套件。")
            return
            
        from PyQt6.QtGui import QTextDocument
        from PyQt6.QtWidgets import QFileDialog
        
        default_name = f"異常紀錄單_{self.serial_number}.pdf"
        filepath, _ = QFileDialog.getSaveFileName(self, "儲存 PDF", default_name, "PDF Files (*.pdf)")
        
        if not filepath:
            return
            
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(filepath)
        
        doc = QTextDocument()
        doc.setHtml(self._get_print_html())
        doc.print(printer)
        
        QMessageBox.information(self, "成功", f"PDF 已成功儲存至：\\n{filepath}")

class PhraseManagementDialog(QDialog):
    def __init__(self, parent, category_name, category_id):
        super().__init__(parent)
        self.category_id = category_id
        self.setWindowTitle(f"片語管理 - {category_name}")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        lbl_hint = QLabel("選取上方片語後，可於下方編輯內容。")
        lbl_hint.setStyleSheet("color: #666666; font-size: 13px;")
        layout.addWidget(lbl_hint)
        
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self.list_widget, 1)
        
        self.edit_text = QTextEdit()
        layout.addWidget(self.edit_text, 1)
        
        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("儲存變更")
        self.btn_save.setObjectName("btn_primary")
        self.btn_save.clicked.connect(self._save_phrase)
        self.btn_delete = QPushButton("刪除選取片語")
        self.btn_delete.clicked.connect(self._delete_phrase)
        btn_close = QPushButton("關閉")
        btn_close.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)

    def _load_data(self):
        self.list_widget.clear()
        self.phrases = AnomalyService.get_phrases(self.category_id)
        for p in self.phrases:
            # 顯示前30個字元作為列表項目
            display_text = p["text"].replace('\\n', ' ')
            if len(display_text) > 30:
                display_text = display_text[:30] + "..."
            self.list_widget.addItem(display_text)
            
    def _on_row_changed(self, row):
        if row >= 0 and row < len(self.phrases):
            self.edit_text.setPlainText(self.phrases[row]["text"])
        else:
            self.edit_text.clear()

    def _save_phrase(self):
        row = self.list_widget.currentRow()
        if row < 0: return
        new_text = self.edit_text.toPlainText().strip()
        if not new_text:
            QMessageBox.warning(self, "錯誤", "片語內容不能為空。")
            return
        template_id = self.phrases[row]["id"]
        AnomalyService.update_phrase(template_id, new_text)
        QMessageBox.information(self, "成功", "片語已成功更新。")
        self._load_data()
        self.list_widget.setCurrentRow(row)

    def _delete_phrase(self):
        row = self.list_widget.currentRow()
        if row < 0: return
        reply = QMessageBox.question(self, '確認刪除', '確定要刪除這個片語嗎？刪除後無法復原。', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            template_id = self.phrases[row]["id"]
            AnomalyService.delete_phrase(template_id)
            self._load_data()
            self.edit_text.clear()
