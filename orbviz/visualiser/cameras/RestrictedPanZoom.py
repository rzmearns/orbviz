from ctypes import ArgumentError

import numpy as np

from vispy.geometry import Rect
from vispy.scene.cameras import BaseCamera, PanZoomCamera


class RestrictedPanZoomCamera(PanZoomCamera):
	# Subclass created by github user h21ak9, and published in vispy issue https://github.com/vispy/vispy/issues/2486

	def __init__(self, limits:tuple=(-np.inf, np.inf, -np.inf, np.inf), *args, **kwargs):
		if len(limits) != 4:
			raise ArgumentError("Input 'limits' must have 4 elements")
		self._left_limit = limits[0]
		self._right_limit = limits[1]
		self._bottom_limit = limits[2]
		self._top_limit = limits[3]
		super().__init__(*args, name='RestrictedPanZoom', **kwargs)

	def zoom(self, factor, center=None):
		"""
		This overwrites the behavior of the parent class
		to prevent the user from zooming outside
		the boundaries set by self._limits
		"""

		# Init some variables
		center = center if (center is not None) else self.center
		assert len(center) in (2, 3, 4)
		# Get scale factor, take scale ratio into account
		if np.isscalar(factor):
			scale = [factor, factor]
		else:
			if len(factor) != 2:
				raise TypeError("factor must be scalar or length-2 sequence.")
			scale = list(factor)
		if self.aspect is not None:
			scale[0] = scale[1]

		# Make a new object (copy), so that allocation will
		# trigger view_changed:
		rect = Rect(self.rect)
		# Get space from given center to edges
		left_space = center[0] - rect.left
		right_space = rect.right - center[0]
		bottom_space = center[1] - rect.bottom
		top_space = rect.top - center[1]
		# Scale these spaces
		rect.left = max(center[0] - left_space * scale[0], self._left_limit)
		rect.right = min(center[0] + right_space * scale[0], self._right_limit)
		rect.bottom = max(center[1] - bottom_space * scale[1], self._bottom_limit)
		rect.top = min(center[1] + top_space * scale[1], self._top_limit)
		self.rect = rect

	def resetToExtents(self):
		rect = Rect(self.rect)
		rect.left = self._left_limit
		rect.right = self._right_limit
		rect.bottom = self._bottom_limit
		rect.top = self._top_limit
		self.rect = rect

	def viewbox_mouse_event(self, event):
		"""
		This overwrites the behavior of the parent class
		to prevent the user from panning outside
		the boundaries set by self._limits
		"""

		# Scrolling
		BaseCamera.viewbox_mouse_event(self, event)

		if event.type == "mouse_wheel":
			center = self._scene_transform.imap(event.pos)
			self.zoom((1 + self.zoom_factor)**(-event.delta[1] * 30), center)
			event.handled = True

		if event.type == "mouse_move":
			if event.press_event is None:
				return

			modifiers = event.mouse_event.modifiers
			p1 = event.mouse_event.press_event.pos
			p2 = event.mouse_event.pos

			if 1 in event.buttons and not modifiers:
				# Translate
				p1 = np.array(event.last_event.pos)[:2]
				p2 = np.array(event.pos)[:2]
				p1s = self._transform.imap(p1)
				p2s = self._transform.imap(p2)
				delta = p1s - p2s
				new_rect = self.rect + delta
				if new_rect.left <= self._left_limit or new_rect.right >= self._right_limit:
					delta[0] = 0.0
				if new_rect.top >= self._top_limit or new_rect.bottom <= self._bottom_limit:
					delta[1] = 0.0
				self.pan(delta)
				event.handled = True
			elif 2 in event.buttons and not modifiers:
				# Zoom
				p1c = np.array(event.last_event.pos)[:2]
				p2c = np.array(event.pos)[:2]
				scale = ((1 + self.zoom_factor)**((p1c - p2c) *
												  np.array([1, -1])))
				center = self._transform.imap(event.press_event.pos[:2])
				self.zoom(scale, center)
				event.handled = True
		elif event.type == "mouse_press":
			# accept the event if it is button 1 or 2.
			# This is required in order to receive future events
			event.handled = event.button in [1,2]
		else:
			event.handled = False