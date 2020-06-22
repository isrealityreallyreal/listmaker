import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import pandas as pd
import numpy as np

class MainWindow(QMainWindow):
    def __init__(self, widget):
        QMainWindow.__init__(self)
        self.setWindowTitle("List Maker Beta")
        self.central_widget = widget
        self.setCentralWidget(self.central_widget)

        # Add menus
        self.menu = self.menuBar()
        self.file_menu = self.menu.addMenu("File")
        self.merge_menu = self.menu.addMenu("Merge")

        # File menu

        load_action = QAction("Load", self)
        load_action.triggered.connect(self.load)

        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save)

        print_action = QAction("Print", self)
        print_action.triggered.connect(self.print_data)

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.Quit)
        quit_action.triggered.connect(self.close)

        self.file_menu.addAction(load_action)
        self.file_menu.addAction(save_action)
        self.file_menu.addAction(print_action)
        self.file_menu.addAction(quit_action)

        # Merge menu

        merge_current_action = QAction("Merge with current sheet", self)
        merge_current_action.triggered.connect(self.merge_current)

        merge_new_action = QAction("Merge external sheets", self)
        merge_new_action.triggered.connect(self.merge_new)

        # Window dimensions
        geometry = qApp.desktop().availableGeometry(self)
        self.setFixedSize(geometry.width(), geometry.height())

    # Prints to the console
    def print_data(self):
        print(self.central_widget.get_data())

    def load(self):
        filename, ok = QFileDialog.getOpenFileName(self, "Load spreadsheet", ".", "CSV files (*.csv)")
        if ok:
            #sheet = pd.read_csv(filename)
            self.central_widget = Widget(pd.read_csv(filename))
            self.setCentralWidget(self.central_widget)

    def save(self):
        filename, ok = QFileDialog.getSaveFileName(self, "Save spreadsheet as", ".", "CSV files (*.csv)")
        if ok:
            self.central_widget.get_data().to_csv(filename)

    def merge_current(self):
        #

    def merge_new(self):
        #

class CustomTableModel(QAbstractTableModel):
    def __init__(self, data):
        QAbstractTableModel.__init__(self)
        self.table = data

    def get_data(self):
        return self.table

    def rowCount(self, parent=QModelIndex()):
        return len(self.table.index)

    def columnCount(self, parent=QModelIndex()):
        return len(self.table.columns)

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.table.columns[section]
        else:
            return self.table.index[section]

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            if orientation == Qt.Horizontal:
                self.table.rename(columns={ (self.table.columns[section]): value }, inplace=True)
            else:
                self.table.rename(index={ (self.table.index[section]) : value }, inplace=True)
            self.headerDataChanged.emit(orientation, section, section)
            return True
        return False

    def removeColumns(self, position, columns, parent):
        self.beginRemoveColumns(QModelIndex(), position, position+columns-1)
        self.table.drop(self.table.columns[position], axis=1, inplace=True)
        self.endRemoveColumns()
        return True

    def removeRows(self, position, rows, parent):
        self.beginRemoveRows(QModelIndex(), position, position+rows-1)
        self.table.drop(self.table.index[position], inplace=True)
        self.endRemoveRows()
        return True

    def insertRows(self, position, rows, parent):
        self.beginInsertRows(QModelIndex(), position, position+rows-1)
        line = pd.DataFrame(columns=self.table.columns, index=[position-0.5])
        self.table = self.table.append(line, ignore_index=False)
        self.table = self.table.sort_index().reset_index(drop=True)
        self.endInsertRows()
        return True

    def data(self, index, role=Qt.DisplayRole):
        column = index.column()
        row = index.row()
        cell = self.table.values[row][column]
        if pd.isna(cell):
            cell = ""

        if role == Qt.DisplayRole:
            return cell
        elif role == Qt.BackgroundRole:
            return QColor(Qt.white)
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignLeft

        return None
    
    def setData(self, index, value, role=Qt.EditRole):
        column = index.column()
        row = index.row()
        if(role == Qt.EditRole):
            self.table.iat[row, column] = value
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable


class Widget(QWidget):
    def __init__(self, data):
        QWidget.__init__(self)

        # Getting the Model
        self.model = CustomTableModel(data)
        self.delegate = Delegate()

        # Creating a QTableView
        self.table_view = QTableView()
        self.table_view.setItemDelegate(self.delegate)
        self.table_view.setModel(self.model)

        # QTableView Headers
        self.horizontal_header = self.table_view.horizontalHeader()
        self.vertical_header = self.table_view.verticalHeader()

        #self.horizontal_header.setSectionResizeMode(QHeaderView.ResizeToContents)
        #self.vertical_header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.horizontal_header.setStretchLastSection(True)

        self.horizontal_header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.horizontal_header.customContextMenuRequested.connect(self.horizontalHeaderMenu)
        self.vertical_header.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.vertical_header.customContextMenuRequested.connect(self.verticalHeaderMenu)

        # QWidget Layout
        self.main_layout = QHBoxLayout()
        size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        ## Left layout
        size.setHorizontalStretch(1)
        self.table_view.setSizePolicy(size)
        self.main_layout.addWidget(self.table_view)

        # Set the layout to the QWidget
        self.setLayout(self.main_layout)

    def horizontalHeaderMenu(self, index):
        globalIndex = self.mapToGlobal(index)
        logicalIndex = self.horizontal_header.logicalIndexAt(index)
        menu = QMenu()
        renameAction = menu.addAction("Rename column")
        deleteAction = menu.addAction("Delete column")
        selectedItem = menu.exec_(globalIndex)
        if selectedItem == renameAction:
            name, ok = QInputDialog.getText(self, "Rename column", "new name:")
            if ok:
                self.model.setHeaderData(logicalIndex, Qt.Horizontal, name, Qt.EditRole)
        elif selectedItem == deleteAction:
            self.model.removeColumn(logicalIndex)

    def verticalHeaderMenu(self, index):
        globalIndex = self.mapToGlobal(index)
        logicalIndex = self.vertical_header.logicalIndexAt(index)
        menu = QMenu()
        renameAction = menu.addAction("Rename row")
        deleteAction = menu.addAction("Delete row")
        insertAction = menu.addAction("Insert row")
        selectedItem = menu.exec_(globalIndex)
        if selectedItem == renameAction:
            name, ok = QInputDialog.getText(self, "Rename row", "new name:")
            if ok:
                self.model.setHeaderData(logicalIndex, Qt.Vertical, name, Qt.EditRole)
        elif selectedItem == deleteAction:
            self.model.removeRow(logicalIndex)
        elif selectedItem == insertAction:
            self.model.insertRow(logicalIndex)

    def get_data(self):
        return self.model.get_data()

class Delegate(QtWidgets.QItemDelegate):

    def createEditor(self, parent, option, index):
        return super(Delegate, self).createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        text = index.data(Qt.EditRole) or index.data(Qt.DisplayRole)
        editor.setText(str(text))

# Create the Qt Application
app = QApplication([])

widget = Widget(pd.DataFrame())
window = MainWindow(widget)
window.show()

# Run the main Qt loop
sys.exit(app.exec_())
