import numpy as np

def generatePixelRayAngles(pixels:tuple[int,int], fov:tuple[float,float]):

	res_arr = np.asarray(pixels, dtype=int)
	fov_arr = np.deg2rad(np.asarray(fov))
	frame_centre = res_arr/2
	h, w = frame_centre
	y, x = np.meshgrid(range(res_arr[0]), range(res_arr[1]))

	x = x.ravel()
	y = y.ravel()
	pixelCoords = np.vstack([y,x]).T
	offsets = frame_centre - pixelCoords
	angles = offsets / np.array([h,w])  * np.array([fov_arr[1], fov_arr[0]])

	return angles