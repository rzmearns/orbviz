from abc import abstractmethod
import logging

from typing import Any

from matplotlib.backends import backend_qtagg
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.figure
import numpy as np

from PyQt5 import QtWidgets

logger = logging.getLogger(__name__)

class BaseFigureWrapper:
	def __init__(self, w:int=800, h:int=600, bgcolor:str='white', canvas=None):

		self.widget = QtWidgets.QWidget()
		self.canvas = canvas
		self.controls = FigureControls(self)

		if canvas is not None:
			self.figure = canvas.figure
		else:
			self.figure = None

		self.axes = None


	@abstractmethod
	def _buildAssets(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def getActiveAssets(self):
		raise NotImplementedError()

	@abstractmethod
	def setModel(self, *args, **kwargs) -> None:
		# Can accept any subclass of Base Data Model
		raise NotImplementedError()

	@abstractmethod
	def _modelUpdated(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def updateIndex(self, index:int) -> None:
		raise NotImplementedError()

	@abstractmethod
	def recomputeRedraw(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def setfirstDrawFlags(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def prepSerialisation(self) -> dict[str, Any]:
		raise NotImplementedError()

	@abstractmethod
	def deSerialise(self, state:dict[str, Any]) -> None:
		raise NotImplementedError()

	def buildWrapperWidget(self):
		vlayout = QtWidgets.QVBoxLayout()
		vlayout.addWidget(self.controls.navigation_controls)
		vlayout.addWidget(self.canvas)
		self.widget.setLayout(vlayout)

	def addAxes(self, nrows:int, ncols:int) -> None:
		if self.figure is None:
			logger.error('Figure wrapper:%s does not have a figure yet.', self)
			raise ValueError(f'Figure wrapper:{self} does not have a figure yet.')
		else:
			# remove old axes
			if self.axes is not None:
				if isinstance(self.axes, np.ndarray):
					for ax in self.axes:
						ax.remove()
				else:
					self.axes.remove()
				self.axes = None

			self.axes = self.figure.subplots(nrows, ncols)
			self.figure.tight_layout()

	def getFigure(self) -> matplotlib.figure.Figure:
		return self.getCanvas().figure

	def getCanvas(self) -> backend_qtagg.FigureCanvas:
		if self.canvas is None:
			logger.error('Canvas wrapper:%s does not have a canvas yet.', self)
			raise ValueError(f'Canvas wrapper:{self} does not have a canvas yet.')
		else:
			return self.canvas

class FigureControls:
	def __init__(self, parent_figure:BaseFigureWrapper):
		self.navigation_controls = NavigationToolbar(parent_figure.getCanvas(), None)