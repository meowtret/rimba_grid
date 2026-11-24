# -*- coding: utf-8 -*-
"""
Rimba Grid - logika inti (tanpa GUI).

Membangun ekspresi label grid bergaya Indonesia (BT/BB, LU/LS) dan
menerapkannya ke grid pada item peta di Print Layout QGIS.

Label disimpan sebagai *ekspresi kustom* grid layout, jadi layout tetap
menampilkan BT/LS walaupun dibuka di QGIS yang tidak memasang plugin ini.
"""

import math

from qgis.core import (
    Qgis,
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsLayoutItemMap,
    QgsLayoutItemMapGrid,
    QgsProject,
    QgsTextFormat,
    QgsUnitTypes,
)
from qgis.PyQt.QtGui import QColor, QFont

# ---------------------------------------------------------------------------
# Ekspresi label
# ---------------------------------------------------------------------------

FMT_DMS = "dms"   # 122°56'00" BT
FMT_DM = "dm"     # 122°56' BT  /  122°56,5' BT
FMT_DD = "dd"     # 122,9333° BT

GRID_NAME_DEFAULT = "Grid BT-LS"

# Penanda di nama grid agar plugin mengenali grid buatannya
_APOS = "char(39)"   # '
_QUOT = "char(34)"   # "


def _q(text):
    """String literal ekspresi QGIS (aman untuk tanda kutip tunggal)."""
    return "'" + str(text).replace("'", "''") + "'"


def _padded_number(var, pad, decimals, dec_sep):
    """Ekspresi teks untuk angka var (>=0) dengan padding 2 digit & desimal."""
    int_part = "to_string(to_int(floor({v})))".format(v=var)
    if pad:
        int_part = "lpad({ip}, 2, '0')".format(ip=int_part)
    if decimals <= 0:
        return int_part
    frac = (
        "lpad(to_string(to_int(round(({v} - floor({v})) * {f}))), {d}, '0')"
    ).format(v=var, f=10 ** decimals, d=decimals)
    return "{ip} || {sep} || {fr}".format(
        ip=int_part, sep=_q(dec_sep), fr=frac)


def build_label_expression(fmt=FMT_DMS, decimals=0, pad=True, dec_sep=",",
                           space=True, lon_pos="BT", lon_neg="BB",
                           lat_pos="LU", lat_neg="LS", spaced=False):
    """
    Kembalikan string ekspresi QGIS untuk anotasi grid kustom.

    Variabel yang tersedia di konteks anotasi grid: @grid_number, @grid_axis.
    Nilai 0 (ekuator / meridian 0) ditulis tanpa akhiran.
    spaced=True menyisipkan spasi antar komponen: 122° 33' 0" BT.
    """
    decimals = max(0, int(decimals))
    sp = " " if space else ""
    deg_mark = _q("° " if spaced else "°")
    gap = " || ' '" if spaced else ""
    suffix = (
        "CASE WHEN @_t = 0 THEN '' "
        "WHEN @grid_axis = 'x' THEN if(@grid_number > 0, {lp}, {ln}) "
        "ELSE if(@grid_number > 0, {tp}, {tn}) END"
    ).format(lp=_q(sp + lon_pos), ln=_q(sp + lon_neg),
             tp=_q(sp + lat_pos), tn=_q(sp + lat_neg))

    deg_txt = "to_string(to_int(@_d))"

    if fmt == FMT_DMS:
        sec_txt = _padded_number("@_s", pad, decimals, dec_sep)
        min_txt = "to_string(to_int(@_m))"
        if pad:
            min_txt = "lpad({m}, 2, '0')".format(m=min_txt)
        body = (
            "{d} || {dm} || {m} || {ap}{gap} || {s} || {qu}"
        ).format(d=deg_txt, dm=deg_mark, m=min_txt, s=sec_txt, ap=_APOS,
                 qu=_QUOT, gap=gap)
        return (
            "with_variable('_t', round(abs(@grid_number) * 3600, {dec}),"
            " with_variable('_d', floor(@_t / 3600),"
            " with_variable('_m', floor((@_t - @_d * 3600) / 60),"
            " with_variable('_s', @_t - @_d * 3600 - @_m * 60,"
            " {body} || {suf}))))"
        ).format(dec=decimals, body=body, suf=suffix)

    if fmt == FMT_DM:
        min_txt = _padded_number("@_m", pad, decimals, dec_sep)
        body = "{d} || {dm} || {m} || {ap}".format(
            d=deg_txt, dm=deg_mark, m=min_txt, ap=_APOS)
        return (
            "with_variable('_t', round(abs(@grid_number) * 60, {dec}),"
            " with_variable('_d', floor(@_t / 60),"
            " with_variable('_m', @_t - @_d * 60,"
            " {body} || {suf})))"
        ).format(dec=decimals, body=body, suf=suffix)

    # Derajat desimal
    dd_txt = _padded_number("@_t", False, max(decimals, 0), dec_sep)
    return (
        "with_variable('_t', round(abs(@grid_number), {dec}),"
        " {dd} || '°' || {suf})"
    ).format(dec=decimals, dd=dd_txt, suf=suffix)


