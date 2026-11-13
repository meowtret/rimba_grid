# -*- coding: utf-8 -*-
"""Dialog Rimba Grid."""

from qgis.core import QgsProject, QgsSettings
from qgis.gui import QgsColorButton
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox,
    QFontComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QSpinBox, QVBoxLayout, QWidget,
)

from . import grid_core as core

NEW_GRID = "__new__"
SKEY = "rimba_grid/"


class DmsInput(QWidget):
    """Input interval derajat-menit-detik."""

    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.d = QSpinBox()
        self.d.setRange(0, 90)
        self.d.setSuffix(" °")
        self.m = QSpinBox()
        self.m.setRange(0, 59)
        self.m.setSuffix(" '")
        self.s = QDoubleSpinBox()
        self.s.setRange(0, 59.999)
        self.s.setDecimals(1)
        self.s.setSuffix(' "')
        for w in (self.d, self.m, self.s):
            lay.addWidget(w)

    def value(self):
        return core.dms_to_deg(self.d.value(), self.m.value(), self.s.value())

    def setValue(self, deg):
        d, m, s = core.deg_to_dms(deg)
        self.d.setValue(d)
        self.m.setValue(m)
        self.s.setValue(s)


class RimbaGridDialog(QDialog):

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        self.iface = iface
        self.setWindowTitle("Rimba Grid — Grid BT/BB · LU/LS")
        self.setMinimumWidth(460)
        self._build_ui()
        self._load_settings()
        self.reload_layouts()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        main = QVBoxLayout(self)

        # --- Target
        g_target = QGroupBox("Target")
        f = QFormLayout(g_target)
        self.cb_layout = QComboBox()
        btn_reload = QPushButton("↻")
        btn_reload.setFixedWidth(30)
        btn_reload.setToolTip("Muat ulang daftar layout")
        btn_reload.clicked.connect(self.reload_layouts)
        row = QHBoxLayout()
        row.addWidget(self.cb_layout, 1)
        row.addWidget(btn_reload)
        f.addRow("Layout", row)
        self.cb_map = QComboBox()
        f.addRow("Item peta", self.cb_map)
        self.cb_grid = QComboBox()
        f.addRow("Grid", self.cb_grid)
        self.chk_label_only = QCheckBox(
            "Hanya ganti label (gaya grid lama tetap)")
        f.addRow("", self.chk_label_only)
        main.addWidget(g_target)

        # --- Interval
        self.g_interval = QGroupBox("Interval grid (derajat-menit-detik)")
        f = QFormLayout(self.g_interval)
        self.iv_x = DmsInput()
        self.iv_y = DmsInput()
        f.addRow("Bujur (X)", self.iv_x)
        f.addRow("Lintang (Y)", self.iv_y)
        btn_auto = QPushButton("Hitung otomatis dari luas peta")
        btn_auto.clicked.connect(self.auto_interval)
        f.addRow("", btn_auto)
        main.addWidget(self.g_interval)

        # --- Label
        g_label = QGroupBox("Format label")
        f = QFormLayout(g_label)
        self.cb_fmt = QComboBox()
        self.cb_fmt.addItem(
            "Derajat-menit-detik (122°56'00\" BT)", core.FMT_DMS)
        self.cb_fmt.addItem("Derajat-menit (122°56' BT)", core.FMT_DM)
        self.cb_fmt.addItem("Derajat desimal (122,93° BT)", core.FMT_DD)
        f.addRow("Format", self.cb_fmt)
        self.sp_dec = QSpinBox()
        self.sp_dec.setRange(0, 4)
        f.addRow("Desimal", self.sp_dec)
        self.cb_sep = QComboBox()
        self.cb_sep.addItem("Koma ( , )", ",")
        self.cb_sep.addItem("Titik ( . )", ".")
        f.addRow("Pemisah desimal", self.cb_sep)
        self.chk_pad = QCheckBox("Menit/detik dua digit (00)")
        self.chk_space = QCheckBox("Spasi sebelum BT/LS")
        f.addRow("", self.chk_pad)
        f.addRow("", self.chk_space)
        self.lbl_preview = QLabel()
        self.lbl_preview.setStyleSheet("font-weight:bold;")
        f.addRow("Contoh", self.lbl_preview)
        main.addWidget(g_label)

        # --- Tampilan
        self.g_style = QGroupBox("Tampilan")
        f = QFormLayout(self.g_style)
        self.cb_style = QComboBox()
        self.cb_style.addItem("Garis penuh", "lines")
        self.cb_style.addItem("Tanda silang (+)", "cross")
        self.cb_style.addItem("Hanya bingkai & label", "frame")
        f.addRow("Gaya grid", self.cb_style)
        lc = QHBoxLayout()
        self.btn_line_color = QgsColorButton()
        self.btn_line_color.setColor(QColor("#000000"))
        self.sp_line_w = QDoubleSpinBox()
        self.sp_line_w.setRange(0.05, 2.0)
        self.sp_line_w.setSingleStep(0.05)
        self.sp_line_w.setSuffix(" mm")
        lc.addWidget(self.btn_line_color)
        lc.addWidget(self.sp_line_w)
        f.addRow("Warna / tebal garis", lc)
        self.cb_frame = QComboBox()
        self.cb_frame.addItem("Zebra", "zebra")
        self.cb_frame.addItem("Zebra nautikal", "zebra_nautical")
        self.cb_frame.addItem("Garis tepi", "line")
        self.cb_frame.addItem("Tick ke dalam", "ticks_in")
        self.cb_frame.addItem("Tick ke luar", "ticks_out")
        self.cb_frame.addItem("Tanpa bingkai", "none")
        f.addRow("Bingkai", self.cb_frame)
        self.sp_frame_w = QDoubleSpinBox()
        self.sp_frame_w.setRange(0.2, 10)
        self.sp_frame_w.setSingleStep(0.1)
        self.sp_frame_w.setSuffix(" mm")
        f.addRow("Lebar bingkai", self.sp_frame_w)
        fr = QHBoxLayout()
        self.cb_font = QFontComboBox()
        self.sp_font = QDoubleSpinBox()
        self.sp_font.setRange(3, 30)
        self.sp_font.setSingleStep(0.5)
        self.sp_font.setSuffix(" pt")
        self.btn_font_color = QgsColorButton()
        self.btn_font_color.setColor(QColor("#000000"))
        self.btn_font_color.setMinimumWidth(40)
        fr.addWidget(self.cb_font, 1)
        fr.addWidget(self.sp_font)
        fr.addWidget(self.btn_font_color)
        f.addRow("Huruf", fr)
        self.cb_side = QComboBox()
        self.cb_side.addItem("Kiri/kanan vertikal", True)
        self.cb_side.addItem("Semua horizontal", False)
        f.addRow("Arah label LU/LS", self.cb_side)
        self.cb_pos = QComboBox()
        self.cb_pos.addItem("Di luar bingkai peta", False)
        self.cb_pos.addItem("Di dalam bingkai peta", True)
        f.addRow("Posisi label", self.cb_pos)
        self.sp_dist = QDoubleSpinBox()
        self.sp_dist.setRange(0, 20)
        self.sp_dist.setSingleStep(0.5)
        self.sp_dist.setSuffix(" mm")
        f.addRow("Jarak label", self.sp_dist)
        main.addWidget(self.g_style)

        bb = QDialogButtonBox()
        self.btn_apply = bb.addButton("Terapkan", QDialogButtonBox.ApplyRole)
        bb.addButton("Tutup", QDialogButtonBox.RejectRole)
        self.btn_apply.clicked.connect(self.apply)
        bb.rejected.connect(self.reject)
        main.addWidget(bb)

        # sinyal
        self.cb_layout.currentIndexChanged.connect(self.reload_maps)
        self.cb_map.currentIndexChanged.connect(self.reload_grids)
        self.cb_grid.currentIndexChanged.connect(self._update_enabled)
        self.chk_label_only.toggled.connect(self._update_enabled)
        for w in (self.cb_fmt, self.cb_sep):
            w.currentIndexChanged.connect(self.update_preview)
        self.sp_dec.valueChanged.connect(self.update_preview)
        self.chk_pad.toggled.connect(self.update_preview)
        self.chk_space.toggled.connect(self.update_preview)

    # ------------------------------------------------------------ settings
    def _load_settings(self):
        s = QgsSettings()
        g = lambda k, d, t=str: s.value(SKEY + k, d, type=t)  # noqa: E731
        self.iv_x.setValue(g("iv_x", 1 / 60, float))
        self.iv_y.setValue(g("iv_y", 1 / 60, float))
        self._set_combo(self.cb_fmt, g("fmt", core.FMT_DMS))
        self.sp_dec.setValue(g("dec", 0, int))
        self._set_combo(self.cb_sep, g("sep", ","))
        self.chk_pad.setChecked(g("pad", True, bool))
        self.chk_space.setChecked(g("space", True, bool))
        self._set_combo(self.cb_style, g("style", "lines"))
        self.btn_line_color.setColor(QColor(g("line_color", "#000000")))
        self.sp_line_w.setValue(g("line_w", 0.15, float))
        self._set_combo(self.cb_frame, g("frame", "zebra"))
        self.sp_frame_w.setValue(g("frame_w", 1.5, float))
        self.cb_font.setCurrentFont(QFont(g("font", "Arial")))
        self.sp_font.setValue(g("font_size", 7.0, float))
        self.btn_font_color.setColor(QColor(g("font_color", "#000000")))
        self._set_combo(self.cb_side, g("vertical", True, bool))
        self._set_combo(self.cb_pos, g("inside", False, bool))
        self.sp_dist.setValue(g("dist", 1.0, float))
        self.update_preview()

    def _save_settings(self):
        s = QgsSettings()
        vals = {
            "iv_x": self.iv_x.value(), "iv_y": self.iv_y.value(),
            "fmt": self.cb_fmt.currentData(), "dec": self.sp_dec.value(),
            "sep": self.cb_sep.currentData(), "pad": self.chk_pad.isChecked(),
            "space": self.chk_space.isChecked(),
            "style": self.cb_style.currentData(),
            "line_color": self.btn_line_color.color().name(),
            "line_w": self.sp_line_w.value(),
            "frame": self.cb_frame.currentData(),
            "frame_w": self.sp_frame_w.value(),
            "font": self.cb_font.currentFont().family(),
            "font_size": self.sp_font.value(),
            "font_color": self.btn_font_color.color().name(),
            "vertical": self.cb_side.currentData(),
            "inside": self.cb_pos.currentData(),
            "dist": self.sp_dist.value(),
        }
        for k, v in vals.items():
            s.setValue(SKEY + k, v)

    @staticmethod
    def _set_combo(cb, data):
        i = cb.findData(data)
        if i >= 0:
            cb.setCurrentIndex(i)

    # --------------------------------------------------------------- data
    def reload_layouts(self):
        current = self.cb_layout.currentText()
        self.cb_layout.blockSignals(True)
        self.cb_layout.clear()
        for lay in QgsProject.instance().layoutManager().printLayouts():
            self.cb_layout.addItem(lay.name())
        i = self.cb_layout.findText(current)
        if i >= 0:
            self.cb_layout.setCurrentIndex(i)
        self.cb_layout.blockSignals(False)
        self.reload_maps()

    def current_layout(self):
        name = self.cb_layout.currentText()
        if not name:
            return None
        return QgsProject.instance().layoutManager().layoutByName(name)

    def reload_maps(self):
        self.cb_map.blockSignals(True)
        self.cb_map.clear()
        layout = self.current_layout()
        if layout:
            for m in core.map_items(layout):
                self.cb_map.addItem(m.displayName(), m.uuid())
        self.cb_map.blockSignals(False)
        self.reload_grids()

    def current_map(self):
        layout = self.current_layout()
        uid = self.cb_map.currentData()
        if not layout or not uid:
            return None
        return layout.itemByUuid(uid)

    def reload_grids(self):
        self.cb_grid.blockSignals(True)
        self.cb_grid.clear()
        self.cb_grid.addItem("➕ Buat grid baru", NEW_GRID)
        m = self.current_map()
        if m:
            for g in m.grids().asList():
                crs = core.grid_crs(g, m)
                tag = ("" if crs.isGeographic()
                       else "  [proyeksi — tidak cocok]")
                self.cb_grid.addItem("✎ " + g.name() + tag, g.id())
        self.cb_grid.blockSignals(False)
        self._update_enabled()

    def current_grid(self):
        m = self.current_map()
        gid = self.cb_grid.currentData()
        if not m or gid in (None, NEW_GRID):
            return None
        return m.grids().grid(gid)

    def _update_enabled(self):
        existing = self.cb_grid.currentData() not in (None, NEW_GRID)
        self.chk_label_only.setEnabled(existing)
        label_only = existing and self.chk_label_only.isChecked()
        self.g_interval.setEnabled(not label_only)
        self.g_style.setEnabled(not label_only)

    # ------------------------------------------------------------ actions
    def label_options(self):
        return dict(
            fmt=self.cb_fmt.currentData(), decimals=self.sp_dec.value(),
            pad=self.chk_pad.isChecked(), dec_sep=self.cb_sep.currentData(),
            space=self.chk_space.isChecked())

    def update_preview(self):
        o = self.label_options()
        lon = core.format_label_py(122 + 56 / 60, "x", **o)
        lat = core.format_label_py(-(42 / 60), "y", **o)
        self.lbl_preview.setText("{}   ·   {}".format(lon, lat))

    def auto_interval(self):
        m = self.current_map()
        if not m:
            QMessageBox.information(self, "Rimba Grid",
                                    "Pilih layout dan item peta dulu.")
            return
        ext = core.map_extent_wgs84(m)
        self.iv_x.setValue(core.auto_interval(ext.width()))
        self.iv_y.setValue(core.auto_interval(ext.height()))

    def apply(self):
        m = self.current_map()
        if not m:
            QMessageBox.warning(self, "Rimba Grid",
                                "Belum ada layout/item peta yang dipilih.")
            return
        expr = core.build_label_expression(**self.label_options())
        grid = self.current_grid()
        label_only = grid is not None and self.chk_label_only.isChecked()

        if grid is not None and not core.grid_crs(grid, m).isGeographic():
            if label_only:
                QMessageBox.warning(
                    self, "Rimba Grid",
                    "Grid '{}' memakai CRS proyeksi (mis. UTM). Label BT/LS "
                    "hanya berlaku untuk grid geografis.\n\nHilangkan centang "
                    "'Hanya ganti format label' agar grid diubah ke "
                    "EPSG:4326.".format(grid.name()))
                return

        if not label_only:
            ivx, ivy = self.iv_x.value(), self.iv_y.value()
            if ivx <= 0 or ivy <= 0:
                QMessageBox.warning(self, "Rimba Grid",
                                    "Interval tidak boleh nol.")
                return
            ext = core.map_extent_wgs84(m)
            n = (ext.width() / ivx) * (ext.height() / ivy)
            if n > 2500:
                QMessageBox.warning(
                    self, "Rimba Grid",
                    "Interval terlalu rapat untuk luas peta ini (±{:.0f} "
                    "sel). Perbesar interval atau klik 'Hitung otomatis'."
                    .format(n))
                return

        layout = m.layout()
        layout.undoStack().beginMacro("Rimba Grid")
        try:
            if grid is None:
                from qgis.core import QgsLayoutItemMapGrid
                grid = QgsLayoutItemMapGrid(core.GRID_NAME_DEFAULT, m)
                m.grids().addGrid(grid)
            if label_only:
                core.apply_label_format(grid, expr)
            else:
                core.configure_grid(grid, self.grid_options(expr))
            core.refresh_map(m)
        finally:
            layout.undoStack().endMacro()

        self._save_settings()
        gid = grid.id()
        self.reload_grids()
        self._set_combo(self.cb_grid, gid)
        self.iface.messageBar().pushSuccess(
            "Rimba Grid", "Grid '{}' pada '{}' diperbarui.".format(
                grid.name(), m.displayName()))

    def grid_options(self, expr):
        return dict(
            interval_x=self.iv_x.value(), interval_y=self.iv_y.value(),
            style=self.cb_style.currentData(),
            line_color=self.btn_line_color.color().name(),
            line_width=self.sp_line_w.value(),
            frame=self.cb_frame.currentData(),
            frame_width=self.sp_frame_w.value(),
            font_family=self.cb_font.currentFont().family(),
            font_size=self.sp_font.value(),
            font_color=self.btn_font_color.color().name(),
            side_vertical=self.cb_side.currentData(),
            annot_inside=self.cb_pos.currentData(),
            annot_distance=self.sp_dist.value(),
            expression=expr,
        )
