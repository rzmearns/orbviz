import logging
import typing

import numpy as np
import numpy.testing as np_test

from satplot.model.geometry import polygons


def test_generateCircle_2D():
	coords = polygons.generateCircle((0, 0, 0), 1, (0, 0, 1), sampling=5)
	expected = np.array([[0, 1, 0], [-1, 0, 0], [0, -1, 0], [1, 0, 0], [0, 1, 0]])
	np_test.assert_allclose(coords, expected, rtol=1e-5, atol=1e-8)