def format_label_py(value, axis, fmt=FMT_DMS, decimals=0, pad=True,
                    dec_sep=",", space=True, spaced=False):
    """Versi Python dari ekspresi di atas (untuk pratinjau di dialog)."""
    sp = " " if space else ""
    dm = "° " if spaced else "°"
    gap = " " if spaced else ""

    def round(x, dec=0):  # noqa: A001
        # pembulatan setengah ke atas, sama seperti fungsi round() QGIS
        f = 10 ** dec
        return math.floor(x * f + 0.5) / f

    def num(v, p, dec):
        ip = str(int(math.floor(v)))
        if p:
            ip = ip.zfill(2)
        if dec <= 0:
            return ip
        fr = str(int(round((v - math.floor(v)) * 10 ** dec))).zfill(dec)
        return ip + dec_sep + fr

    if fmt == FMT_DMS:
        t = round(abs(value) * 3600, decimals)
        d = math.floor(t / 3600)
        m = math.floor((t - d * 3600) / 60)
        s = t - d * 3600 - m * 60
        mm = str(int(m)).zfill(2) if pad else str(int(m))
        sec = num(s, pad, decimals)
        body = "{}{}{}'{}{}\"".format(int(d), dm, mm, gap, sec)
    elif fmt == FMT_DM:
        t = round(abs(value) * 60, decimals)
        d = math.floor(t / 60)
        m = t - d * 60
        body = "{}{}{}'".format(int(d), dm, num(m, pad, decimals))
    else:
        t = round(abs(value), decimals)
        body = "{}°".format(num(t, False, decimals))
    if t == 0:
        return body
    if axis == "x":
        return body + sp + ("BT" if value > 0 else "BB")
    return body + sp + ("LU" if value > 0 else "LS")


# ---------------------------------------------------------------------------
# Interval
# ---------------------------------------------------------------------------

# Interval "cantik" dalam derajat (1", 2", 5", ... 10°)
NICE_INTERVALS = [
    1 / 3600, 2 / 3600, 5 / 3600, 10 / 3600, 15 / 3600, 20 / 3600, 30 / 3600,
    1 / 60, 2 / 60, 5 / 60, 10 / 60, 15 / 60, 20 / 60, 30 / 60,
    1, 2, 5, 10, 15, 20, 30,
]


def dms_to_deg(d, m, s):
    return float(d) + float(m) / 60.0 + float(s) / 3600.0


