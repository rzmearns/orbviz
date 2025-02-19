from abc import ABC, abstractmethod
import json
import numpy as np
import sys
from typing import Any

from PyQt5 import QtWidgets, QtCore

import satplot.visualiser.assets.base as base_assets

class BaseCanvas():
	def __init__(self, w:int=800, h:int=600, keys:str='interactive', bgcolor:str='white'):
		self.canvas = None
		self.grid = None
		self.view_box = None
		self.assets={}


	@abstractmethod
	def _buildAssets(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def getActiveAssets(self) -> list[base_assets.AbstractAsset|base_assets.AbstractCompoundAsset|base_assets.AbstractSimpleAsset]:
		raise NotImplementedError()

	@abstractmethod
	def setModel(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def _modelUpdated(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def updateIndex(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def recomputeRedraw(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def setfirstDrawFlags(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def prepSerialisation(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def deSerialise(self) -> None:
		raise NotImplementedError()