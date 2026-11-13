# -*- coding: utf-8 -*-
"""Rimba Grid - grid koordinat layout berlabel BT/BB dan LU/LS."""

import os

from qgis.core import Qgis, QgsMessageLog

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction

MENU = "&Rimba Grid"


class RimbaGridPlugin:

    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dlg = None

    def initGui(self):  # noqa: N802
        icon = QIcon(os.path.join(os.path.dirname(__file__), "icon.png"))
        self.action = QAction(icon, "Rimba Grid (BT/BB · LU/LS)",
                              self.iface.mainWindow())
        self.action.setToolTip(
            "Buat/ubah grid layout berlabel BT/BB dan LU/LS")
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(MENU, self.action)
        # Ikon juga di toolbar Layout Designer
        self.iface.layoutDesignerOpened.connect(self._add_to_designer)

    def _add_to_designer(self, designer):
        try:
            tb = designer.actionsToolbar()
            if tb is not None:
                tb.addAction(self.action)
        except (AttributeError, RuntimeError) as err:
            QgsMessageLog.logMessage(
                "Gagal menambah ikon ke Layout Designer: {}".format(err),
                "Rimba Grid", Qgis.Warning)

    def unload(self):
        try:
            self.iface.layoutDesignerOpened.disconnect(self._add_to_designer)
        except (TypeError, RuntimeError):
            QgsMessageLog.logMessage(
                "Sinyal Layout Designer sudah terputus.", "Rimba Grid",
                Qgis.Info)
        self.iface.removePluginMenu(MENU, self.action)
        self.iface.removeToolBarIcon(self.action)
        if self.dlg:
            self.dlg.close()
            self.dlg = None

    def run(self):
        from .dialog import RimbaGridDialog
        if self.dlg is None:
            self.dlg = RimbaGridDialog(self.iface, self.iface.mainWindow())
        else:
            self.dlg.reload_layouts()
        self.dlg.show()
        self.dlg.raise_()
        self.dlg.activateWindow()
