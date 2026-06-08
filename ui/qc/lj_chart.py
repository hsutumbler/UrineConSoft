# ui/qc/lj_chart.py — L-J Chart 品管圖

import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QDateEdit, QPushButton, QSplitter, QListWidget, QListWidgetItem,
    QFrame, QMessageBox, QScrollBar, QMenu, QInputDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor, QCursor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import matplotlib

from config import DEFAULT_FONT
# 設定中文字型，與主程式一致
matplotlib.rcParams['font.sans-serif'] = [DEFAULT_FONT, 'PingFang TC', 'Heiti TC', 'Microsoft JhengHei', 'sans-serif']
matplotlib.rcParams['axes.unicode_minus'] = False

from ui.base_page import BasePage, PAGE_STYLE, COLORS
from services.qc_service import MasterService, QCResultService, TargetSettingService, QCBatchService


class LJChartPage(BasePage):
    def __init__(self, user: dict):
        super().__init__("品管圖 (L-J Chart)", "查看各項目的 Levey-Jennings Chart", user)
        self._instruments = MasterService.get_instruments()
        self._build()

    def _build(self):
        # 上方過濾列
        filter_bar = QHBoxLayout()
        
        filter_bar.addWidget(QLabel("選擇儀器："))
        self.cmb_inst = QComboBox()
        for inst in self._instruments:
            self.cmb_inst.addItem(inst["instrument_name"], inst["instrument_id"])
        self.cmb_inst.currentIndexChanged.connect(self._reload_items)
        filter_bar.addWidget(self.cmb_inst)
        
        filter_bar.addStretch()
        
        filter_bar.addWidget(QLabel("品管液批號："))
        self.cmb_batch = QComboBox()
        self.cmb_batch.setMinimumContentsLength(20)
        if self.cmb_batch.view():
            self.cmb_batch.view().setMinimumWidth(280)
        self.cmb_batch.currentIndexChanged.connect(self._draw_chart)
        filter_bar.addWidget(self.cmb_batch)
        
        filter_bar.addStretch()
        
        filter_bar.addWidget(QLabel("日期區間："))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        
        filter_bar.addWidget(self.date_from)
        filter_bar.addWidget(QLabel("~"))
        filter_bar.addWidget(self.date_to)
        
        filter_bar.addStretch()
        
        btn_refresh = QPushButton("更新圖表")
        btn_refresh.setObjectName("btn_primary")
        btn_refresh.clicked.connect(self._draw_chart)
        filter_bar.addWidget(btn_refresh)
        
        self.content_layout.addLayout(filter_bar)
        
        # 分割畫面：左側項目列表，右側圖表
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左側：項目列表
        self.list_items = QListWidget()
        self.list_items.setMaximumWidth(90)
        self.list_items.setStyleSheet(f"""
            QListWidget {{
                background: {COLORS['bg_input']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {COLORS['grid']};
            }}
            QListWidget::item:selected {{
                background: {COLORS['table_select']};
                color: {COLORS['accent']};
                font-weight: bold;
            }}
        """)
        self.list_items.itemSelectionChanged.connect(lambda: self._draw_chart(reset_scroll=True))
        splitter.addWidget(self.list_items)
        
        # 右側：圖表區
        self.charts_container = QFrame()
        self.charts_container.setObjectName("section_card")
        self.charts_layout = QVBoxLayout(self.charts_container)
        
        splitter.addWidget(self.charts_container)
        splitter.setSizes([90, 910])
        
        self.content_layout.addWidget(splitter, 1)
        
        self._hover_info = []
        self._reload_items()

    def _reload_items(self):
        self.list_items.clear()
        inst_id = self.cmb_inst.currentData()
        if not inst_id:
            return
            
        iqis = MasterService.get_iqi(inst_id)
        reagents = {}
        for iqi in iqis:
            rname = iqi["reagent_name"]
            if rname not in reagents:
                reagents[rname] = {
                    "reagent_name": rname,
                    "param_type": iqi["param_type"],
                    "iqis": {}
                }
            reagents[rname]["iqis"][iqi["level_name"]] = iqi
            
        for rname, rdata in reagents.items():
            item = QListWidgetItem(rname)
            item.setData(Qt.ItemDataRole.UserRole, rdata)
            self.list_items.addItem(item)
            
        if self.list_items.count() > 0:
            self.list_items.setCurrentRow(0)

    def _draw_chart(self, reset_scroll=False):
        item = self.list_items.currentItem()
        if not item:
            self._clear_chart()
            return
            
        # Store scrollbar states to restore after redraw (e.g., after adding a note)
        old_scrolls = {}
        if not reset_scroll and hasattr(self, '_chart_widgets'):
            for i, cw in enumerate(self._chart_widgets):
                if cw['scrollbar'].isVisible():
                    old_scrolls[i] = cw['scrollbar'].value()
                    
        self._clear_chart()
        self._hover_info = []
        self._chart_widgets = []
        
        rdata = item.data(Qt.ItemDataRole.UserRole)
        from_date = self.date_from.date().toPyDate()
        to_date = self.date_to.date().toPyDate()
        
        levels = list(rdata["iqis"].keys())
        levels.sort()  # Ensures Level 1 comes before Level 2
        
        from matplotlib.gridspec import GridSpec
        
        # 取得目前的 active_batch 資訊
        active_batches = {}
        for b in QCBatchService.get_all():
            if b["is_active"] and b["level_name"] not in active_batches:
                active_batches[b["level_name"]] = b
                
        # 取得所有批號以便過濾
        all_batches = QCBatchService.get_all()
        batch_id_to_lot = {b["batch_id"]: b["lot_number"] for b in all_batches}
        selected_lots = self.cmb_batch.currentData()
        
        for idx, level_name in enumerate(levels):
            iqi = rdata["iqis"][level_name]
            
            # Create independent UI for this level
            level_widget = QWidget()
            level_layout = QVBoxLayout(level_widget)
            level_layout.setContentsMargins(0, 0, 0, 10)
            
            fig = Figure(figsize=(8, 3.5), dpi=100)
            fig.patch.set_facecolor('#FDFBF0')
            canvas = FigureCanvas(fig)
            
            scrollbar = QScrollBar(Qt.Orientation.Horizontal)
            scrollbar.hide()
            
            # Use QHBoxLayout to align scrollbar under the right-side chart (ratio 1 : 3.5)
            scroll_layout = QHBoxLayout()
            scroll_layout.setContentsMargins(0, 0, 0, 0)
            spacer = QWidget()
            scroll_layout.addWidget(spacer, 10)  # matching ratio 1
            scroll_layout.addWidget(scrollbar, 35) # matching ratio 3.5
            
            level_layout.addWidget(canvas)
            level_layout.addLayout(scroll_layout)
            self.charts_layout.addWidget(level_widget)
            
            canvas.mpl_connect("motion_notify_event", self._on_hover)
            canvas.mpl_connect("button_press_event", self._on_click)
            
            gs = GridSpec(1, 2, width_ratios=[1, 3.5], figure=fig)
            
            if selected_lots:
                display_batch = next((b for b in all_batches if b["level_name"] == level_name and b["lot_number"] in selected_lots), None)
            else:
                display_batch = active_batches.get(level_name)
            
            ax_stats = fig.add_subplot(gs[0, 0])
            ax_stats.axis('on')
            ax_stats.set_xticks([])
            ax_stats.set_yticks([])
            for spine in ax_stats.spines.values():
                spine.set_edgecolor('#B5A97A')
                spine.set_linewidth(1.5)
            ax_stats.set_facecolor('#F6F4E8')
            
            ax = fig.add_subplot(gs[0, 1])
            ax.set_facecolor('#FFFEF7')
            ax.tick_params(axis='both', which='major', labelsize=8.5)
            
            title = f"{iqi['reagent_name']} - {level_name}"
            ax_stats.set_title(title, fontsize=10, pad=8)
            
            annot = ax.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                                bbox=dict(boxstyle="round,pad=0.5", fc="lightyellow", alpha=0.9),
                                fontsize=9, zorder=20)
            annot.set_visible(False)
            
            results = QCResultService.get_results(iqi["iqi_id"], from_date, to_date)
            
            if selected_lots:
                results = [r for r in results if batch_id_to_lot.get(r["qc_batch_id"]) in selected_lots]
            
            if not results:
                ax.text(0.5, 0.5, '此區間無品管資料', ha='center', va='center', transform=ax.transAxes)
                continue

            # 強制依照日期與輸入時間進行遞增排序 (從以前到現在)
            results.sort(key=lambda r: (r["result_date"], r["entered_at"] if "entered_at" in r else r["result_date"]))

            scatters = []
            cell_text = []
            if iqi["param_type"] == 1:
                scatters, cell_text, num_points = self._draw_quantitative(ax, iqi, results, display_batch)
            else:
                scatters, cell_text, num_points = self._draw_semi_quantitative(ax, iqi, results, display_batch)
            
            # 在左側 ax_stats 畫統計資料 (正式表格形式)
            table = ax_stats.table(cellText=cell_text, loc='center', cellLoc='center', edges='open', bbox=[0, 0, 1, 1])
            table.auto_set_font_size(False)
            table.set_fontsize(7.5)
            
            # 第一列加上底色與粗體
            for (row, col), cell in table.get_celld().items():
                cell.set_facecolor('none') # 讓儲存格背景透明以顯示 ax_stats 背景
                # 移除內部 padding，避免字距太開被擠壓
                cell.PAD = 0.05
                
                if row == 0:
                    cell.set_facecolor('#E6E2D1')
                    cell.set_text_props(weight='bold', color='#4A442D', ha='center')
                else:
                    if col == 0:
                        cell.set_text_props(weight='bold', color='#4A442D', ha='center')
                    elif row == 1:
                        cell.set_text_props(weight='bold', color='#6B6444', ha='center')
                    else:
                        cell.set_text_props(ha='center')
            
            if num_points > 30:
                scrollbar.show()
                scrollbar.setRange(0, num_points - 30)
                if idx in old_scrolls:
                    scrollbar.setValue(old_scrolls[idx])
                else:
                    scrollbar.setValue(num_points - 30)
                val = scrollbar.value()
                ax.set_xlim(val - 0.5, val + 30 - 0.5)
            else:
                scrollbar.hide()
                ax.set_xlim(-0.5, max(num_points - 0.5, 0.5))
                
            fig.tight_layout(w_pad=0.5)
            canvas.draw()
            
            def make_on_scroll(ax_l, canvas_l):
                def on_scroll(value):
                    ax_l.set_xlim(value - 0.5, value + 30 - 0.5)
                    canvas_l.draw_idle()
                return on_scroll
            
            scrollbar.valueChanged.connect(make_on_scroll(ax, canvas))
            self._chart_widgets.append({'canvas': canvas, 'scrollbar': scrollbar})
            
            self._hover_info.append({
                'ax': ax,
                'scatters': scatters,
                'annot': annot,
                'canvas': canvas,
                'level_name': level_name
            })

    def _draw_quantitative(self, ax, iqi, results, active_batch):
        values = [float(r["measured_value"]) if r["measured_value"] is not None else None for r in results]
        
        # 取得 TM / TSD 畫基準線
        ts = None
        if active_batch:
            ts = TargetSettingService.get_for_batch(iqi["iqi_id"], active_batch["batch_id"])
        
        tm = float(ts["tm"]) if ts and ts.get("tm") is not None else None
        tsd = float(ts["tsd"]) if ts and ts.get("tsd") is not None else None
        
        # 過濾掉 None 的資料以利繪圖
        valid_dates = []
        valid_values = []
        
        x_acc, y_acc, data_acc = [], [], []
        x_rej_in, y_rej_in, data_rej_in = [], [], []
        x_rej_out, y_rej_out, data_rej_out = [], [], []
        x_notes, y_notes = [], []
        x_anomaly, y_anomaly = [], []
        
        for v, r in zip(values, results):
            if v is not None:
                drawn_v = v
                is_out = False
                is_out_of_bounds = False
                if tm is not None and tsd is not None:
                    # 限制繪圖座標在 Y 軸可視範圍內 (±3.4SD) 以免飛出圖表外
                    max_v = tm + 3.4 * tsd
                    min_v = tm - 3.4 * tsd
                    if drawn_v > max_v: 
                        drawn_v = max_v
                        is_out_of_bounds = True
                    if drawn_v < min_v: 
                        drawn_v = min_v
                        is_out_of_bounds = True

                valid_dates.append(r["result_date"])
                valid_values.append(drawn_v)
                idx = len(valid_dates) - 1
                
                if r.get("notes") and r.get("notes").strip():
                    x_notes.append(idx)
                    y_notes.append(drawn_v)
                    
                if r.get("has_anomaly"):
                    x_anomaly.append(idx)
                    y_anomaly.append(drawn_v)
                        
                is_accepted = r.get("is_accepted")
                rejected = False
                if is_accepted is False or is_accepted == 0:
                    rejected = True
                    
                if rejected:
                    if is_out_of_bounds:
                        x_rej_out.append(idx)
                        y_rej_out.append(drawn_v)
                        data_rej_out.append(r)
                    else:
                        x_rej_in.append(idx)
                        y_rej_in.append(drawn_v)
                        data_rej_in.append(r)
                else:
                    x_acc.append(idx)
                    y_acc.append(drawn_v)
                    data_acc.append(r)
                
        if not valid_dates:
             ax.text(0.5, 0.5, '無有效的定量資料', ha='center', va='center', transform=ax.transAxes)
             return [], [], 0

        x = range(len(valid_values))
        ax.plot(x, valid_values, marker='', linestyle='-', color='gray', alpha=0.5, markersize=4)
        
        scatters = []
        if x_acc:
            sc_acc = ax.scatter(x_acc, y_acc, c='black', marker='o', zorder=5)
            scatters.append((sc_acc, data_acc))
        if x_rej_in:
            sc_rej_in = ax.scatter(x_rej_in, y_rej_in, c='red', marker='o', zorder=6)
            scatters.append((sc_rej_in, data_rej_in))
        if x_rej_out:
            sc_rej_out = ax.scatter(x_rej_out, y_rej_out, c='red', marker='X', s=100, zorder=6)
            scatters.append((sc_rej_out, data_rej_out))
            
        if x_notes:
            # 針對有備註的點畫上橘黃色光圈
            ax.scatter(x_notes, y_notes, facecolors='none', edgecolors='#FFA500', s=180, linewidths=2.5, zorder=4)
            
        if x_anomaly:
            # 針對有異常紀錄的點畫上深紫色外層光圈
            ax.scatter(x_anomaly, y_anomaly, facecolors='none', edgecolors='#800080', s=350, linewidths=2.5, zorder=3)

        # 設定 X 軸標籤（僅顯示「日」）
        labels = []
        last_day = None
        for d in valid_dates:
            day_str = str(d.day)
            if day_str != last_day:
                labels.append(day_str)
                last_day = day_str
            else:
                labels.append("")

        ax.set_xticks(x)
        ax.set_xticklabels(labels)

        if tm is not None and tsd is not None:
            # 中間以 TM 畫線
            ax.axhline(tm, color='#8DB4E2', linestyle='-')
            
            # 在 +1SD, +2SD, +3SD 用淺色系畫線
            ax.axhline(tm + tsd, color='#E0E0E0', linestyle='--')
            ax.axhline(tm - tsd, color='#E0E0E0', linestyle='--')
            
            ax.axhline(tm + 2*tsd, color='#FFCCCC', linestyle='--')
            ax.axhline(tm - 2*tsd, color='#FFCCCC', linestyle='--')
            
            ax.axhline(tm + 3*tsd, color='#FFCCCC', linestyle='-.')
            ax.axhline(tm - 3*tsd, color='#FFCCCC', linestyle='-.')
            
            # Y 軸以 TM 為中心，範圍至 TM ± 3.5SD
            ax.set_ylim(tm - 3.5*tsd, tm + 3.5*tsd)
            
        # 計算統計資訊
        import numpy as np
        display_batch_id = active_batch["batch_id"] if active_batch else None
        t_stats = QCResultService.get_total_stats(iqi["iqi_id"], display_batch_id)
        
        r_n = len(valid_values)
        r_mean = f"{np.mean(valid_values):.2f}" if r_n > 0 else "—"
        r_sd = f"{np.std(valid_values, ddof=1):.3f}" if r_n > 1 else "—"
        r_cv = f"{(np.std(valid_values, ddof=1) / np.mean(valid_values))*100:.1f}%" if r_n > 1 and np.mean(valid_values)!=0 else "—"
        
        t_n = t_stats["n"]
        t_mean = f"{t_stats['mean']:.2f}" if t_stats["mean"] is not None else "—"
        t_sd = f"{t_stats['sd']:.3f}" if t_stats["sd"] is not None else "—"
        t_cv = f"{(t_stats['sd'] / t_stats['mean'])*100:.1f}%" if t_stats["mean"] and t_stats["sd"] else "—"
        
        lot_no = active_batch["lot_number"] if active_batch else "未設定"
        exp_dt = active_batch["expiry_date"].strftime("%Y/%m/%d") if active_batch and active_batch["expiry_date"] else "—"
        tm_str = f"{ts['tm']}" if ts and ts["tm"] is not None else "—"
        tsd_str = f"{ts['tsd']}" if ts and ts["tsd"] is not None else "—"
        
        cell_text = [
            ["", "", f"Lot {lot_no}", ""],
            ["", "Target", "T.Rec", "R.Rec"],
            ["N", "", str(t_n), str(r_n)],
            ["Mean", tm_str, t_mean, r_mean],
            ["SD", tsd_str, t_sd, r_sd],
            ["CV%", "", t_cv, r_cv],
            ["Exp.Dt", "", exp_dt, ""]
        ]
            
        return scatters, cell_text, len(valid_values)

    def _draw_semi_quantitative(self, ax, iqi, results, active_batch):
        # 半定量：將字串轉為對應的等級數值
        levels = {"Neg": 0, "Trace": 0.5, "1+": 1, "2+": 2, "3+": 3}
        y_labels = list(levels.keys())
        y_ticks = list(levels.values())
        
        valid_dates = []
        valid_values = []
        
        x_acc, y_acc, data_acc = [], [], []
        x_rej, y_rej, data_rej = [], [], []
        x_notes, y_notes = [], []
        x_anomaly, y_anomaly = [], []
        
        for r in results:
            qual = r["qualitative_result"]
            if qual in levels:
                val = levels[qual]
                valid_dates.append(r["result_date"])
                valid_values.append(val)
                idx = len(valid_dates) - 1
                
                if r.get("notes") and r.get("notes").strip():
                    x_notes.append(idx)
                    y_notes.append(val)
                    
                if r.get("has_anomaly"):
                    x_anomaly.append(idx)
                    y_anomaly.append(val)
                
                if r["is_accepted"]:
                    x_acc.append(idx)
                    y_acc.append(val)
                    data_acc.append(r)
                else:
                    x_rej.append(idx)
                    y_rej.append(val)
                    data_rej.append(r)
                
        if not valid_dates:
             ax.text(0.5, 0.5, '無有效的半定量資料', ha='center', va='center', transform=ax.transAxes)
             return [], [], 0
             
        x_all = range(len(valid_values))
        ax.plot(x_all, valid_values, marker='', linestyle='-', color='gray', alpha=0.5)
        
        scatters = []
        if x_acc:
            sc_acc = ax.scatter(x_acc, y_acc, c='black', marker='o', zorder=5)
            scatters.append((sc_acc, data_acc))
        if x_rej:
            sc_rej = ax.scatter(x_rej, y_rej, c='red', marker='o', zorder=6)
            scatters.append((sc_rej, data_rej))
            
        if x_notes:
            # 針對有備註的點畫上橘黃色光圈
            ax.scatter(x_notes, y_notes, facecolors='none', edgecolors='#FFA500', s=180, linewidths=2.5, zorder=4)
            
        if x_anomaly:
            # 針對有異常紀錄的點畫上深紫色外層光圈
            ax.scatter(x_anomaly, y_anomaly, facecolors='none', edgecolors='#800080', s=350, linewidths=2.5, zorder=3)
        
        labels = []
        last_day = None
        for d in valid_dates:
            day_str = str(d.day)
            if day_str != last_day:
                labels.append(day_str)
                last_day = day_str
            else:
                labels.append("")

        ax.set_xticks(x_all)
        ax.set_xticklabels(labels)
        
        ax.set_yticks(y_ticks)
        ax.set_yticklabels(y_labels)
        ax.set_ylim(-0.5, len(y_ticks) - 0.5)  # 動態對應所有等級的數量

        # 標示設定的合理品管範圍
        ts = None
        if active_batch:
            ts = TargetSettingService.get_for_batch(iqi["iqi_id"], active_batch["batch_id"])
            
        target_str = "未設定"
        if ts:
            s_min = ts.get("semi_target_min")
            s_max = ts.get("semi_target_max")
            if s_min and s_max and s_min in levels and s_max in levels:
                target_str = f"{s_min} ~ {s_max}" if s_min != s_max else s_min
                min_val = levels[s_min]
                max_val = levels[s_max]
                # 繪製範圍色塊，上下各延伸半格
                ax.axhspan(min_val - 0.25, max_val + 0.25, color='#E6F2FF', alpha=0.8, zorder=1)
                ax.axhline(min_val - 0.25, color='#8DB4E2', linestyle='--', alpha=0.7)
                ax.axhline(max_val + 0.25, color='#8DB4E2', linestyle='--', alpha=0.7)

        # 統計資訊
        display_batch_id = active_batch["batch_id"] if active_batch else None
        t_stats = QCResultService.get_total_stats(iqi["iqi_id"], display_batch_id)
        lot_no = active_batch["lot_number"] if active_batch else "未設定"
        exp_dt = active_batch["expiry_date"].strftime("%Y/%m/%d") if active_batch and active_batch["expiry_date"] else "—"
        
        cell_text = [
            ["", "", f"Lot {lot_no}", ""],
            ["", "Target", "T.Rec", "R.Rec"],
            ["N", "", str(t_stats["n"]), str(len(valid_values))],
            ["Accept", "", str(t_stats["accept"]), str(len(x_acc))],
            ["Reject", "", str(t_stats["reject"]), str(len(x_rej))],
            ["Range", target_str, "", ""],
            ["Exp.Dt", "", exp_dt, ""]
        ]

        return scatters, cell_text, len(valid_values)

    def _on_hover(self, event):
        if getattr(self, '_hover_info', None) is None:
            return
            
        if not event.inaxes:
            # 隱藏所有 annotations
            for info in self._hover_info:
                if info['annot'].get_visible():
                    info['annot'].set_visible(False)
            event.canvas.draw_idle()
            return

        is_hovered = False
        for info in self._hover_info:
            if event.inaxes == info['ax']:
                for sc, data_list in info['scatters']:
                    cont, ind = sc.contains(event)
                    if cont:
                        point_idx = ind["ind"][0]
                        r = data_list[point_idx]
                        
                        pos = sc.get_offsets()[point_idx]
                        info['annot'].xy = pos
                        r_dt = r.get("result_date")
                        r_dt_str = r_dt.strftime("%Y/%m/%d") if hasattr(r_dt, "strftime") else str(r_dt).split()[0]
                        dt = r.get("entered_at")
                        dt_str = dt.strftime("%m/%d %H:%M") if hasattr(dt, "strftime") else ""
                        val = r.get("measured_value")
                        if val is None: val = r.get("qualitative_result")
                        user = r.get("entered_by_name", "未知")
                        notes = r.get("notes") or "無"
                        
                        text = f"數值：{val}\n檢驗日期：{r_dt_str}\n輸入時間：{dt_str}\n操作：{user}\n備註：{notes}"
                        if r.get("has_anomaly"):
                            text += "\n★ 已填寫異常單"
                        if r.get("westgard_flag"):
                            text = f"[異常] {r['westgard_flag']}\n" + text
                            
                        # 防止提示框在邊界被截斷
                        xlim = info['ax'].get_xlim()
                        ylim = info['ax'].get_ylim()
                        
                        x_offset = -10 if pos[0] > (xlim[0] + xlim[1]) / 2 else 10
                        info['annot'].set_horizontalalignment('right' if x_offset < 0 else 'left')
                        
                        y_offset = -10 if pos[1] > (ylim[0] + ylim[1]) / 2 + (ylim[1] - ylim[0]) * 0.25 else 10
                        info['annot'].set_verticalalignment('top' if y_offset < 0 else 'bottom')
                            
                        info['annot'].xyann = (x_offset, y_offset)
                        info['annot'].set_text(text)
                        info['annot'].set_visible(True)
                        info['canvas'].draw_idle()
                        is_hovered = True
                        break
                
                # 如果滑鼠在這個圖表內，但沒有碰到點，隱藏
                if not is_hovered and info['annot'].get_visible():
                    info['annot'].set_visible(False)
                    info['canvas'].draw_idle()

    def _on_click(self, event):
        if event.button != 3: # 3 is right click
            return
            
        if getattr(self, '_hover_info', None) is None:
            return
            
        if not event.inaxes:
            return

        for info in self._hover_info:
            if event.inaxes == info['ax']:
                for sc, data_list in info['scatters']:
                    cont, ind = sc.contains(event)
                    if cont:
                        point_idx = ind["ind"][0]
                        r = data_list[point_idx]
                        
                        menu = QMenu(self)
                        action_note = menu.addAction("📝 備註")
                        anomaly_txt = "📝 檢視/修改品管異常紀錄" if r.get("has_anomaly") else "⚠️ 品管異常紀錄"
                        action_anomaly = menu.addAction(anomaly_txt)
                        
                        # Show menu at global cursor pos
                        action = menu.exec(QCursor.pos())
                        if action == action_note:
                            current_note = r.get("notes") or ""
                            text, ok = QInputDialog.getText(
                                self, "點擊備註", "請輸入備註內容：", text=current_note
                            )
                            if ok:
                                new_note = text.strip()
                                r["notes"] = new_note
                                QCResultService.update_note(r["result_id"], new_note)
                                
                                # 重繪圖表以立即顯示備註光圈
                                self._draw_chart()
                        
                        elif action == action_anomaly:
                            from ui.qc.anomaly_dialog import AnomalyRecordDialog
                            
                            # Get instrument and level names for context
                            inst_name = self.cmb_inst.currentText()
                            level_name = info['level_name']
                            
                            # Fetch lot number context from cmb_batch
                            lot_number = "未知"
                            selected_lots = self.cmb_batch.currentData()
                            if selected_lots and len(selected_lots) > 0:
                                lot_number = selected_lots[0]
                            else:
                                # try to extract from combo box text
                                txt = self.cmb_batch.currentText()
                                if " [" in txt:
                                    lot_number = txt.split(" [")[0]
                                else:
                                    lot_number = txt
                            
                            r_enriched = r.copy()
                            r_enriched["instrument_name"] = inst_name
                            r_enriched["lot_number"] = lot_number
                            
                            dialog = AnomalyRecordDialog(self, self.user, r_enriched, level_name)
                            dialog.exec()
                                    
                        return # Only handle the first found point

    def _clear_chart(self):
        while self.charts_layout.count():
            item = self.charts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _load_batches(self):
        self.cmb_batch.blockSignals(True)
        self.cmb_batch.clear()
        
        from services.qc_service import QCBatchService
        batches = QCBatchService.get_all()
        
        groups = {}
        for b in batches:
            key = (b["open_date"], b["expiry_date"])
            if key not in groups:
                groups[key] = []
            groups[key].append(b)
            
        active_index = -1
        archived_count = 0
        
        for idx, ((od, ed), group_batches) in enumerate(groups.items()):
            lots = sorted(list(set(b["lot_number"] for b in group_batches)))
            is_active = any(b.get("is_active") for b in group_batches)
            is_archived = any(b.get("is_archived") for b in group_batches)
            
            label = f"{'/'.join(lots)}"
            if is_active:
                label += " [使用中]"
                active_index = self.cmb_batch.count()
            elif is_archived:
                if archived_count > 0:
                    continue
                label += " [已退役]"
                archived_count += 1
            else:
                label += " [待允收]"
                
            self.cmb_batch.addItem(label, lots)
                
        if active_index >= 0 and self.cmb_batch.count() > 0:
            self.cmb_batch.setCurrentIndex(active_index)
            
        self.cmb_batch.blockSignals(False)

    def on_page_show(self):
        self._load_batches()
        self._draw_chart(reset_scroll=True)
