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
# IMPORTS FOR GUI
#
from PyQt4 import uic
from ..UiPaths import UiPaths

from PyMca5.PyMca import PyMcaQt as qt


#
# IMPORTS FROM RIXSTOOL
#   unique: In place removal of redundant elements in a sequence
#   FileContextMenu: Custom context menus for DirTree
#   AddFilesAction: Custom action in context menu
#   QDirListModel: Simple list model to manage directories
#
from ..Utils import unique as RixsUtilsUnique
from .ContextMenu import FileContextMenu, AddFilesAction
from .Models import QDirListModel

#
# IMPORTS FROM OS: General file system browsing
#
from os import listdir as OsListDir
from os.path import isdir as OsPathIsDir
from os.path import isfile as OsPathIsFile
from os.path import join as OsPathJoin

#
# DEVELOPMENT IMPORT
#
import platform

DEBUG = 0
PLATFORM = platform.system()


class DirTree(qt.QTreeView):
    filesChangedSignal = qt.pyqtSignal(object)

    def __init__(self, parent):
        qt.QTreeView.__init__(self, parent)

        #
        # Model is qt.QFileSystemModel()
        #
        fsModel = qt.QFileSystemModel()
        self.setModel(fsModel)

        #
        # Set width of the columns in the File System Browser
        #
        self.setColumnWidth(0,250)
        self.setColumnWidth(1,100)
        self.setColumnWidth(2,100)
        #self.setColumnWidth(3,150)

        #
        # Set up monitor for the file system
        #
        self.watcher = qt.QFileSystemWatcher()
        self.watcher.directoryChanged.connect(self.handleDirectoryChangedSignal)

        #
        # Context menu
        #
        self.setContextMenuPolicy(qt.Qt.DefaultContextMenu)
        if hasattr(parent, 'handleContextMenuAction'):
            self.callback = parent.handleContextMenuAction
        else:
            self.callback = None

        #
        # List to keep track of files and avoid unnecessary actions
        #
        self.fileList = []

    def handleDirectoryChangedSignal(self, path):
        """
        Emits filesChangedSignal with list of fully qualified file paths (i.e.
        path + file name).

        :param str path: Path to directory in which a file was added, deleted or
            renamed
        """
        path = str(path)
        tmpFileList = filter(OsPathIsFile, [OsPathJoin(path, directory) 
            for directory in OsListDir(path)])

        #
        # Check for the difference between the current content of path and the
        # previous one
        #
        newFiles = [fileName for fileName in tmpFileList 
            if fileName not in self.fileList]
        if DEBUG >= 1:
            print("DirTree.handleDirectoryChangedSignal -- path: '%s' " \
                "(Files added: %d)" % (str(path), len(newFiles)))
            for fileName in newFiles:
                print('\t%s' % str(fileName))
        #
        # Add new files to self.fileList and emit signal if content of
        # self.fileList has changed.
        #
        if len(newFiles) > 0:
            self.fileList += newFiles
            self.filesChangedSignal.emit(newFiles)
        #
        # Remove deleted or renamed files from self.fileList
        #
        actFiles = [fileName for fileName in tmpFileList 
            if fileName in self.fileList]
        if len(actFiles) < len(self.fileList):
            self.fileList = actFiles

    def setRootDirectory(self, path):
        """
        Sets the models root directory. Removes all directories from the views

        :param str path: Root directory
        :py:class:`QFileSystemWatcher`
        """
        #
        # Set model to new root path
        #
        fsModel = self.model()
        fsModel.setRootPath(path)
        newRoot = fsModel.index(path)
        self.setRootIndex(newRoot)

        #
        # Remove all directories monitered by the watcher
        #
        watcherDirs = self.watcher.directories()
        if len(watcherDirs) > 0:
            self.watcher.removePaths(watcherDirs)

    def setWorkingDirectory(self, path):
        """
        Sets a working directory in the :py:class:`DirTree`. The working
        directory differs from the roots directory in that the views
        :py:class:`QFileSystemWatcher` monitors the directory and the immediate
        subdirectories for changes.

        **Note from the Qt-Manual:**
        For every monitored directory, system resources are consumend.

        :param str path: Working directory
        """
        self.setRootDirectory(path)

        #
        # Look for subdirectories in path and let them be monitored. Update
        # self.fileList
        #
        lsDir = [OsPathJoin(path, item) for item in OsListDir(path)]
        directoryList = [path] + filter(OsPathIsDir, lsDir)
        self.watcher.addPaths(directoryList)

        #
        # Keep track of files in the directory
        #
        self.fileList = []
        for directory in directoryList:
            lsSubDir = [OsPathJoin(directory, item) for item in
                OsListDir(directory)]
            self.fileList += filter(OsPathIsFile, lsSubDir)

        if DEBUG >= 1:
            print('DirTree.setWorkingDirectory -- watcherDirs (%d):' %
                len(self.watcher.directories()))
            for directory in self.watcher.directories():
                print("\t'%s'" % str(directory))
            print('DirTree.setWorkingDirectory -- self.fileList (%d):' %
                len(self.fileList))
            for filename in self.fileList:
                print("\t'%s'" % str(filename))

    def contextMenuEvent(self, event):
        """
        Shows a custom context menu of type

        :param QContextMenuEvent event: Request for context menu
        :py:class:`RixsTool.widgets.ContextMenu.FileContextMenu`.
        """
        modelIndexList = self.selectedIndexes()
        RixsUtilsUnique(modelIndexList, "row")
        # modelIndexList = [self.indexAt(event.pos())]

        model = self.model()
        fileInfoList = [model.fileInfo(idx) for idx in modelIndexList]

        if all([elem.isFile() for elem in fileInfoList]):
            menu = FileContextMenu(self)
            if DEBUG >= 1:
                print('DirTree.contextMenuEvent -- All files!')
        else:
            if DEBUG >= 1:
                print('DirTree.contextMenuEvent -- Not all files!')
            return
        menu.build()
        action = menu.exec_(event.globalPos())

        if action:
            if self.callback:
                self.callback(action, {'fileInfoList': fileInfoList})
            else:
                raise AttributeError(
                    "DirTree.contextMenuEvent -- callback not set")
        return

    def setModel(self, fsModel):
        """
        Reimplements :py:function:`qt.QTreeView.setModel` to ensure the usage of
        a :py:class:`qt.QFileSystemModel`.

        :param QFileSystemModel fsModel: Model to be visualized by the view
        :raises ValueError: if model is not of type QFileSystemModel
        """
        if not isinstance(fsModel, qt.QFileSystemModel):
            raise ValueError("DirTree.setModel -- provided model must be " \
                "of type QFileSystemModel")
        else:
            qt.QTreeView.setModel(self, fsModel)


