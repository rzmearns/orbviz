from __future__ import division

import numpy as np
from vispy.scene.cameras import BaseCamera
from vispy.geometry import Rect
from vispy.scene.cameras import PanZoomCamera
from ctypes import ArgumentError

class Static2D(PanZoomCamera):

    def __init__(self, *args, **kwargs):
        super(Static2D, self).__init__(*args, **kwargs)
    
    def zoom(self, factor, center=None):
        """
        This overwrites the behavior of the parent class
        to prevent the user from zooming
        """
        pass                                # noqa PIE790
    
    def viewbox_mouse_event(self, event):
        """
        This overwrites the behavior of the parent class
        to prevent the user from panning
        """

        pass                                # noqa PIE790