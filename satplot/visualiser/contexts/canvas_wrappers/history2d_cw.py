import json
import logging
from PyQt5.QtCore import QTimer
import numpy as np
import time
from typing import Any

from PyQt5 import QtCore
from PyQt5 import QtGui

from vispy import scene
from vispy.app.canvas import MouseEvent, ResizeEvent
from vispy.scene.cameras import PanZoomCamera

from satplot.model.data_models.history_data import (HistoryData)
from satplot.model.data_models.earth_raycast_data import (EarthRayCastData)
import satplot.model.geometry.primgeom as pg
from satplot.model.data_models.data_types import PrimaryConfig
from satplot.visualiser.contexts.canvas_wrappers.base_cw import BaseCanvas
import satplot.util.constants as c
import satplot.util.exceptions as exceptions
# import satplot.visualiser.assets.axis_indicators as axis_indicators
import satplot.visualiser.assets.base_assets as base_assets
import satplot.visualiser.assets.constellation as constellation
import satplot.visualiser.assets.earth as earth
import satplot.visualiser.assets.gizmo as gizmo
import satplot.visualiser.assets.orbit as orbit
import satplot.visualiser.assets.moon as moon
import satplot.visualiser.assets.spacecraft as spacecraft
import satplot.visualiser.assets.sun as sun
import satplot.visualiser.assets.widgets as widgets
import satplot.visualiser.cameras.RestrictedPanZoom as RestrictedPanZoom

from vispy.visuals.transforms import STTransform

logger = logging.getLogger(__name__)

create_time = time.monotonic()
MIN_MOVE_UPDATE_THRESHOLD = 1
MOUSEOVER_DIST_THRESHOLD = 5
last_mevnt_time = time.monotonic()
mouse_over_is_highlighting = False

IMAGE_SHAPE = (2046, 1023)  # (height, width)
CANVAS_SIZE = (800, 600)  # (width, height)
COLORMAP_CHOICES = ["viridis", "reds", "blues"]

