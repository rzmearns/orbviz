from abc import ABC, abstractmethod
import datetime as dt
import json
import pathlib

from typing import Any

import imageio
import matplotlib.pyplot as plt
import numpy as np

from PyQt5 import QtCore, QtWidgets

import vispy.app as app
from vispy.gloo.util import _screenshot

import orbviz.model.utility_types.gif_datatypes as gif_datatypes
import orbviz.util.paths as orbviz_paths
from orbviz.visualiser.contexts.canvas_wrappers.base_cw import BaseCanvas
from orbviz.visualiser.contexts.figure_wrappers.base_fw import BaseFigureWrapper
import orbviz.visualiser.interface.console as console


class BaseContext(ABC):

	# name_str: str

	@abstractmethod
	def __init__(self, name:str|None=None, data=None):

		self.widget = QtWidgets.QWidget()
		self.layout = QtWidgets.QHBoxLayout(self.widget)
		self.window = None
		self.controls:None|BaseControls = None
		self.active:bool = False
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
	def getIndex(self) -> int|None:
		raise NotImplementedError()

	@abstractmethod
	def setIndex(self, idx:int) -> None:
		raise NotImplementedError()

	@abstractmethod
	def _procDataUpdated(self) -> None:
		# Use this function to collate all functions which should be called when the data model is updated.
		# Only using a single function as a callback avoids any race conditions between setting the timeslider
		# and updating the data
		raise NotImplementedError()

	def setupScreenshot(self):
		file = f"{dt.datetime.now().strftime('%Y-%m-%d_%H%M%S')}_{self.config['name']}.png"
		self.saveScreenshot(pathlib.Path(f'{orbviz_paths.data_dir}/screenshots/{file}'))

	def saveScreenshot(self, file:pathlib.Path):
		if self.canvas_wrapper is None:
			raise AttributeError(f'{self} has no canvas to screenshot')
		if self.window is None:
			raise AttributeError(f'{self} is not in a window')

		if isinstance(self.canvas_wrapper, BaseCanvas):
			# calculate viewport of just the canvas
			geom = self.canvas_wrapper.canvas.native.geometry()
			ratio = self.canvas_wrapper.canvas.native.devicePixelRatio()
			geom = (geom.x(), geom.y(), geom.width(), geom.height())
			new_pos = self.canvas_wrapper.canvas.native.mapTo(self.window, QtCore.QPoint(0, 0))
			new_y = self.window.height() - (new_pos.y() + geom[3])
			viewport = (new_pos.x() * ratio, new_y * ratio, geom[2] * ratio, geom[3] * ratio)

			im = _screenshot(viewport=viewport)
			imageio.imsave(file, im, extension='.png')

		elif isinstance(self.canvas_wrapper, BaseFigureWrapper):
			plt.savefig(file)

		console.send(f"Saved {self.config['name']} screenshot to {file}")

	def saveGif(self, gif_config:gif_datatypes.GIFConfig):
		# TODO: need to lockout controls

		console.send('Starting GIF saving, please do not touch the controls.')
		if gif_config.loop:
			num_loops = 0
		else:
			num_loops = 1

		writer = imageio.get_writer(gif_config.file_path, loop=num_loops)

		# check if vispy based
		if isinstance(self.canvas_wrapper, BaseCanvas):
			canvas_wrapper_type = 'vispy'
			# calculate viewport of just the canvas
			geom = self.canvas_wrapper.canvas.native.geometry()
			ratio = self.canvas_wrapper.canvas.native.devicePixelRatio()
			geom = (geom.x(), geom.y(), geom.width(), geom.height())
			new_pos = self.canvas_wrapper.canvas.native.mapTo(self.window, QtCore.QPoint(0, 0))
			new_y = self.window.height() - (new_pos.y() + geom[3])
			viewport = (new_pos.x() * ratio, new_y * ratio, geom[2] * ratio, geom[3] * ratio)

		elif isinstance(self.canvas_wrapper, BaseFigureWrapper):
			canvas_wrapper_type = 'matplotlib'
			viewport = None
		else:
			raise TypeError(f'Unrecognised canvas_wrapper:{self.canvas_wrapper}, when saving GIF')


		for ii in range(gif_config.num_steps):
			# check if GIF aborted

			# rotate
			if gif_config.cam_config.cam_adjustment:
				if gif_config.cam_config.cam_type == 'Turntable':
					new_az = gif_config.cam_config.az_start - ii*gif_config.cam_config.az_step
					new_el = gif_config.cam_config.el_start - ii*gif_config.cam_config.el_step
					self.canvas_wrapper.view_box.camera.azimuth = new_az
					self.canvas_wrapper.view_box.camera.elevation = new_el
					self.canvas_wrapper.onManualCameraRotate()

			# update time slider
			curr_timespan_idx = gif_config.start_idx + ii
			self.controls.time_slider.setValue(curr_timespan_idx)

			# process events
			app.process_events()

			# add image to buffer
			if canvas_wrapper_type == 'vispy':
				im = _screenshot(viewport=viewport)
			elif canvas_wrapper_type == 'matplotlib':
				im = np.frombuffer(self.canvas_wrapper.figure.canvas.tostring_rgb(), dtype=np.uint8)
				im = im.reshape(self.canvas_wrapper.figure.canvas.get_width_height()[::-1] + (3,))

			writer.append_data(im)

			# use this to print to console on last iteration, otherwise thread doesn't get serviced until after writer closes
			if ii==gif_config.num_steps-2:
				console.send("Writing file. Please wait...")
				app.process_events()

		writer.close()
		# reset to pre-gif state
		if gif_config.cam_config.cam_adjustment:
			if gif_config.cam_config.cam_type == 'Turntable':
				self.canvas_wrapper.view_box.camera.azimuth = gif_config.cam_config.az_start
				self.canvas_wrapper.view_box.camera.elevation = gif_config.cam_config.el_start

		self.controls.time_slider.setValue(gif_config.start_idx)
		del(self._gif_dialog)
		console.send(f"Saved {self.config['name']} GIF to {gif_config.file_path}")


	@abstractmethod
	def setupGIFDialog(self):
		raise NotImplementedError

	def prepSerialisation(self) -> dict[str,Any]:
		state = {}
		state['data'] = self.data
		return state

	def deSerialise(self, state_dict):
		pass

	def makeActive(self) -> None:
		self.active = True
		if self.controls is not None and self.controls.shortcuts is not None:
			for shortcut in self.controls.shortcuts.values():
				shortcut.blockSignals(False)

	def makeDormant(self) -> None:
		self.active = False
		if self.controls is not None and self.controls.shortcuts is not None:
			for shortcut in self.controls.shortcuts.values():
				shortcut.blockSignals(True)
	
class BaseControls:
	@abstractmethod
	def __init__(self, context_name:str, *args, **kwargs):
		self.context_name = context_name
		# dict storing config state for this context
		self.state = {}
		self.action_dict = {}
		self.shortcuts:dict[str,QtWidgets.QShortcut] = {}
		self.toolbar = None
		self.menubar = None
		self._buildActionDict()


	def _buildActionDict(self) -> None:
		with orbviz_paths.actions_dir.joinpath('all.json').open('r') as fp:
			all_action_dict = json.load(fp)
		with orbviz_paths.actions_dir.joinpath(f'{self.context_name}.json').open('r') as fp:
			context_action_dict = json.load(fp)
		self.action_dict = {**all_action_dict, **context_action_dict}

	@abstractmethod
	def getCurrIndex(self):
		raise NotImplementedError