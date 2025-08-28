import sys

from PyQt5 import QtCore

from vispy import scene
from vispy.scene.canvas import SceneCanvas
from vispy.scene.widgets.viewbox import ViewBox

import satplot.visualiser.colours as colours


class PopUpTextBox:
	def __init__(
		self,
		v_parent: ViewBox | None = None,
		padding: list[float] = [0, 0, 0, 0],
		text_colour: tuple[float, float, float] = (0, 0, 0),
		colour: tuple[float, float, float] = (1, 1, 1),
		border_colour: tuple[float, float, float] = (0, 0, 0),
		font_size: int = 10,
	):
		self.padding = padding
		self.v_parent = v_parent
		self.pos = (0, 0)
		self.b_visual = None
		self.t_width = 1
		self.t_height = 1
		self.updateCenter()
		self.colour = colours.normaliseColour(colour)
		self.border_colour = colours.normaliseColour(border_colour)
		self.text_colour = colours.normaliseColour(text_colour)
		self.val = 0
		self.state = True
		self.b_visual = scene.visuals.Rectangle(
			center=self.center,
			width=self.t_width + self.padding[0] + self.padding[2],
			height=self.t_height + self.padding[1] + self.padding[3],
			color=self.colour,
			border_color=self.border_colour,
			radius=0,
			parent=v_parent,
		)
		self.t_visual = scene.visuals.Text(
			"Default Text",
			color=(0, 0, 0),
			anchor_x="left",
			anchor_y="top",
			parent=v_parent,
			font_size=font_size,
			pos=(0, 0),
		)
		self.t_visual.visible = False
		self.b_visual.visible = False
		self.notifier = self.Notifier()

	def getWidth(self) -> int:
		return self.b_visual.width

	def getHeight(self) -> int:
		return self.b_visual.height

	def setPos(self, pos: tuple[int, int]) -> None:
		self.pos = (pos[0], pos[1])
		self.t_visual.pos = (pos[0] + self.padding[0], pos[1] - self.padding[3])
		self.updateCenter()

	def setAnchorPosWithinCanvas(self, anchor_pos: tuple[int, int], canvas: SceneCanvas) -> None:
		pos = [0, 0]
		if anchor_pos[0] > canvas.native.width() - self.getWidth() + 5:
			pos[0] = anchor_pos[0] - self.getWidth() - 5
		else:
			pos[0] = anchor_pos[0] + 5

		if anchor_pos[1] < self.getHeight() - 5:
			pos[1] = anchor_pos[1] + self.getHeight() + 5
			pos[0] += 10
		else:
			pos[1] = anchor_pos[1] - 5

		self.setPos(pos)

	def updateCenter(self) -> None:
		self.center = (
			(self.pos[0] + self.t_width / 2 + self.padding[0]),
			(self.pos[1] - self.t_height / 2 - self.padding[3]),
		)
		if self.b_visual is not None:
			self.b_visual.center = self.center

	def updateBounds(self) -> None:
		height, width, desc, dx, dy = self._vboInfo(
			self.t_visual.text, self.t_visual._font, "left", "top"
		)
		divider = self.t_visual.transforms.dpi / self.t_visual._font_size / 2
		top_line = abs(height) + abs(desc)
		self.t_height = top_line / divider
		self.t_width = abs(width) / divider

		self.updateCenter()
		if self.b_visual is not None:
			self.b_visual.width = self.t_width + self.padding[0] + self.padding[2]
			self.b_visual.height = self.t_height + self.padding[1] + self.padding[3]
			self.b_visual.update()

	def setText(self, text: str) -> None:
		self.text = str.replace(text, "\x1d", "")
		self.t_visual.text = self.text
		self.notifier.emit(text)
		self.updateBounds()

	def setVisible(self, state: bool) -> None:
		self.t_visual.visible = state
		self.b_visual.visible = state

	def setParent(self, v_parent: ViewBox | None = None) -> None:
		self.v_parent = v_parent
		self.t_visual.parent = v_parent
		self.b_visual.parent = v_parent

	def _vboInfo(self, text, font, anchor_x, anchor_y) -> tuple[float, float, float, float, float]:
		prev = None
		width = height = ascender = descender = 0
		ratio, slop = 1.0 / font.ratio, font.slop
		x_off = -slop

		# Need to make sure we have a unicode string here (Py2.7 mis-interprets
		# characters like "•" otherwise)
		if sys.version[0] == "2" and isinstance(text, str):
			text = text.decode("utf-8")
		# Need to store the original viewport, because the font[char] will
		# trigger SDF rendering, which changes our viewport
		# TODO: get rid of call to glGetParameter!

		# Also analyse chars with large ascender and descender, otherwise the
		# vertical alignment can be very inconsistent
		for char in "hy":
			glyph = font[char]
			y0 = glyph["offset"][1] * ratio + slop
			y1 = y0 - glyph["size"][1]
			ascender = max(ascender, y0 - slop)
			descender = min(descender, y1 + slop)
			height = max(height, glyph["size"][1] - 2 * slop)

		# Get/set the fonts whitespace length and line height (size of this ok?)
		glyph = font[" "]
		spacewidth = glyph["advance"] * ratio
		lineheight = height * 1.5

		# Added escape sequences characters: {unicode:offset,...}
		#   ord('\a') = 7
		#   ord('\b') = 8
		#   ord('\f') = 12
		#   ord('\n') = 10  => linebreak
		#   ord('\r') = 13
		#   ord('\t') = 9   => tab, set equal 4 whitespaces?
		#   ord('\v') = 11  => vertical tab, set equal 4 linebreaks?
		# If text coordinate offset > 0 -> it applies to x-direction
		# If text coordinate offset < 0 -> it applies to y-direction
		esc_seq = {7: 0, 8: 0, 9: -4, 10: 1, 11: 4, 12: 0, 13: 0}

		# Keep track of y_offset to set lines at right position
		y_offset = 0

		# When a line break occur, record the vertices index value
		vi_marker = 0  # noqa: F841
		ii_offset = 0  # Offset since certain characters won't be drawn

		# The running tracker of characters vertex index
		vi = 0  # noqa: F841
		max_width = 0
		for ii, char in enumerate(text):
			if ord(char) in esc_seq:
				if esc_seq[ord(char)] < 0:
					# Add offset in x-direction
					x_off += abs(esc_seq[ord(char)]) * spacewidth
					width += abs(esc_seq[ord(char)]) * spacewidth
				elif esc_seq[ord(char)] > 0:
					# Add offset in y-direction and reset things in x-direction
					dx = dy = 0
					if anchor_x == "right":
						dx = -width
					elif anchor_x == "center":
						dx = -width / 2.0
					ii_offset -= 1
					# Reset variables that affects x-direction positioning
					x_off = -slop
					max_width = max(max_width, width)
					width = 0
					# Add offset in y-direction
					y_offset += esc_seq[ord(char)] * lineheight
			else:
				# For ordinary characters, normal procedure
				glyph = font[char]
				kerning = glyph["kerning"].get(prev, 0.0) * ratio
				y0 = glyph["offset"][1] * ratio + slop - y_offset
				y1 = y0 - glyph["size"][1]
				x_move = glyph["advance"] * ratio + kerning
				x_off += x_move
				ascender = max(ascender, y0 - slop)
				descender = min(descender, y1 + slop)
				width += x_move
				height = max(height, glyph["size"][1] - 2 * slop)
				prev = char

		max_width = max(max_width, width)

		dx = dy = 0
		if anchor_y == "top":
			dy = -descender
		elif anchor_y in ("center", "middle"):
			dy = (-descender - ascender) / 2
		elif anchor_y == "bottom":
			dy = -ascender
		if anchor_x == "right":
			dx = -width
		elif anchor_x == "center":
			dx = -width / 2.0

		return height, max_width, descender, dx, dy

	class Notifier(QtCore.QObject):
		text_updated = QtCore.pyqtSignal(str)

		def __init__(self):
			super().__init__()

		def emit(self, s):
			self.text_updated.emit(s)