def deg_to_dms(value):
    t = round(value * 3600, 3)
    d = int(t // 3600)
    m = int((t - d * 3600) // 60)
    s = round(t - d * 3600 - m * 60, 3)
    return d, m, s


def map_extent_wgs84(map_item):
    """Extent item peta dalam EPSG:4326."""
    src = map_item.crs()
    dst = QgsCoordinateReferenceSystem("EPSG:4326")
    ext = map_item.extent()
    if src.isValid() and src != dst:
        tr = QgsCoordinateTransform(src, dst, QgsProject.instance())
        ext = tr.transformBoundingBox(ext)
    return ext


def auto_interval(span_deg, target=3):
    """Pilih interval cantik yang menghasilkan sekitar `target` garis."""
    if span_deg <= 0:
        return 1 / 60
    best = NICE_INTERVALS[0]
    for iv in NICE_INTERVALS:
        if span_deg / iv >= target:
            best = iv
        else:
            break
    return best


# ---------------------------------------------------------------------------
# Penerapan ke layout
# ---------------------------------------------------------------------------

# Enum dengan nama kelompok lengkap (wajib untuk Qt6 / QGIS 4,
# tetap berlaku di QGIS 3)
_G = QgsLayoutItemMapGrid
GridUnit = _G.GridUnit
GridStyle = _G.GridStyle
FrameStyle = _G.FrameStyle
AnnFmt = _G.AnnotationFormat
AnnPos = _G.AnnotationPosition
AnnDir = _G.AnnotationDirection
Side = _G.BorderSide
Display = _G.DisplayMode


def _points_unit():
    try:
        return Qgis.RenderUnit.Points
    except AttributeError:  # QGIS < 3.30
        return QgsUnitTypes.RenderUnit.RenderPoints


def make_text_format(family="Arial", size=7.0, color="#000000", bold=False):
    fmt = QgsTextFormat()
    font = QFont(family)
    font.setBold(bold)
    fmt.setFont(font)
    fmt.setSize(size)
    fmt.setSizeUnit(_points_unit())
    fmt.setColor(QColor(color))
    return fmt


def grid_crs(grid, map_item):
    crs = grid.crs()
    if not crs.isValid():
        crs = map_item.crs()
    return crs


def apply_label_format(grid, expression):
    """Hanya ganti format label grid menjadi BT/BB LU/LS."""
    grid.setAnnotationEnabled(True)
    grid.setAnnotationFormat(AnnFmt.CustomFormat)
    grid.setAnnotationExpression(expression)


def configure_grid(grid, opts):
    """
    Atur grid lengkap sesuai opsi dari dialog.

    opts: dict berisi kunci
      interval_x, interval_y (derajat), style, frame, frame_width,
      line_color, line_width, font_family, font_size, font_color, font_bold,
      side_vertical (bool), annot_inside (bool), annot_distance, expression
    """
    grid.setEnabled(True)
    grid.setCrs(QgsCoordinateReferenceSystem("EPSG:4326"))
    grid.setUnits(GridUnit.MapUnit)
    grid.setIntervalX(opts["interval_x"])
    grid.setIntervalY(opts["interval_y"])
    grid.setOffsetX(0)
    grid.setOffsetY(0)

    style = {
        "lines": GridStyle.Solid,
        "cross": GridStyle.Cross,
        "frame": GridStyle.FrameAnnotationsOnly,
    }[opts.get("style", "lines")]
    grid.setStyle(style)
    if opts.get("style") == "cross":
        grid.setCrossLength(opts.get("cross_length", 2.0))

    sym = grid.lineSymbol()
    if sym is not None:
        sym = sym.clone()
        sym.setColor(QColor(opts.get("line_color", "#000000")))
        sym.setWidth(opts.get("line_width", 0.15))
        grid.setLineSymbol(sym)

    frame = {
        "zebra": FrameStyle.Zebra,
        "zebra_nautical": FrameStyle.ZebraNautical,
        "line": FrameStyle.LineBorder,
        "ticks_in": FrameStyle.InteriorTicks,
        "ticks_out": FrameStyle.ExteriorTicks,
        "none": FrameStyle.NoFrame,
    }[opts.get("frame", "zebra")]
    grid.setFrameStyle(frame)
    grid.setFrameWidth(opts.get("frame_width", 1.5))
    grid.setFramePenSize(opts.get("frame_pen", 0.2))
    grid.setFramePenColor(QColor("#000000"))
    if frame in (FrameStyle.Zebra, FrameStyle.ZebraNautical):
        grid.setFrameFillColor1(QColor("#ffffff"))
        grid.setFrameFillColor2(QColor("#000000"))

    # Anotasi
    grid.setAnnotationEnabled(True)
    grid.setAnnotationFormat(AnnFmt.CustomFormat)
    grid.setAnnotationExpression(opts["expression"])
    grid.setAnnotationTextFormat(make_text_format(
        opts.get("font_family", "Arial"), opts.get("font_size", 7.0),
        opts.get("font_color", "#000000"), opts.get("font_bold", False)))
    grid.setAnnotationFrameDistance(opts.get("annot_distance", 1.0))
    grid.setAnnotationPrecision(0)

    if opts.get("annot_inside"):
        pos = AnnPos.InsideMapFrame
    else:
        pos = AnnPos.OutsideMapFrame
    vertical = opts.get("side_vertical", True)
    horiz = AnnDir.Horizontal
    sides = {
        Side.Left: (Display.LatitudeOnly,
                    AnnDir.Vertical if vertical else horiz),
        Side.Right: (Display.LatitudeOnly,
                     AnnDir.VerticalDescending if vertical else horiz),
        Side.Top: (Display.LongitudeOnly, horiz),
        Side.Bottom: (Display.LongitudeOnly, horiz),
    }
    for side, (display, direction) in sides.items():
        grid.setAnnotationDisplay(display, side)
        grid.setAnnotationPosition(pos, side)
        grid.setAnnotationDirection(direction, side)
        grid.setFrameDivisions(display, side)


def refresh_map(map_item):
    map_item.updateBoundingRect()
    map_item.update()
    map_item.refresh()
    layout = map_item.layout()
    if layout is not None:
        layout.refresh()


def map_items(layout):
    return [i for i in layout.items() if isinstance(i, QgsLayoutItemMap)]
