import numpy as np
import satplot.model.geometry.primgeom as primgeom

def generatePixelRays(pixels:tuple[int,int], fov:tuple[float,float]) -> np.ndarray:
	res_arr = np.asarray(pixels, dtype=int)
	# print(f'{res_arr=}')
	fov_arr = np.deg2rad(np.asarray(fov))
	frame_centre = res_arr/2
	h, w = frame_centre
	y, x = np.meshgrid(range(res_arr[0]), range(res_arr[1]))

	x = x.ravel()
	y = y.ravel()
	num_rays = len(x)
	pixelCoords = np.vstack([y,x]).T
	offsets = frame_centre - pixelCoords
	offsets[:,0] *= -1
	angles = offsets / np.array([h,w])  * np.array([fov_arr[1]/2, fov_arr[0]/2])

	# rays in camera frame
	rays_cf = np.ones((num_rays, 3))
	rays_cf[:,0] = -np.tan(angles[:,0])
	rays_cf[:,1] = np.tan(angles[:,1])
	# print(f'{rays_cf.shape=}')
	unit_rays_cf = primgeom.unitVector(rays_cf)
	unit_rays_cf = np.hstack((unit_rays_cf,np.ones((unit_rays_cf.shape[0],1))))
	return unit_rays_cf

def calcPixelAngularSize(pixels:tuple[int,int], fov:tuple[float, float]) -> tuple[float,float]:
	px_deg_x = pixels[0]/fov[0]
	px_deg_y = pixels[1]/fov[1]

	return 1/np.deg2rad(1/px_deg_x), 1/np.deg2rad(1/px_deg_y)

def generateEdgeRays(pixels:tuple[int,int], fov:tuple[float,float]) -> np.ndarray:
	all_rays = generatePixelRays(pixels, fov)
	num_rays = len(all_rays)
	right_range = np.arange(pixels[0]-1,pixels[1]*pixels[0],pixels[0])
	left_range = np.arange(0,pixels[1]*pixels[0],pixels[0])
	edge_rays = np.vstack((all_rays[left_range,:],all_rays[right_range,:],all_rays[1:pixels[0]-1,:],all_rays[num_rays-pixels[0]+1:-1,:]))
	return edge_rays