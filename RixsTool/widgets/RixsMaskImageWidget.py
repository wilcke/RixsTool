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
__author__ = "Tonn Rueter - ESRF Data Analysis Unit"

#
# Import tool windows
#
from ..UiPaths import UiPaths
from RixsTool.widgets.ToolWindows import FlipWidget, BandPassFilterWindow, \
    BandPassID32Window, ImageAlignmentWindow, SumImageTool, EnergyScaleTool

#
# Imports from PyMca
# PyMcaQt: qt version of pymca
# MaskImageWidget: Base class for image visualization
#
from PyMca5.PyMcaGui import PyMcaQt as qt
from PyMca5.PyMca import MaskImageWidget
#
# TODO: platform is import for dev purposes, remove me
#
import platform

DEBUG = 0
PLATFORM = platform.system()

class RixsMaskImageWidget(MaskImageWidget.MaskImageWidget):

    __doc__ = """Image visualization derived from :py:class:`MaskImageWidget`.
    Features several tool windows based on
    py:class:`RixsTool.widgets.ToolWindows.AbstractToolWindow` to manipulate the
    data while still being able to use the general image visualization operation
    provided by the MaskImageWidget class (color mapping, data selection)

    **TODO:**
        * Get tool windows in left dock widget area to align in the top area of
        the dock widget area evenly"""

    def __init__(self, parent=None):
        MaskImageWidget.MaskImageWidget.__init__(
            self,
            parent=parent,
            rgbwidget=None,
            selection=True,
            colormap=True,  # Shows ColorMapDialog
            imageicons=True,
            standalonesave=False,  # No save for image..
            usetab=False,  # Inserts MaskImageWidget into a new QTabWidget
            profileselection=True,
            scanwindow=None,
            aspect=True,
            polygon=False
        )

        self.dockWidgetArea = self.graphWidget.graph.dockWidgetArea

        #
        # Data handling: only one image at a time is shown
        #
        self.currentImageItem = None

        #
        # ATTRIBUTES CONCERNING DATA MANIPULATION
        #

        # ORDER: Operations must happen in fixed order
        # self.toolList = [
        #    self.flipWidget,
        #    self.filterWidget,
        #    self.imageAlignmentWindow
        # ]
        self.toolList = 3 * [None]

        # FLIPPING
        self.flipWidget = FlipWidget()
        self.flipWidget.valuesChangedSignal.connect(
            self.toolWindowValuesChanged)
        self.showFlipWidget()
        self.toolList[0] = self.flipWidget

        # FILTER: General preprocessing
        self.filterDict = {
            'bandpass': BandPassFilterWindow(),
            'bandpassID32': BandPassID32Window()
        }
        self.filterWidget = None
        # self.toolList[1] is set to "bandpass" in setCurrentFilter()
        self.setCurrentFilter('bandpass')

        # ALIGNMENT: Shift image along columns
        self.imageAlignmentWindow = ImageAlignmentWindow()
        self.imageAlignmentWindow.valuesChangedSignal.connect(
            self.toolWindowValuesChanged)
        self.showImageAlignmentWindow()
        self.toolList[2] = self.imageAlignmentWindow

        # INTEGRATION: Sum shifted images along an axis and export the resulting
        # spectra to the project
        self.sumImageTool = SumImageTool()
        self.showSumImageTool()

        # ENERGY SCALE: set the energy calibration values
        self.energyScaleTool = EnergyScaleTool()
        self.showEnergyScaleTool()

        #
        # Disconnect the horizontal flip button from its normal purpose
        #
        self.graphWidget.hFlipToolButton.clicked.disconnect(
            self._hFlipIconSignal)
        self.graphWidget.hFlipToolButton.clicked.connect(self.hflip)

        if DEBUG >= 1:
            print('RixsMaskImageWidget.__init__ finished')

    #
    # METHODS CONCERNING DATA MANIPULATION TOOLS
    #

    def setCurrentFilter(self, key):
        """
        :param str key: Key of the filter to be used. Currently either
        'bandpass' or 'bandpassID32'

        Adds :py:class:`RixsTool.widgets.ToolWindows.BandPassFilterWindow` or
        :py:class:`RixsTool.widgets.ToolWindows.BandPassID32Window` instance to
        the left dock widget area.

        :raises KeyError: if key not in filterDict
        """
        if self.filterWidget:
            #
            # There is an acitve filter, disconnect its actions
            #
            self.filterWidget.valuesChangedSignal.disconnect(
                self.toolWindowValuesChanged)
            dockWidgetArea = self.dockWidgetArea(self.filterWidget)
            self.filterWidget.hide()
        else:
            dockWidgetArea = qt.Qt.LeftDockWidgetArea

        currentFilter = self.filterDict[key]
        currentFilter.valuesChangedSignal.connect(self.toolWindowValuesChanged)

        #
        # Positioning
        #
        self.addDockWidget(dockWidgetArea, currentFilter)
        currentFilter.show()
        self.filterWidget = currentFilter
        self.toolList[1] = self.filterWidget

        if DEBUG >= 1:
            print('RixsMaskImageWidget.setCurrentFilter -- Filter changed: %s' %
                str(self.filterWidget))
            print('RixsMaskImageWidget.setCurrentFilter -- Tool list: %s' %
                str(self.toolList))

    def toolWindowValuesChanged(self, ddict):
        """
        :param dict ddict: Remove parameter

        Function is triggered by
        :py:func:`RixsTool.widgets.ToolWindows.AbstractToolWindow.valuesChangedSignal`.
        The dictionary parameter is not used and should be removed. The present
        function requests the tool parameter using the
        :py:func:`RixsTool.widgets.ToolWindows.AbstractToolWindow.getValues`
        function and calls the generic
        :py:func:`RixsTool.widgets.ToolWindows.AbstractToolWindow.process`
        function to obtain the result.

        To allow the image processing, the process function must be implemented
        in subclasses of
        :py:func:`RixsTool.widgets.ToolWindows.AbstractToolWindow.process` and
        has to feature a two parameter interface. The first parameter is the
        current image itself, the second is a dictionary of parameter values.

        Calculated results are displayed using the :py:func:`addImage` function.
        """

        #
        # AVOID RECALCULATION: If change occured in tool at position idx,
        # perform recalculation for self.toolList[idx:] ...
        #
        if not self.currentImageItem:
            return
        key = self.currentImageItem.key()
        imageData = self.currentImageItem.array

        for tool in self.toolList:
            if not tool.active():
                continue
            parameters = tool.getValues()
            imageData = tool.process(imageData, parameters)
        if DEBUG >= 1:
            print("RixsMaskImageWidget.toolWindowValuesChanged -- key: '%s'" %
                key)
        self.setImageData(
            data=imageData,
            clearmask=False,
            xScale=self.currentImageItem.scaleX,
            yScale=self.currentImageItem.scaleY
        )

    def hflip(self, **kw):
        __doc__ = """Flips the current image. This function is triggered by the
            re-directed horizontal flip button of the graphics window. It
            operates independently of the state of the "Flip Image" image tool.
            However, its Status label and Flip Radio Button will still change
            accordingly and therefore show the flip state of the displayed
            image."""

        if DEBUG >= 1:
            print('RixsMaskImageWidget.hflip -- called. kw: %s' % str(kw))
        flipWidget = self.toolList[0]

        #
        # Set the state of the "flipWidget" to "not active" to prevent the
        # "toolWindowValuesChanged" function to be triggered by the toggling of
        # the "flipRadioButton"
        #
        active = flipWidget.active()
        if active:
            flipWidget.setActive(False)
        flipWidget.flipRadioButton.toggle()
        parameters = flipWidget.getValues()
        imageData = self.currentImageItem.array
        imageData = flipWidget.process(imageData, parameters)

        #
        # Set the state of the "flipWidet" back to its original state.
        #
        flipWidget.setActive(active)

    def getActiveImage(self, just_legend=True):
        """
        :param bool just_legend: Determines the return type

        Reimplementation of :py:class:`PyMca.PlotWindow.getActiveImage` function
        to have it available on this level of the class hierarchy.

        Function either returns a tuple in case of just_legend=False
        containining the image data, the legend and meta data. In case of
        just_legend=True, the function returns the legend string.

        :returns tupel or string: Image data or legend string
        """
        plotWindow = self.graphWidget.graph
        legend = plotWindow.getActiveImage(just_legend=just_legend)
        if DEBUG >= 1:
            print("RixsMaskImageWidget.getActiveImage -- legend: '%s'" % legend)
        return legend

    def setImageItem(self, projectItem):
        self.currentImageItem = projectItem
        imageData = self.currentImageItem.array

        self.setImageData(
            data=imageData,
            clearmask=False,
            xScale=self.currentImageItem.scaleX,
            yScale=self.currentImageItem.scaleY
        )

        if DEBUG >= 1:
            print('RixsMaskImageWidget.setImageItem -- finished!')

    def showFlipWidget(self):
        """
        Adds :py:class:`FlipWidget` instance to the left dock widget area
        """
        self.addDockWidget(qt.Qt.LeftDockWidgetArea, self.flipWidget)

    def showImageAlignmentWindow(self):
        """
        Adds :py:class:`RixsTool.widgets.ToolWindows.ImageAlignmentWindow`
        instance to the left dock widget area
        """
        self.addDockWidget(qt.Qt.LeftDockWidgetArea, self.imageAlignmentWindow)

    def showSumImageTool(self):
        """
        Adds :py:class:`RixsTool.widgets.ToolWindows.SumImageTool` instance to
        the left dock widget area
        """
        self.addDockWidget(qt.Qt.LeftDockWidgetArea, self.sumImageTool)

    def showEnergyScaleTool(self):
        """
        Adds :py:class:`RixsTool.widgets.ToolWindows.EnergyScaleTool` instance
        to the left dock widget area
        """
        self.addDockWidget(qt.Qt.LeftDockWidgetArea, self.energyScaleTool)

    def addDockWidget(self, area, widget, orientation=qt.Qt.Vertical):
        self.graphWidget.graph.addDockWidget(area, widget, orientation)


if __name__ == '__main__':
    app = qt.QApplication([])
    win = RixsMaskImageWidget()
    win.show()
    app.exec_()
