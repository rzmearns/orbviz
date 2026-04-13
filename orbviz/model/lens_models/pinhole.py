

import numpy as np

import orbviz.model.geometry.primgeom as primgeom


def generatePixelRays(pixels:tuple[int,int], fov:tuple[float,float]) -> np.ndarray:
	res_arr = np.asarray(pixels, dtype=int)
	# print(f'{res_arr=}')
	fov_arr = np.deg2rad(np.asarray(fov))
	x_fov_step = (fov_arr[0]/(res_arr[0]-1))
	y_fov_step = (fov_arr[1]/(res_arr[1]-1))

	x_fov_range = np.append(np.arange(-fov_arr[0]/2, fov_arr[0]/2, x_fov_step), fov_arr[0]/2)
	y_fov_range = np.append(np.arange(-fov_arr[1]/2, fov_arr[1]/2, y_fov_step), fov_arr[1]/2)
	angles_x, angles_y = np.meshgrid(x_fov_range, y_fov_range)


	# angles_x, angles_y = np.meshgrid(np.append(np.arange(-fov_arr[0]/2, fov_arr[0]/2, x_fov_step),fov_arr[0]/2),
    									# np.append(np.arange(-fov_arr[1]/2, fov_arr[1]/2, y_fov_step),fov[1]/2))
	angles_x_flat = angles_x.ravel()
	angles_y_flat = angles_y.ravel()
	angles = np.vstack([angles_x_flat, angles_y_flat]).T
	num_rays = len(angles)

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

def calcLowRes(true_resolution:tuple[int,int]) -> tuple[int,int]:
	lowres = [0,0]
	max_1D_res = 240
	min_1D_res = 3
	lowres_ratio = 100
	aspect_ratio = true_resolution[0]/true_resolution[1]
	if aspect_ratio > 1:
		lowres_h = int(true_resolution[1]/lowres_ratio)
		lowres_h = np.clip(lowres_h, min_1D_res, max_1D_res)
		if lowres_h == max_1D_res or lowres_h == max_1D_res:
			lowres_ratio = true_resolution[1]/lowres_h
		lowres_w = int(true_resolution[0]/lowres_ratio)

	elif aspect_ratio < 1:
		lowres_w = int(true_resolution[0]/lowres_ratio)
		lowres_w = np.clip(lowres_w, min_1D_res, max_1D_res)
		if lowres_w == max_1D_res or lowres_w == max_1D_res:
			lowres_ratio = true_resolution[0]/lowres_w
		lowres_h = int(true_resolution[1]/lowres_ratio)
	else:
		lowres_w = int(true_resolution[0]/lowres_ratio)
		lowres_w = np.clip(lowres_w, min_1D_res, max_1D_res)
		lowres_h = lowres_w

	return (lowres_w, lowres_h)

def calcReScaling(true_resolution:tuple[int,int], scaling:float) -> tuple[int,int]:

	scaled_res_w = int(true_resolution[0] * scaling)
	scaled_res_h = int(true_resolution[1] * scaling)

	return (scaled_res_w, scaled_res_h)