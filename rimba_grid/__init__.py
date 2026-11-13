# -*- coding: utf-8 -*-


def classFactory(iface):  # noqa: N802
    from .rimba_grid import RimbaGridPlugin
    return RimbaGridPlugin(iface)
