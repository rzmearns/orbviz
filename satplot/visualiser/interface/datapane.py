import logging

import typing

from PyQt5 import QtCore, QtGui, QtWidgets


class DataPaneWidget(QtWidgets.QWidget):

	def __init__(self, model, label:str|None='Data Pane') -> None:
		self.content_layout = None
		super().__init__()
		super_vlayout = QtWidgets.QVBoxLayout()
		if label is not None:
			_label_font = QtGui.QFont()
			_label_font.setWeight(QtGui.QFont.Medium)
			_label = QtWidgets.QLabel(label)
			_label.setFont(_label_font)
			super_vlayout.addWidget(_label)

		self._table = self.DataPaneTable()
		self._model = model
		self._table.setModel(self._model)
		self._selection_model = self._table.selectionModel()
		# self._selection_model.selectionChanged.connect(self.emitSelectionMade)
		self._entry_font = QtGui.QFont()
		self._entry_font.setPointSize(8)
		self._header_font = QtGui.QFont()
		self._header_font.setPointSize(10)
		self._header_font.setWeight(QtGui.QFont.Medium)
		self._setStyling()
		super_vlayout.addWidget(self._table)
		super_vlayout.addStretch()


		_label_font = QtGui.QFont()
		_label_font.setWeight(QtGui.QFont.Medium)
		_mouse_font = QtGui.QFont()
		_mouse_font.setItalic(True)
		_mouse_font.setPointSize(8)
		mouse_vlayout = QtWidgets.QVBoxLayout()
		self.mouseover_text = QtWidgets.QLabel('')
		self.mouseover_text.setFont(_mouse_font)
		self.mouseover_fontmetric = self.mouseover_text.fontMetrics()
		mouse_groupbox = QtWidgets.QGroupBox('Mouse Over Info')
		mouse_groupbox.setFont(_label_font)

		mouse_vlayout.addWidget(self.mouseover_text)
		mouse_groupbox.setLayout(mouse_vlayout)
		super_vlayout.addWidget(mouse_groupbox)

		self.setLayout(super_vlayout)
		self._model.rowsInserted.connect(self._setRowStyling)
		self._model.dataChanged.connect(self._autoSetColWidth)

	def _setStyling(self):
		# Config title
		self._table.setStyleSheet('''
										QTableView {
														background-color:#00000000;
										}
									''');
		self._table.horizontalHeader().setStyleSheet('''
														QHeaderView::section {
																background-color: #00000000;
																border: 0px;
														}
														''')
		self._table.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft)

		# self._table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
		# TODO: when contens of data pane can be modified FUTURE, switch to selectRows selection mode
		self._table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
		# self._table.setFocusPolicy(QtCore.Qt.NoFocus)
		self._table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
		self._table.setFont(self._entry_font)

		self._setRowStyling(QtCore.QModelIndex(), 0, self._model.rowCount()-1)

		self._table.verticalHeader().hide()
		self._table.setShowGrid(False)


	def _setRowStyling(self, model, first_row_changed, last_row_changed):
		for row_num in range(first_row_changed, last_row_changed+1):
			self._table.setRowHeight(row_num, 6)
		for col_num in range(self._model.columnCount()):
			self._table.resizeColumnToContents(col_num)

	def _autoSetColWidth(self, model, first_row_changed, last_row_changed) -> None:
		for col_num in range(self._model.columnCount()):
			self._table.resizeColumnToContents(col_num)

	def setMouseText(self,text):
		if self.geometry().width() < self.mouseover_fontmetric.boundingRect(text).width():
			new_text = str.replace(text, '\x1D', '\n')
		else:
			new_text = text
		self.mouseover_text.setText(new_text)

	class DataPaneTable(QtWidgets.QTableView):
		def __init__(self):
			super().__init__()

		def keyPressEvent(self, e):
			clipboard = QtWidgets.QApplication.clipboard()
			if e.matches(QtGui.QKeySequence.Copy):
				row_strs = []
				for index in self.selectionModel().selectedRows():
					row_num = index.row()
					col_str = [f'{self.model().index(row_num, col_num).data()}' for col_num in range(self.model().columnCount())]
					row_strs.append(','.join(col_str))
				s = '\n'.join(row_strs)
				clipboard.setText(s)
				e.setAccepted(True)
			else:
				QtWidgets.QTableView.keyPressEvent(self, e)