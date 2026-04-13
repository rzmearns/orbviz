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

import orbviz.util.gifs as gifs
import orbviz.util.paths as orbviz_paths
from orbviz.visualiser.cameras import cam_utility_types
from orbviz.visualiser.contexts.canvas_wrappers.base_cw import BaseCanvas
from orbviz.visualiser.contexts.figure_wrappers.base_fw import BaseFigureWrapper
import orbviz.visualiser.interface.console as console
import orbviz.visualiser.interface.dialogs as orbviz_dialogs


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
		self._gif_data = {'setup_dialog': None,
							'abort_dialog': None,
							'running':False,
							'config':None}

		self._autoplay_data = {'setup_dialog': None,
								'abort_dialog': None,
								'running':False,
								'config':None}

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

	def saveGif(self, gif_config:gifs.GIFConfig):
		# TODO: need to lockout controls

		console.send('Starting GIF saving, please do not touch the controls.')
		self._gif_data['running'] = True
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

		# calculate number of steps of timespan to skip per frame of gif.
		# if less than 1, rounds to 0, and timeslider doesn't move.
		timespan_step_delta = int((gif_config.end_idx - gif_config.start_idx)/gif_config.num_steps)

		for ii in range(gif_config.num_steps):
			# check if GIF aborted
			if not self._gif_data['running']:
				console.send("Aborting GIF creation...")
				break
			# rotate
			if gif_config.cam_config.cam_adjustment:
				if gif_config.cam_config.cam_type == cam_utility_types.CanvasCameraTypes.TURNTABLE:
					new_az = gif_config.cam_config.az_start - ii*gif_config.cam_config.az_step
					new_el = gif_config.cam_config.el_start - ii*gif_config.cam_config.el_step
					self.canvas_wrapper.view_box.camera.azimuth = new_az
					self.canvas_wrapper.view_box.camera.elevation = new_el
					self.canvas_wrapper.onManualCameraRotate()

			# update time slider
			curr_timespan_idx = gif_config.start_idx + ii*timespan_step_delta
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

		self._gif_data['abort_dialog'].close()
		writer.close()
		# reset to pre-gif state
		if gif_config.cam_config.cam_adjustment:
			if gif_config.cam_config.cam_type == 'Turntable':
				self.canvas_wrapper.view_box.camera.azimuth = gif_config.cam_config.az_start
				self.canvas_wrapper.view_box.camera.elevation = gif_config.cam_config.el_start

		self.controls.time_slider.setValue(gif_config.start_idx)


		del self._gif_data['setup_dialog']
		self._gif_data['setup_dialog'] = None
		del self._gif_data['abort_dialog']
		self._gif_data['abort_dialog'] = None
		self._gif_data['running'] = False

		console.send(f"Saved {self.config['name']} GIF to {gif_config.file_path}")

	def autoplay(self, speed:int):
		# TODO: need to lockout controls

		console.send('Starting autoplay, please do not touch the controls.')

		start_idx = self.controls.time_slider.getValue()
		num_steps = self.controls.time_slider.num_ticks
		self._autoplay_data['running'] = True
		for curr_timespan_idx in range(start_idx, num_steps):
			# check if autoplay aborted
			if not self._autoplay_data['running']:
				console.send("Aborting autoplay...")
				break
			# rotate

			# update time slider
			self.controls.time_slider.setValue(curr_timespan_idx)

			# process events
			app.process_events()

		# reset to pre-gif state
		self.controls.time_slider.setValue(start_idx)

		console.send(f"Finished autoplay")

	def setupGIFDialog(self):

		if self.data['history'].timespan is None:
			console.sendErr("Can't create GIF if no data loaded. Please create a scenario.")
			return

		cam_config = cam_utility_types.TurntableCameraAdjustment(self.getCameraState())

		gif_config = gifs.GIFConfig(self.data['history'].timespan,
											cam_config=cam_config)

		self._gif_data['abort_dialog'] = orbviz_dialogs.AbortGIFDialog(self.window, self)
		self._gif_data['setup_dialog'] = orbviz_dialogs.GIFDialog(self.window, self, gif_config)

	def abortGif(self):
		self._gif_data['running'] = False

	def abortAutoplay(self):
		self._autoplay_data['running'] = False

	@abstractmethod
	def getCameraState(self) -> dict:
		raise NotImplementedError()

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