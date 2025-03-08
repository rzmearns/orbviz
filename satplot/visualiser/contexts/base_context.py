from abc import ABC, abstractmethod
import datetime as dt
import imageio
import json
import pathlib
from typing import Any

from PyQt5 import QtWidgets, QtCore

from vispy.gloo.util import _screenshot

import satplot.util.paths as paths

class BaseContext(ABC):

	# name_str: str

	@abstractmethod
	def __init__(self, name:str|None=None, data=None):

		self.widget = QtWidgets.QWidget()
		self.layout = QtWidgets.QHBoxLayout(self.widget)
		self.window = None
		self.controls = None

		# dict storing crucial configuration data for this context
		self.config = {}
		self.config['name'] = name
		self.sccam_state = None
		self.canvas_wrapper = None
		self.data = None
		self.load_worker = None
		self.load_worker_thread = None
		self.save_worker = None
		self.save_worker_thread = None

	@abstractmethod
	def saveState(self) -> None:
		raise NotImplementedError()
	
	@abstractmethod
	def loadState(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def connectControls(self) -> None:
		raise NotImplementedError()

	@abstractmethod
	def _configureData(self) -> None:
		raise NotImplementedError()

	def setupScreenshot(self):
		file = f"{dt.datetime.now().strftime('%Y-%m-%d_%H%M%S')}_{self.config['name']}.png"
		self.saveScreenshot(pathlib.Path(f'{paths.data_dir}/screenshots/{file}'))

	def saveScreenshot(self, file:pathlib.Path):
		if self.canvas_wrapper is None:
			raise AttributeError(f'{self} has no canvas to screenshot')
		if self.window is None:
			raise AttributeError(f'{self} is not in a window')

		# calculate viewport of just the canvas
		geom = self.canvas_wrapper.canvas.native.geometry()
		ratio = self.canvas_wrapper.canvas.native.devicePixelRatio()
		geom = (geom.x(), geom.y(), geom.width(), geom.height())
		new_pos = self.canvas_wrapper.canvas.native.mapTo(self.window, QtCore.QPoint(0, 0))
		new_y = self.window.height() - (new_pos.y() + geom[3])
		viewport = (new_pos.x() * ratio, new_y * ratio, geom[2] * ratio, geom[3] * ratio)

		im = _screenshot(viewport=viewport)
		imageio.imsave(file, im, extension='.png')

	@abstractmethod
	def saveGif(self, file:pathlib.Path, loop=True, *args, **kwargs):
		raise NotImplementedError

	@abstractmethod
	def setupGIFDialog(self):
		raise NotImplementedError

	def prepSerialisation(self) -> dict[str,Any]:
		state = {}
		state['data'] = self.data
		return state

	def deSerialise(self, state_dict):
		pass
	
class BaseControls:
	@abstractmethod
	def __init__(self, context_name:str, *args, **kwargs):
		self.context_name = context_name
		# dict storing config state for this context
		self.state = {}
		self.action_dict = {}
		self._buildActionDict()

	def _buildActionDict(self) -> None:
		with open(f'resources/actions/all.json','r') as fp:
			all_action_dict = json.load(fp)
		with open(f'resources/actions/{self.context_name}.json','r') as fp:
			context_action_dict = json.load(fp)
		self.action_dict = {**all_action_dict, **context_action_dict}