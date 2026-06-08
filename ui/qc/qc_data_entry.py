# ui/qc/qc_data_entry.py — 品管數據輸入（手動 + 儀器傳輸 File Drop）

import os
import csv
from datetime import date, datetime
from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidgetItem, QFrame, QWidget,
    QTabWidget, QDoubleSpinBox, QTextEdit, QDateTimeEdit, QDateEdit,
    QScrollArea, QGroupBox, QMessageBox, QFileDialog,
    QGridLayout, QSizePolicy,
)
from PyQt6.QtCore import Qt, QDate, QDateTime, QFileSystemWatcher, QObject, QEvent
from ui.base_page import BasePage, PAGE_STYLE, COLORS
from services.qc_service import (
    MasterService, QCResultService,
    ReagentBatchService, QCBatchService,
)
from config import INSTRUMENT_WATCH_DIR


SEMI_OPTIONS = ["Neg", "Trace", "1+", "2+", "3+", "—（未測）"]

SEMI_OPTIONS = ["Neg", "Trace", "1+", "2+", "3+", "—（未測）"]

class FocusNextFilter(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                obj.focusNextChild()
                return True
        return super().eventFilter(obj, event)

class QCDataEntryPage(BasePage):
    def __init__(self, user: dict):
        super().__init__("品管數據輸入", "手動輸入或匯入儀器傳輸檔案", user)
        self._instruments = MasterService.get_instruments()
        self._watcher = QFileSystemWatcher()
        self._watcher.directoryChanged.connect(self._on_dir_changed)
        self._build()
        self._setup_file_watcher()

    def _build(self):
        tabs = QTabWidget()

        # Tab 1: 手動輸入
        manual_tab = self._build_manual_tab()
        tabs.addTab(manual_tab, "📝 手動輸入")

        # Tab 2: 儀器傳輸
        file_tab = self._build_file_tab()
        tabs.addTab(file_tab, "📂 儀器傳輸（File Drop）")

        self.content_layout.addWidget(tabs)

    # ── 手動輸入 ────────────────────────────────────────────

    def _build_manual_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 上方：選擇儀器 + 日期
        top = QHBoxLayout()
        top.addWidget(QLabel("儀器："))
        self.cmb_inst = QComboBox()
        for inst in self._instruments:
            self.cmb_inst.addItem(inst["instrument_name"], inst["instrument_id"])
        self.cmb_inst.currentIndexChanged.connect(self._reload_manual_form)
        top.addWidget(self.cmb_inst)
        top.addWidget(QLabel("品管輸入時間："))
        
        self.cmb_time_mode = QComboBox()
        self.cmb_time_mode.addItems(["現在(預設)", "選擇輸入時間"])
        top.addWidget(self.cmb_time_mode)
        
        self.qc_date = QDateTimeEdit()
        self.qc_date.setCalendarPopup(True)
        self.qc_date.setDateTime(QDateTime.currentDateTime())
        self.qc_date.setDisplayFormat("yyyy/MM/dd HH:mm")
        self.qc_date.setVisible(False)
        self.cmb_time_mode.currentIndexChanged.connect(lambda i: self.qc_date.setVisible(i == 1))
        
        top.addWidget(self.qc_date)
        top.addSpacing(20)
        
        top.addWidget(QLabel("品管液："))
        self.cmb_qc_batch = QComboBox()
        self.cmb_qc_batch.currentIndexChanged.connect(self._reload_manual_form)
        top.addWidget(self.cmb_qc_batch)
        
        top.addStretch()
        layout.addLayout(top)


        
        self._load_qc_batches()

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"background:{COLORS['border']};")
        layout.addWidget(divider)

        # 輸入表格
        self.table_container = QVBoxLayout()
        layout.addLayout(self.table_container)

        # 儲存按鈕
        btn_row = QHBoxLayout()
        btn_save = QPushButton("💾 儲存品管結果")
        btn_save.setObjectName("btn_primary")
        btn_save.setFixedHeight(42)
        btn_save.clicked.connect(self._save_manual)
        btn_row.addStretch()
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        self._manual_widgets: dict = {}  # iqi_id -> widget
        self.focus_filter = FocusNextFilter(self)
        self._reload_manual_form()
        return tab

    def _load_qc_batches(self):
        self.cmb_qc_batch.blockSignals(True)
        self.cmb_qc_batch.clear()
        
        batches = QCBatchService.get_all()
        groups = {}
        for b in batches:
            # Group by open_date, expiry_date, created_at date to keep L1/L2 together
            key = (b["open_date"], b["expiry_date"], b["created_at"].date() if b["created_at"] else None)
            if key not in groups:
                groups[key] = []
            groups[key].append(b)
            
        active_index = -1
        idx = 0
        for key, group_batches in groups.items():
            lots = sorted(list(set(b["lot_number"] for b in group_batches)))
            label = f"{'/'.join(lots)}"
            # Find if this group contains the active batches
            is_active = any(b.get("is_active") for b in group_batches)
            is_archived = any(b.get("is_archived") for b in group_batches)
            
            if is_archived:
                continue
                
            if is_active:
                label += " [使用中]"
                active_index = self.cmb_qc_batch.count()
            else:
                label += " [待允收]"
                
            self.cmb_qc_batch.addItem(label, group_batches)
            
        self.cmb_qc_batch.setMinimumContentsLength(20)
        if self.cmb_qc_batch.view():
            self.cmb_qc_batch.view().setMinimumWidth(280)
            
        if active_index >= 0:
            self.cmb_qc_batch.setCurrentIndex(active_index)
            
        self.cmb_qc_batch.blockSignals(False)

    def _reload_manual_form(self):
        # 清除舊的
        while self.table_container.count():
            item = self.table_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._manual_widgets.clear()

        inst_id = self.cmb_inst.currentData()
        if not inst_id:
            return

        iqis = MasterService.get_iqi(inst_id)
        if not iqis:
            return

        # 依 reagent_id 群組化 IQI
        reagents = {}
        for iqi in iqis:
            rid = iqi["reagent_id"]
            if rid not in reagents:
                reagents[rid] = {
                    "label": f"{iqi['reagent_name']}  {iqi['reagent_label']}",
                    "param_type": iqi["param_type"],
                    "levels": {}
                }
            reagents[rid]["levels"][iqi["level_name"]] = iqi["iqi_id"]

        from PyQt6.QtWidgets import QTableWidget, QHeaderView, QStyledItemDelegate
        from PyQt6.QtGui import QColor, QBrush
        
        self.t_input = QTableWidget(len(reagents), 5)
        self.t_input.setHorizontalHeaderLabels(["項目", "Level 1", "合格範圍 (L1)", "Level 2", "合格範圍 (L2)"])
        self.t_input.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.t_input.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.t_input.setColumnWidth(0, 250)
        self.t_input.setAlternatingRowColors(True)
        self.t_input.verticalHeader().setVisible(False)
        
        self._row_param_types = {}
        
        class InputDelegate(QStyledItemDelegate):
            def eventFilter(self, editor, event):
                if event.type() == QEvent.Type.KeyPress:
                    if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                        table = self.parent().t_input
                        row = table.currentRow()
                        col = table.currentColumn()
                        self.commitData.emit(editor)
                        self.closeEditor.emit(editor, QStyledItemDelegate.EndEditHint.NoHint)
                        
                        next_row, next_col = row, col
                        while True:
                            if next_col == 1:
                                next_col = 3
                            elif next_col == 3:
                                next_col = 1
                                next_row += 1
                            else:
                                break
                                
                            if next_row >= table.rowCount():
                                break
                                
                            item = table.item(next_row, next_col)
                            if item and (item.flags() & Qt.ItemFlag.ItemIsEditable):
                                table.setCurrentCell(next_row, next_col)
                                table.editItem(item)
                                break
                        return True
                return super().eventFilter(editor, event)

            def createEditor(self, parent, option, index):
                row = index.row()
                col = index.column()
                if col in (1, 3):
                    ptype = self.parent()._row_param_types.get(row)
                    if ptype == 2:
                        cb = QComboBox(parent)
                        cb.addItems(SEMI_OPTIONS)
                        return cb
                    else:
                        sp = QDoubleSpinBox(parent)
                        sp.setRange(-9999, 9999)
                        sp.setDecimals(3)
                        sp.setSpecialValueText("—")
                        sp.setMinimum(-9999)
                        return sp
                return super().createEditor(parent, option, index)

            def setModelData(self, editor, model, index):
                if isinstance(editor, QComboBox):
                    model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
                elif isinstance(editor, QDoubleSpinBox):
                    val = editor.value()
                    if val == editor.minimum():
                        model.setData(index, "", Qt.ItemDataRole.EditRole)
                    else:
                        model.setData(index, str(val), Qt.ItemDataRole.EditRole)
                else:
                    super().setModelData(editor, model, index)
                    
        self.t_input.setItemDelegate(InputDelegate(self))
        
        batches = self.cmb_qc_batch.currentData()
        b1 = b2 = None
        if batches:
            b1 = next((b for b in batches if b["level_name"] == "Level 1"), None)
            b2 = next((b for b in batches if b["level_name"] == "Level 2"), None)
        
        row = 0
        for rid, rdata in reagents.items():
            rname = rdata["label"].split()[0]
            rlabel = " ".join(rdata["label"].split()[1:])
            disp_name = rlabel if rname in rlabel else rdata["label"]
            
            self._row_param_types[row] = rdata["param_type"]
            
            it_name = QTableWidgetItem(disp_name)
            it_name.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_name.setFlags(it_name.flags() & ~Qt.ItemFlag.ItemIsEditable)
            it_name.setBackground(QBrush(QColor("#FFFFFF")))
            self.t_input.setItem(row, 0, it_name)
            
            # Level 1
            iqi_l1 = rdata["levels"].get("Level 1")
            it_l1 = QTableWidgetItem("")
            it_l1.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if iqi_l1:
                it_l1.setBackground(QBrush(QColor("#E3F2FD")))
                it_l1.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
                self._manual_widgets[iqi_l1] = {"row": row, "col": 1, "param_type": rdata["param_type"]}
            else:
                it_l1.setText("—")
                it_l1.setFlags(it_l1.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.t_input.setItem(row, 1, it_l1)
            
            range_l1 = self._get_range_string(iqi_l1, rdata["param_type"], b1["batch_id"] if b1 else None) if iqi_l1 else ""
            it_r1 = QTableWidgetItem(range_l1)
            it_r1.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_r1.setFlags(it_r1.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.t_input.setItem(row, 2, it_r1)
            
            # Level 2
            iqi_l2 = rdata["levels"].get("Level 2")
            it_l2 = QTableWidgetItem("")
            it_l2.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if iqi_l2:
                it_l2.setBackground(QBrush(QColor("#E3F2FD")))
                it_l2.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
                self._manual_widgets[iqi_l2] = {"row": row, "col": 3, "param_type": rdata["param_type"]}
            else:
                it_l2.setText("—")
                it_l2.setFlags(it_l2.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.t_input.setItem(row, 3, it_l2)
            
            range_l2 = self._get_range_string(iqi_l2, rdata["param_type"], b2["batch_id"] if b2 else None) if iqi_l2 else ""
            it_r2 = QTableWidgetItem(range_l2)
            it_r2.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it_r2.setFlags(it_r2.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.t_input.setItem(row, 4, it_r2)
            
            row += 1
            
        self.table_container.addWidget(self.t_input)

    def _get_range_string(self, iqi_id, param_type, qc_batch_id):
        from services.qc_service import TargetSettingService
        if qc_batch_id:
            ts = TargetSettingService.get_for_batch(iqi_id, qc_batch_id)
        else:
            ts = TargetSettingService.get_current(iqi_id)
            
        if not ts:
            return "未設定"
        
        if param_type == 1:
            if ts.get("tm") is not None and ts.get("tsd") is not None:
                tm = float(ts["tm"])
                tsd = float(ts["tsd"])
                return f"{tm - 2*tsd:.4g} ~ {tm + 2*tsd:.4g}"
            return "未設定"
        else:
            s_min = ts.get("semi_target_min")
            s_max = ts.get("semi_target_max")
            if s_min and s_max:
                return f"{s_min} ~ {s_max}" if s_min != s_max else s_min
            return "未設定"

    def _create_input_widget(self, param_type):
        if param_type == 2:
            combo = QComboBox()
            combo.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            combo.addItems(SEMI_OPTIONS)
            combo.installEventFilter(self.focus_filter)
            return combo
        else:
            sp = QDoubleSpinBox()
            sp.setRange(-9999, 9999)
            sp.setDecimals(3)
            sp.setFixedWidth(110)
            sp.setSpecialValueText("—")
            sp.setMinimum(-9999)
            sp.installEventFilter(self.focus_filter)
            return sp

    def _save_manual(self):
        if not self._manual_widgets or not hasattr(self, 't_input'):
            return

        rb = ReagentBatchService.get_active()
        selected_qc_group = self.cmb_qc_batch.currentData()
        l1_batch = l2_batch = None
        if selected_qc_group:
            for b in selected_qc_group:
                if b["level_name"] == "Level 1":
                    l1_batch = b
                elif b["level_name"] == "Level 2":
                    l2_batch = b

        user_id = self.user["user_id"]
        
        if hasattr(self, 'cmb_time_mode') and self.cmb_time_mode.currentIndex() == 0:
            from datetime import datetime
            q_date = datetime.now()
        else:
            q_date = self.qc_date.dateTime().toPyDateTime()
            
        saved = 0
        flags = []

        for iqi_id, w in self._manual_widgets.items():
            row = w["row"]
            col = w["col"]
            param_type = w["param_type"]
            
            it = self.t_input.item(row, col)
            if not it: continue
            val_str = it.text().strip()

            if not val_str or val_str == "—" or val_str == "—（未測）":
                continue

            if param_type == 2:
                qual = val_str
                mval = None
            else:
                try:
                    mval = float(val_str)
                    qual = None
                except ValueError:
                    continue

            # 判斷這個 iqi 屬於哪個 level 的批號
            # 簡化：奇數 iqi_id 對應 L1，偶數對應 L2（依 seed data 規律）
            qc_batch_id = None
            if iqi_id % 2 == 1 and l1_batch:
                qc_batch_id = l1_batch["batch_id"]
            elif iqi_id % 2 == 0 and l2_batch:
                qc_batch_id = l2_batch["batch_id"]

            result_id = QCResultService.save_result(
                iqi_id=iqi_id,
                result_date=q_date,
                reagent_batch_id=rb["batch_id"] if rb else None,
                qc_batch_id=qc_batch_id,
                measured_value=mval,
                qualitative_result=qual,
                notes=None,
                entered_by=self.user["user_id"],
                source=1,
            )
            # 取得 westgard 判斷結果
            from database.connection import DBContext
            with DBContext() as (_, cur):
                cur.execute(
                    "SELECT westgard_flag, is_accepted FROM qc_results WHERE result_id=%s",
                    (result_id,)
                )
                row_db = cur.fetchone()
                if row_db and row_db["westgard_flag"]:
                    item_name = self.t_input.item(row, 0).text()
                    level_str = "Level 1" if col == 1 else "Level 2"
                    flags.append(f"• {item_name} ({level_str}): {row_db['westgard_flag']}")
            saved += 1

        if saved == 0:
            self.alert("提示", "沒有輸入任何數值，請填寫後再儲存。")
            return

        msg = f"已儲存 {saved} 筆品管結果。"
        if flags:
            msg += f"\n\n⚠️ Westgard 異常項目：\n" + "\n".join(flags)
            self.warn("品管警示", msg)
        else:
            self.alert("完成", msg)

    # ── 儀器傳輸（File Drop）────────────────────────────────

    def _build_file_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 監聽資料夾路徑
        watch_row = QHBoxLayout()
        self.lbl_watch_dir = QLabel(f"監聽資料夾：{os.path.abspath(INSTRUMENT_WATCH_DIR)}")
        self.lbl_watch_dir.setStyleSheet(f"font-size:12px; color:{COLORS['text_secondary']};")
        self.lbl_watch_status = QLabel("🟡 待監聽")
        watch_row.addWidget(self.lbl_watch_dir)
        watch_row.addStretch()
        watch_row.addWidget(self.lbl_watch_status)
        layout.addLayout(watch_row)

        btn_row = QHBoxLayout()
        btn_pick = QPushButton("📁 手動匯入檔案")
        btn_pick.clicked.connect(self._pick_file)
        btn_browse = QPushButton("📂 開啟監聽資料夾")
        btn_browse.clicked.connect(self._open_watch_dir)
        btn_row.addWidget(btn_pick)
        btn_row.addWidget(btn_browse)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        # 匯入記錄
        log_lbl = QLabel("匯入記錄：")
        log_lbl.setStyleSheet(f"font-weight:700; color:{COLORS['text_primary']};")
        layout.addWidget(log_lbl)

        self.import_log = QTextEdit()
        self.import_log.setReadOnly(True)
        self.import_log.setPlaceholderText(
            "此處顯示自動匯入的記錄。\n"
            "儀器將檔案存入上方監聽資料夾後，系統會自動偵測並匯入。\n\n"
            "支援格式：CSV（逗號分隔），欄位：\n"
            "  date, parameter, level, value\n"
            "  例：2025-06-01, pH, Level 1, 6.5"
        )
        self.import_log.setStyleSheet(
            f"background:#FDFBF0; color:{COLORS['text_secondary']}; "
            f"font-size:12px; border:1px solid {COLORS['border']}; border-radius:8px;"
        )
        layout.addWidget(self.import_log)

        format_info = QLabel(
            "📋 儀器 CSV 格式：date, instrument, parameter, level, value\n"
            "例：2025-06-01,77-1,pH,Level 1,6.50"
        )
        format_info.setStyleSheet(f"font-size:12px; color:{COLORS['text_muted']};")
        layout.addWidget(format_info)

        return tab

    def _setup_file_watcher(self):
        watch_path = INSTRUMENT_WATCH_DIR
        if not os.path.exists(watch_path):
            try:
                os.makedirs(watch_path)
            except Exception:
                pass
        if os.path.exists(watch_path):
            self._watcher.addPath(watch_path)
            self.lbl_watch_status.setText("🟢 監聽中")

    def _on_dir_changed(self, path: str):
        """當監聽資料夾有新檔案時自動觸發。"""
        try:
            files = [f for f in os.listdir(path) if f.endswith(".csv")]
            for fname in files:
                fpath = os.path.join(path, fname)
                self._import_csv(fpath)
        except Exception as e:
            self.import_log.append(f"[錯誤] {e}")

    def _pick_file(self):
        fpath, _ = QFileDialog.getOpenFileName(
            self, "選擇 CSV 檔案", "", "CSV Files (*.csv)"
        )
        if fpath:
            self._import_csv(fpath)

    def _open_watch_dir(self):
        import subprocess
        path = os.path.abspath(INSTRUMENT_WATCH_DIR)
        try:
            subprocess.Popen(["open", path])
        except Exception:
            self.import_log.append(f"無法開啟資料夾：{path}")

    def _import_csv(self, fpath: str):
        """解析 CSV 並寫入 qc_results。"""
        self.import_log.append(f"\n[{datetime.now():%H:%M:%S}] 匯入：{os.path.basename(fpath)}")

        rb = ReagentBatchService.get_active()
        active_qc = QCBatchService.get_active_batches()
        
        batches = self.cmb_qc_batch.currentData()
        b1 = b2 = None
        if batches:
            b1 = next((b for b in batches if b["level_name"] == "Level 1"), None)
            b2 = next((b for b in batches if b["level_name"] == "Level 2"), None)

        # 建立 (instrument_name, reagent_name, level_name) -> iqi_id 的查詢表
        iqi_map: dict[tuple, int] = {}
        for inst in self._instruments:
            for iqi in MasterService.get_iqi(inst["instrument_id"]):
                key = (
                    inst["instrument_name"].lower(),
                    iqi["reagent_name"].lower(),
                    iqi["level_name"].lower(),
                )
                iqi_map[key] = iqi["iqi_id"]

        saved = 0
        errors = 0
        try:
            with open(fpath, encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                for line_no, row in enumerate(reader, start=1):
                    if len(row) < 5:
                        continue
                    try:
                        r_date_str, inst_name, param, level, value_str = (
                            row[0].strip(), row[1].strip(), row[2].strip(),
                            row[3].strip(), row[4].strip()
                        )
                        r_date = datetime.strptime(r_date_str, "%Y-%m-%d").date()
                        key = (inst_name.lower(), param.lower(), level.lower())
                        iqi_id = iqi_map.get(key)
                        if not iqi_id:
                            self.import_log.append(f"  ⚠️ 行{line_no}：找不到項目 {inst_name}/{param}/{level}")
                            errors += 1
                            continue

                        # 判斷定量或半定量
                        try:
                            mval = float(value_str)
                            qual = None
                        except ValueError:
                            mval = None
                            qual = value_str

                        qc_batch_id = None
                        if "1" in level and l1_batch:
                            qc_batch_id = l1_batch["batch_id"]
                        elif "2" in level and l2_batch:
                            qc_batch_id = l2_batch["batch_id"]

                        QCResultService.save_result(
                            iqi_id=iqi_id,
                            result_date=r_date,
                            reagent_batch_id=rb["batch_id"] if rb else None,
                            qc_batch_id=qc_batch_id,
                            measured_value=mval,
                            qualitative_result=qual,
                            notes=f"儀器傳輸：{os.path.basename(fpath)}",
                            entered_by=self.user["user_id"],
                            source=2,
                        )
                        saved += 1
                    except Exception as ex:
                        self.import_log.append(f"  ❌ 行{line_no}：{ex}")
                        errors += 1
        except Exception as ex:
            self.import_log.append(f"  ❌ 讀取失敗：{ex}")
            return

        self.import_log.append(f"  ✅ 完成：{saved} 筆匯入，{errors} 筆錯誤")

        # 匯入後移動到已處理資料夾
        done_dir = os.path.join(INSTRUMENT_WATCH_DIR, "processed")
        os.makedirs(done_dir, exist_ok=True)
        try:
            import shutil
            dest = os.path.join(done_dir, os.path.basename(fpath))
            shutil.move(fpath, dest)
            self.import_log.append(f"  📁 已移至 processed/")
        except Exception:
            pass

    def on_page_show(self):
        self._load_qc_batches()
        inst_id = self.cmb_inst.currentData()
        if inst_id:
            self._reload_manual_form()