class FileSystemBrowser(qt.QWidget):
    __doc__ = """Widget contains a view to browse a file system, a custom
    context menu to perform actions on selected files. Working directory
    functionality is offered to switch between folders in the file system. All
    changes in the working directory and the next level of subdirectories is
    monitored by a QFileSystemMonitor.

    **Signals**
        * addSignal: Emits a qt.QFileInfoList
    """
    addSignal = qt.pyqtSignal(object)

    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)
        uiFilePath = UiPaths.fileSystemBrowserUiPath()
        uic.loadUi(uiFilePath, self)

        #
        # Set start directory to qt.QDir.current()
        #
        workingDirModel = QDirListModel(self)
        self.workingDirCB.setModel(workingDirModel)

        #
        # Init addDir- and closeDirButtons
        #
        self.closeDirButton.setEnabled(False)

        #
        # Connect
        #
        self.fsView.filesChangedSignal.connect(self.handleFilesChanged)
        self.workingDirCB.currentIndexChanged.connect(
            self.handleWorkingDirectoryChanged)

        self.addDirButton.clicked[()].connect(self.addDir)
        self.closeDirButton.clicked[()].connect(self.closeDir)

        startDir = qt.QDir.current()
        self.addDir(startDir.absolutePath())

    #
    # Handler functions for various user interaction:
    #   fileChangedSignal
    #   directoryChanged
    #   currentIndexChanged
    #

    def handleFilesChanged(self, fileList):
        """
        Emits addSignal with the a :py:class:`qt.QFileInfoList` as parameter

        :param list fileList: Contains file paths to modified files
        """
        #
        # Check if files shall be automatically added to the project
        #
        if self.autoAddCheckBox.checkState() == qt.Qt.Unchecked:
            if DEBUG >= 1:
                print('FileSystemBrowser.handleFilesChanged -- AutoAdd off')
            return

        #
        # Create a file info list
        #
        if DEBUG >= 1:
            print('FileSystemBrowser.handleFilesChanged -- \n\tfileList: %s' %
                str(fileList))
        fileInfoList = [qt.QFileInfo(path) for path in fileList]
        self.addSignal.emit(fileInfoList)

    def handleWorkingDirectoryChanged(self, **kw):
        """
        Reset the DirTree to the directory actually displayed, or to the user's
        current directory if none is displayed.
        """
        if DEBUG >= 1:
            print('FileSystemBrowser.handleWorkingDirectoryChanged -- kw:\n\t%s'
                % str(kw))
            print(kw)
        path = self.workingDirCB.currentText()
        if len(path) <= 0:
            path = qt.QDir.current().absolutePath()
        self.fsView.setWorkingDirectory(path)

    def handleContextMenuAction(self, action, param=None):
        """
        Based on the type of action, the function decides how to react:

         :py:class:`RixsTool.ContextMenu`
            Looks in params for key 'fileInfoList' and emits addSignal with said
            list of QFileInfo objects as elements.

        :param QAction action: Action from the context menu
        :param dict param: Parameters that might accompany a certain action.
            Default: None
        """
        if not param:
            param = {}
        if isinstance(action, AddFilesAction):
            fileInfoList = param.get('fileInfoList', None)
            if fileInfoList:
                self.addSignal.emit(fileInfoList)
        if DEBUG >= 1:
            print('FileSystemBrowser.handleContextMenuAction -- finished!')

    #
    # Adding/Removing working directories
    #

    def closeDir(self, safeClose=True):
        """
        Removes the working directory currently selected in the drop down menu.

        :param bool safeClose: Prompts user to confirm closing of working
            directory. Default: True
        """
        #
        # Prompt warning
        #
        if safeClose:
            msg = qt.QMessageBox()
            msg.setIcon(qt.QMessageBox.Warning)
            msg.setWindowTitle('Close directory')
            msg.setText(
                'Are you sure you want to close the current working directory?')
            msg.setStandardButtons(qt.QMessageBox.Ok | qt.QMessageBox.Cancel)
            if msg.exec_() == qt.QMessageBox.Cancel:
                if DEBUG >= 1:
                    print('FileSystemBrowser.closeDir -- Abort')
                return

        #
        # Inteact with QDirListModel
        #
        currentIdx = self.workingDirCB.currentIndex()
        model = self.workingDirCB.model()

        if model.rowCount() > 0:
            model.removeDirs(row=currentIdx, count=1)
        if model.rowCount() <= 0:
            self.closeDirButton.setEnabled(False)
            self.workingDirCB.setCurrentIndex(-1)
        else:
            self.workingDirCB.setCurrentIndex(0)

    def addDir(self, path=None):
        """
        Path is added to working directory combo box and set as new root
        directory in the view.

        :param str path: New directory to be added
        """
        if path is None:
            startDir = self.workingDirCB.currentText()
            if len(startDir) <= 0:
                startDir = qt.QDir.current().absolutePath()
            path = qt.QFileDialog.getExistingDirectory(parent=self,
                caption='Add directory..',
                directory=startDir,
                options=qt.QFileDialog.ShowDirsOnly)
        path = str(path)
        if len(path) <= 0:
            if DEBUG >= 1:
                print('FileSystemBrowser.addDir -- Received empty path. Return.')
            return
        if DEBUG >= 1:
            print("FileSystemBrowser.addDir -- Inserting dir '%s'" % path)
        newIdx = self.workingDirCB.currentIndex() + 1
        model = self.workingDirCB.model()
        model.insertDirs(newIdx, [path])
        # Update ComboBox. The TreeView is updated automatically by the function
        # handleWorkingDirectoryChanged().
        self.workingDirCB.setCurrentIndex(newIdx)
        if not self.closeDirButton.isEnabled():
            self.closeDirButton.setEnabled(True)


class DummyNotifier(qt.QObject):
    @staticmethod
    def signalReceived(**kw):
        print('DummyNotifier.signal received -- kw: %s' % str(kw))


def unitTest_FileSystemBrowser():
    app = qt.QApplication([])

    browser = FileSystemBrowser()
    browser.addSignal.connect(DummyNotifier.signalReceived)
    browser.show()
    app.exec_()


if __name__ == '__main__':
    unitTest_FileSystemBrowser()