class History2DCanvasWrapper(BaseCanvas):
	def __init__(self, w:int=1200, h:int=600, keys:str='interactive', bgcolor:str='white'):
		self.canvas = scene.canvas.SceneCanvas(size=(w,h),
										keys=keys,
										bgcolor=bgcolor,
										show=True)
		self.canvas.events.mouse_move.connect(self.onMouseMove)
		self.canvas.events.mouse_wheel.connect(self.onMouseScroll)
		self.canvas.events.resize.connect(self.onResize)
		self.grid = self.canvas.central_widget.add_grid()

		self.view_box = self.grid.add_view(0, 0, bgcolor='#008eaf')
		# self.view_box.camera = RestrictedPanZoom.RestrictedPanZoomCamera(limits=(0, IMAGE_SHAPE[0], 0, IMAGE_SHAPE[1]))
		self.view_box.camera = PanZoomCamera()
		self.view_box.camera.set_range(x=(0, IMAGE_SHAPE[0]), y=(0, IMAGE_SHAPE[1]), margin=0)
		self.vb_aspect_ratio = self.view_box.camera.aspect
		rect = self.view_box.camera.rect
		self.vb_max_extents = [int(rect.width), int(rect.height)]
		self.vb_min_extents = [0, 0]
		self.horiz_pixel_scale = rect.width/360
		self.vert_pixel_scale = rect.height/180

		self.data_models: dict[str,Any] = {}
		self.assets = {}
		self._buildAssets()
		self.mouseOverText = widgets.PopUpTextBox(v_parent=self.view_box,
											padding=[3,3,3,3],
											colour=(253,255,189),
											border_colour=(186,186,186),
											font_size=10)
		self.mouseOverTimer = QtCore.QTimer()
		self.mouseOverTimer.timeout.connect(self._setMouseOverVisible)
		self.mouseOverObject = None

	def _buildAssets(self) -> None:
		self.assets['earth'] = earth.Earth2DAsset(v_parent=self.view_box.scene)
		self.assets['primary_orbit'] = orbit.Orbit2DAsset(v_parent=self.view_box.scene)
		self.assets['spacecraft'] = spacecraft.Spacecraft2DAsset(v_parent=self.view_box.scene)
		self.assets['moon'] = moon.Moon2DAsset(v_parent=self.view_box.scene)
		self.assets['sun'] = sun.Sun2DAsset(v_parent=self.view_box.scene)

	def getActiveAssets(self) -> list[base_assets.AbstractAsset|base_assets.AbstractCompoundAsset|base_assets.AbstractSimpleAsset]:
		active_assets = []
		for k,v in self.assets.items():
			if v.isActive():
				active_assets.append(k)
		return active_assets

	def setModel(self, hist_data:HistoryData, earth_raycast_data:EarthRayCastData) -> None:
		self.data_models['history'] = hist_data
		self.data_models['raycast_src'] = earth_raycast_data

	def modelUpdated(self) -> None:
		if self.data_models['history'] is None:
			logger.error(f'canvas wrapper: {self} does not have a history data model yet')
			raise exceptions.InvalidDataError

		if self.data_models['history'].timespan is not None:
			self.assets['earth'].makeActive()

		# Update data source for moon asset
		if len(self.data_models['history'].getConfigValue('primary_satellite_ids')) > 0:
			self.assets['moon'].setScale(*self.assets['earth'].getDimensions())
			self.assets['moon'].setSource(self.data_models['history'])
			self.assets['moon'].makeActive()

		# Update data source for primary orbit(s)
		if len(self.data_models['history'].getConfigValue('primary_satellite_ids')) > 0:
			# TODO: extend to draw multiple primary satellites
			self.assets['primary_orbit'].setScale(*self.assets['earth'].getDimensions())
			self.assets['primary_orbit'].setSource(self.data_models['history'])
			self.assets['primary_orbit'].makeActive()

		# Update data source for spacecraft
		if len(self.data_models['history'].getConfigValue('primary_satellite_ids')) > 0:
			# TODO: extend to draw multiple primary satellites
			self.assets['spacecraft'].setScale(*self.assets['earth'].getDimensions())
			self.assets['spacecraft'].setSource(list(self.data_models['history'].getPrimaryConfig().getAllSpacecraftConfigs().values())[0],
												self.data_models['history'],
												self.data_models['raycast_src'])
			# set scale again after source, so it gets passed to children assets
			self.assets['spacecraft'].setScale(*self.assets['earth'].getDimensions())
			self.assets['spacecraft'].makeActive()

		# Update data source for sun asset
		if len(self.data_models['history'].getConfigValue('primary_satellite_ids')) > 0:
			self.assets['sun'].makeDormant()
			self.assets['sun'].setScale(*self.assets['earth'].getDimensions())
			self.assets['sun'].setSource(self.data_models['history'])
			self.assets['sun'].makeActive()

		self.assets['earth'].makeDormant()
		self.assets['earth'].makeActive()

	def updateIndex(self, index:int) -> None:
		for asset_name,asset in self.assets.items():
			if asset.isActive():
				asset.updateIndex(index)

	def recomputeRedraw(self) -> None:
		for asset_name, asset in self.assets.items():
			if asset.isActive():
				asset.recomputeRedraw()

	def setFirstDrawFlags(self) -> None:
		for asset in self.assets.values():
			asset.setFirstDrawFlagRecursive()

	def prepSerialisation(self) -> dict[str,Any]:
		# state = {}
		# state['cam-center'] = self.view_box.camera.center
		# state['cam-zoom'] = self.view_box.camera.scale_factor
		# state['cam-az'] = self.view_box.camera.azimuth
		# state['cam-el'] = self.view_box.camera.elevation
		# state['cam-roll'] = self.view_box.camera.roll
		# asset_states = {}
		# for asset_name, asset in self.assets.items():
		# 	asset_states[asset_name] = asset.prepSerialisation()

		# state['asset_states'] = asset_states
		# return state
		pass

	def deSerialise(self, state:dict[str,Any]) -> None:
		# self.view_box.camera.center = state['cam-center']
		# self.view_box.camera.scale_factor = state['cam-zoom']
		# self.view_box.camera.azimuth = state['cam-az']
		# self.view_box.camera.elevation = state['cam-el']
		# self.view_box.camera.roll = state['cam-roll']
		# for asset_name, asset in self.assets.items():
		# 	asset.deSerialise(state['asset_states'][asset_name])
		pass

	def mapAssetPositionsToScreen(self) -> list:
		mo_infos = []
		for asset_name, asset in self.assets.items():
			if asset.isActive():
				mo_infos.append(asset.getScreenMouseOverInfo())
				for ii, world_pos in enumerate(mo_infos[-1]['world_pos']):
					mo_infos[-1]['screen_pos'][ii] = self.mapWorldPosToScreen(world_pos)

		return mo_infos

	def mapScreenPosToWorld(self, screen_pos):
		curr_screen_rect = self.view_box.camera.rect
		canvas_height = self.canvas.native.height()
		canvas_width = self.canvas.native.width()
		world_x = curr_screen_rect.left + screen_pos[0]/canvas_width * curr_screen_rect.width
		world_y = self.vb_max_extents[1] - ((self.vb_max_extents[1]-curr_screen_rect.top) + screen_pos[1]/canvas_height * curr_screen_rect.height)
		return world_x, world_y

	def mapWorldPosToScreen(self, world_pos):
		if len(world_pos) == 0:
			return (None, None)
		curr_screen_rect = self.view_box.camera.rect
		canvas_height = self.canvas.native.height()
		canvas_width = self.canvas.native.width()
		world_pixels_x = (world_pos[0]+180)*self.horiz_pixel_scale
		world_pixels_y = (world_pos[1]+90)*self.vert_pixel_scale
		screen_pos_x = (world_pixels_x - curr_screen_rect.left)*canvas_width/curr_screen_rect.width
		screen_pos_y = ((self.vb_max_extents[1] - world_pixels_y) - (self.vb_max_extents[1]-curr_screen_rect.top))*canvas_height/curr_screen_rect.height

		return screen_pos_x, screen_pos_y

	def _setMouseOverVisible(self):
		self.mouseOverText.setVisible(True)
		self.mouseOverTimer.stop()

	def stopMouseOverTimer(self) -> None:
		self.mouseOverTimer.stop()

	def onMouseMove(self, event:MouseEvent) -> None:
		global last_mevnt_time
		global mouse_over_is_highlighting

		# throttle mouse events to 50ms
		if time.monotonic() - last_mevnt_time < 0.05:
			return

		# reset mouseOver
		self.mouseOverTimer.stop()

		mo_infos = self.mapAssetPositionsToScreen()
		pp = event.pos
		event_world_x, event_world_y = self.mapScreenPosToWorld(pp)
		event_lon = (event_world_x/self.horiz_pixel_scale - 180)
		event_lat = (event_world_y/self.vert_pixel_scale - 90)
		text = f'{event_lon:.2f}, {event_lat:.2f}'

		for jj, mo_info in enumerate(mo_infos):
			for ii, pos in enumerate(mo_info['screen_pos']):
				if ((abs(pos[0] - pp[0]) < MOUSEOVER_DIST_THRESHOLD) and \
					(abs(pos[1] - pp[1]) < MOUSEOVER_DIST_THRESHOLD)):
					last_mevnt_time = time.monotonic()
					self.mouseOverText.setText(mo_info['strings'][ii].lower().capitalize())
					self.mouseOverText.setAnchorPosWithinCanvas(pp, self.canvas)
					self.mouseOverObject = mo_info['objects'][ii].mouseOver(ii)
					self.mouseOverTimer.start(300)
					mouse_over_is_highlighting = True
					return

		self.mouseOverText.setText(text)
		self.mouseOverText.setAnchorPosWithinCanvas(pp, self.canvas)
		self.mouseOverTimer.start(300)

		self.mouseOverText.setVisible(False)
		last_mevnt_time = time.monotonic()
		pass

	def onResize(self, event:ResizeEvent) -> None:
		pass

	def onMouseScroll(self, event:QtGui.QMouseEvent) -> None:
		pass