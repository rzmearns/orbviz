import logging

from collections.abc import Callable
from typing import Any

import numpy as np

from PyQt5 import QtCore

from orbviz.util import formatting

'''
data items of the DataPaneModel are stored as a dict
{parameter:<str>,
 value:<val/callback>,
 unit:<str>,
 precision:<int>}

'''

logger = logging.getLogger(__name__)

class DataPaneModel(QtCore.QAbstractTableModel):
	counter = 0
	def __init__(self, *args: Any, **kwargs: Any) -> None:
		super().__init__()
		self._items = []
		self._headers = ['Parameter', 'Unit', 'Value']

	def count(self) -> int:
		return len(self._items)

	def rowCount(self, parent=QtCore.QModelIndex()) -> int:
		if parent.isValid():
			# this is not a tree, rows should not have children
			return 0
		return len(self._items)

	def columnCount(self, parent=QtCore.QModelIndex()) -> int:
		if parent.isValid():
			# this is not a tree, columns should not have children
			return 0
		return 3

	def headerData(self,
					section: int,
					orientation: QtCore.Qt.Orientation,
					role: int=QtCore.Qt.ItemDataRole.DisplayRole) -> str:
		if orientation == QtCore.Qt.Orientation.Horizontal:
			if role == QtCore.Qt.ItemDataRole.DisplayRole and 0 <= section < len(self._headers):
				return self._headers[section]

	def data(self, index: QtCore.QModelIndex, role:int=QtCore.Qt.ItemDataRole.DisplayRole) -> str:
		row = index.row()
		column = index.column()
		if role == QtCore.Qt.ItemDataRole.DisplayRole:
			column_key = self._headers[column].lower()
			val = self._items[row][column_key]
			if val is None:
				val = ''
			# if it's a lambda, call it
			if isinstance(val, Callable):
				try:
					return_val = val()
				except IndexError:
					# TODO: logger not respecting main handlers, prints to stdout as well as log file.
					# logger.warning(e)
					# print(e)
					return_val = None
				except Exception as e:
					logger.warning("Datapane callback for %s:%s", self._items[row]['parameter'], e)
					return_val = 'Error'
			else:
				return_val = val

			if self._headers[column].lower() == 'value':
				if 'precision' in self._items[row].keys():
					display_precision = self._items[row]['precision']
				else:
					display_precision = 2
				return_val = self._formatReturnVal(return_val, display_precision)

			return f'{return_val}'

	def removeEntries(self, uds_list: list[tuple[str, str]]) -> None:
		for el in uds_list:
			try:
				self._items.index(el)
			except ValueError:
				continue
			self._items.remove(el)

	def refresh(self):
		top_left = self.index(0,0)
		bottom_right = self.index(self.count(),3)
		self.dataChanged.emit(top_left, bottom_right)

	def insertRows(self,row:int, count:int, parent=QtCore.QModelIndex()) -> bool:

		first_idx = row
		last_idx = row + count -1
		if parent.isValid():
			return False

		# required by QT
		self.beginInsertRows(parent, first_idx, last_idx)

		# required by QT
		self.endInsertRows()
		return True

	def appendData(self, item_dict:dict):
		new_row_idx = self.count()
		if self.insertRow(self.rowCount()):
			self._items.append(item_dict)
			col_num = 0
			max_cols = self.columnCount()
			for v in item_dict.values():
				if col_num < max_cols:
					self.setData(self.createIndex(new_row_idx, col_num), v, QtCore.Qt.ItemDataRole.DisplayRole);
		self.dataChanged.emit(self.index(new_row_idx,0), self.index(new_row_idx,self.columnCount()))

	def removeRows(self,row:int, count:int, parent=QtCore.QModelIndex()) -> bool:
		# required by QT
		first_idx = row
		last_idx = row + count -1
		self.beginRemoveRows(parent, first_idx, last_idx)

		# required by QT
		self.endRemoveRows()


	def _formatReturnVal(self, return_val, display_precision):
		if isinstance(return_val, float):
			return formatting.float2TableRow(return_val, display_precision)
		elif isinstance(return_val, np.ndarray):
			return formatting.ndarray2TableRow(return_val, display_precision)
		elif isinstance(return_val, list):
			return formatting.list2TableRow(return_val, display_precision)
		elif isinstance(return_val, tuple):
			return formatting.tuple2TableRow(return_val, display_precision)
		else:
			return f'{return_val}'