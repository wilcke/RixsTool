#/*##########################################################################
# Copyright (C) 2014 European Synchrotron Radiation Facility
#
# This file is part of the PyMca X-ray Fluorescence Toolkit developed at
# the ESRF by the Software group.
#
# This toolkit is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
# PyMca is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# PyMca; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# PyMca follows the dual licensing model of Riverbank's PyQt and cannot be
# used as a free plugin for a non-free program.
#
# Please contact the ESRF industrial unit (industry@esrf.fr) if this license
# is a problem for you.
#############################################################################*/
__author__ = "V.A. Sole - ESRF Data Analysis Unit"

#
# Import tool windows
#
from PyMca5.PyMca import PlotWindow

class RixsPlotWindow(PlotWindow.PlotWindow):
    __doc__ = """Simple wrapper to initialize PlotWindow arguments"""
    def __init__(self, parent=None, backend=None, plugins=False, newplot=False,
        control=True, position=True, **kw):
        super(RixsPlotWindow, self).__init__(parent=parent, backend=backend,
            plugins=plugins, newplot=newplot, control=control,
            position=position, **kw)
