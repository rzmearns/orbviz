import logging
import pathlib

from typing import Any, cast

import numpy as np
from scipy.spatial.transform import Rotation
import spherapy.orbit as orbit

from orbviz.model.data_models import (
	data_types,
)
from orbviz.model.geometry import primgeom
import orbviz.util.conversion as orbviz_conversions


class HistoricalAttitude:
	def __init__(self, sc_config:data_types.SpacecraftConfig,
						timestamps:np.ndarray[tuple[int], np.dtype[np.datetime64]],
						raw_quats: np.ndarray[tuple[int,int],np.dtype[np.float64]],
						eci2bf=True):
		# TODO: why is this a necessary parameter of the Attitude
		self.sc_config = sc_config
		self._timestamps = timestamps
		self._sc_raw_quats = raw_quats
		num_samples = len(self._timestamps)
		self._attitude_quats:np.ndarray[tuple[int,int],np.dtype[np.float64]] = np.zeros(self._sc_raw_quats.shape, dtype=np.float64)
		self._sens_attitude_quats:dict[tuple[str,str],np.ndarray[tuple[int,int],np.dtype[np.float64]]] = {}

		self._cached_sc_idx = np.full((num_samples),False)
		self._attitude_matrix_cache:np.ndarray[tuple[int,int,int],np.dtype[np.float64]] = np.zeros((num_samples,3,3), dtype=np.float64)
		self._cached_sens_idx:dict[tuple[str,str], np.ndarray[tuple[int],np.dtype[np.bool_]]] = {}
		self._sens_attitude_matrix_cache:dict[tuple[str,str], np.ndarray[tuple[int,int],np.dtype[np.float64]]] = {}

		# TODO: set standard transform direction as eci2bf
		if eci2bf:
			self._invert_transform = True
			self._attitude_quats = self._sc_raw_quats
		else:
			self._invert_transform = False
			self._attitude_quats = self._sc_raw_quats
			self._attitude_quats[:,3] *= -1

		for suite_name, suite_config in sc_config.getSensorSuites().items():
			for sens_name in suite_config.getSensorNames():
				sens_bf_quat = suite_config.getSensorBodyQuat(sens_name)
				sens_key = (suite_name, sens_name)
				self._sens_attitude_quats[sens_key] = self._quatArrMult(self._attitude_quats, np.tile(sens_bf_quat,(num_samples,1)))
				self._cached_sens_idx[sens_key] = np.full((num_samples),False)
				self._sens_attitude_matrix_cache[sens_key] = np.zeros((num_samples,3,3), dtype=np.float64)

	def getAttitudeTimestamps(self) -> np.ndarray[tuple[int], np.dtype[np.datetime64]]:
		return self._timestamps

	def getAttitude(self, curr_index) -> np.ndarray[tuple[int],np.dtype[np.float64]] | bool:
		if self.isAttitudeValid(curr_index):
			return self.getAttitudeQuat(curr_index)
		return False

	def isAttitudeValid(self, idx:int) -> bool:
		if np.any(np.isnan(self._attitude_quats[idx,:])):
			return False
		return True

	def getAttitudeQuat(self, *args:int) -> np.ndarray[tuple[int],np.dtype[np.float64]]|np.ndarray[tuple[int,int],np.dtype[np.float64]]:
		if len(args) > 0:
			return self._attitude_quats[args[0],:]
		return self._attitude_quats

	def getAttitudeMatrix(self, idx:int) -> np.ndarray[tuple[int,int],np.dtype[np.float64]]:
		cache_key = idx
		if self._cached_sc_idx[cache_key]:
			return self._attitude_matrix_cache[cache_key,:,:]
		else:
			if self.isAttitudeValid(idx):
				rot_mat = Rotation.from_quat(self._attitude_quats[idx,:]).as_matrix()
			else:
				rot_mat = np.eye(3)
			self._cached_sc_idx[cache_key] = True
			self._attitude_matrix_cache[cache_key,:,:] = rot_mat
			cast("np.ndarray[tuple[int,int], np.dtype[np.float64]]",rot_mat)
			return rot_mat

	def getSensorAttitudeQuat(self, suite_name:str, sens_name:str, *args:int) -> np.ndarray[tuple[int],np.dtype[np.float64]]|np.ndarray[tuple[int,int],np.dtype[np.float64]]:
		if len(args) > 0:
			return self._sens_attitude_quats[(suite_name,sens_name)][args[0],:]
		return self._sens_attitude_quats[(suite_name,sens_name)]

	def getSensorAttitudeMatrix(self, suite_name:str, sens_name:str, idx:int) -> np.ndarray[tuple[int],np.dtype[np.float64]]|np.ndarray[tuple[int,int],np.dtype[np.float64]]:
		sens_key = (suite_name, sens_name)
		cache_key = idx
		if self._cached_sens_idx[sens_key][cache_key]:
			return self._sens_attitude_matrix_cache[sens_key][cache_key,:,:]
		else:
			rot_mat = Rotation.from_quat(self._sens_attitude_quats[sens_key][idx,:]).as_matrix()
			self._cached_sens_idx[sens_key][idx] = True
			self._sens_attitude_matrix_cache[sens_key][cache_key,:,:] = rot_mat
			return rot_mat

	def _quatMult(self, q1,q2):
		"""Multiples two quaternions

		Multiplies two quaternions, R and S
		All quaternions need to be supplied in (x,y,z,w)

		#T = R*S
		#Tw = (Rw*Sw − Rx*Sx − Ry*Sy − Rz*Sz)
		#Tx = (Rw*Sx + Rx*Sw − Ry*Sz + Rz*Sy)
		#Ty = (Rw*Sy + Rx*Sz + Ry*Sw − Rz*Sx)
		#Tz = (Rw*Sz − Rx*Sy + Ry*Sx + Rz*Sw)

		Args:
			q1 (ndarray(4,)):
			q2 (ndarray(4,)):

		Returns:
			ndarray(4,): resulting quaternion
		"""

		w = q1[3]*q2[3]-q1[0]*q2[0]-q1[1]*q2[1]-q1[2]*q2[2]
		x = q1[3]*q2[0]+q1[0]*q2[3]+q1[1]*q2[2]-q1[2]*q2[1]
		y = q1[3]*q2[1]-q1[0]*q2[2]+q1[1]*q2[3]+q1[2]*q2[0]
		z = q1[3]*q2[2]+q1[0]*q2[1]-q1[1]*q2[0]+q1[2]*q2[3]
		return np.array((x,y,z,w))

	def _quatArrMult(self, q1_arr, q2_arr):
		res_q_arr = np.zeros((len(q1_arr),4))
		res_q_arr[:,3] = q1_arr[:,3]*q2_arr[:,3]-q1_arr[:,0]*q2_arr[:,0]-q1_arr[:,1]*q2_arr[:,1]-q1_arr[:,2]*q2_arr[:,2]
		res_q_arr[:,0] = q1_arr[:,3]*q2_arr[:,0]+q1_arr[:,0]*q2_arr[:,3]+q1_arr[:,1]*q2_arr[:,2]-q1_arr[:,2]*q2_arr[:,1]
		res_q_arr[:,1] = q1_arr[:,3]*q2_arr[:,1]-q1_arr[:,0]*q2_arr[:,2]+q1_arr[:,1]*q2_arr[:,3]+q1_arr[:,2]*q2_arr[:,0]
		res_q_arr[:,2] = q1_arr[:,3]*q2_arr[:,2]+q1_arr[:,0]*q2_arr[:,1]-q1_arr[:,1]*q2_arr[:,0]+q1_arr[:,2]*q2_arr[:,3]
		return res_q_arr

	@classmethod
	def fromAttitudeConfig(cls, sc_cnfg: data_types.SpacecraftConfig,
								orbit_data: orbit.Orbit,
								att_cnfg:data_types.AttitudeConfig):

		# check sc_id matches sc_config
		if att_cnfg.gen_type == data_types.AttitudeGenMethod.HISTORICAL:
			if att_cnfg.historical_attitude_file is not None:
				timestamps, raw_quats = cls._loadAttitudeFile(att_cnfg.historical_attitude_file)
				return cls(sc_cnfg, timestamps, raw_quats, eci2bf=att_cnfg._attitude_invert_transform)
			else:
				logger.error('Historical Attitude selected, but no data file selected')
				raise ValueError('Historical Attitude selected, but no data file selected')
		elif att_cnfg.gen_type == data_types.AttitudeGenMethod.GENERATED:
			# raw_quats = np.tile((0,0,0,1), (len(orbit_data.timespan), 1))
			raw_quats = cls._genQuats(orbit_data, att_cnfg)

			return cls(sc_cnfg, orbit_data.timespan[:], raw_quats, eci2bf=att_cnfg._attitude_invert_transform)

	@classmethod
	def _loadAttitudeFile(cls, p_file: pathlib.Path) -> tuple[np.ndarray[tuple[int], np.dtype[np.datetime64]], np.ndarray[tuple[int,int],np.dtype[np.float64]]]:
		attitude_q = np.array(())
		attitude_w = np.genfromtxt(p_file, delimiter=',', usecols=[1], skip_header=1).reshape(-1,1)
		attitude_x = np.genfromtxt(p_file, delimiter=',', usecols=[2], skip_header=1).reshape(-1,1)
		attitude_y = np.genfromtxt(p_file, delimiter=',', usecols=[3], skip_header=1).reshape(-1,1)
		attitude_z = np.genfromtxt(p_file, delimiter=',', usecols=[4], skip_header=1).reshape(-1,1)
		attitude_q = np.hstack((attitude_x,attitude_y,attitude_z,attitude_w))
		attitude_dates = np.genfromtxt(p_file, delimiter=',', usecols=[0],skip_header=1, converters={0:orbviz_conversions.date_parser})

		return attitude_dates, attitude_q

	@classmethod
	def _genQuats(cls, orbit_data: orbit.Orbit,
								att_cnfg:data_types.AttitudeConfig):
		num_steps = len(orbit_data.timespan)
		quats = np.zeros((num_steps,4))


		if att_cnfg._prim_target == data_types.RefTarget('ram'):
			prim_target_unit_v = primgeom.unitVector(orbit_data.vel)
		elif att_cnfg._prim_target == data_types.RefTarget('wake'):
			prim_target_unit_v = primgeom.unitVector(-1*orbit_data.vel)
		elif att_cnfg._prim_target == data_types.RefTarget('zenith'):
			prim_target_unit_v = primgeom.unitVector(orbit_data.pos)
		elif att_cnfg._prim_target == data_types.RefTarget('nadir'):
			prim_target_unit_v = primgeom.unitVector(-1*orbit_data.pos)
		elif att_cnfg._prim_target == data_types.RefTarget('sun'):
			prim_target_unit_v = primgeom.unitVector(orbit_data.sun_pos)
		elif att_cnfg._prim_target == data_types.RefTarget('moon'):
			prim_target_unit_v = primgeom.unitVector(orbit_data.moon_pos)

		if att_cnfg._sec_target == data_types.RefTarget('ram'):
			sec_target_unit_v = primgeom.unitVector(orbit_data.vel)
		elif att_cnfg.sec_target == data_types.RefTarget('wake'):
			sec_target_unit_v = primgeom.unitVector(-1*orbit_data.vel)
		elif att_cnfg.sec_target == data_types.RefTarget('zenith'):
			sec_target_unit_v = primgeom.unitVector(orbit_data.pos)
		elif att_cnfg.sec_target == data_types.RefTarget('nadir'):
			sec_target_unit_v = primgeom.unitVector(-1*orbit_data.pos)
		elif att_cnfg.sec_target == data_types.RefTarget('sun'):
			sec_target_unit_v = primgeom.unitVector(orbit_data.sun_pos)
		elif att_cnfg.sec_target == data_types.RefTarget('moon'):
			sec_target_unit_v = primgeom.unitVector(orbit_data.moon_pos)

		ortho_sec_target_unit_v = primgeom.orthogonalProjection(sec_target_unit_v, prim_target_unit_v)
		third_target_vec = np.cross(prim_target_unit_v, ortho_sec_target_unit_v)

		prim_body = primgeom.unitVector(att_cnfg.prim_body_axis)
		sec_body = primgeom.unitVector(att_cnfg.sec_body_axis)
		third_body = np.cross(prim_body, sec_body)

		if not np.isclose(np.dot(prim_body, sec_body), 0):
			raise ValueError("Prim body vectors and Sec Body vectors aren't orthogonal")

		basis_rot = np.zeros((3,3))
		basis_rot[0,0] = np.dot(prim_body, [1,0,0])
		basis_rot[1,0] = np.dot(prim_body, [0,1,0])
		basis_rot[2,0] = np.dot(prim_body, [0,0,1])
		basis_rot[0,1] = np.dot(sec_body, [1,0,0])
		basis_rot[1,1] = np.dot(sec_body, [0,1,0])
		basis_rot[2,1] = np.dot(sec_body, [0,0,1])
		basis_rot[0,2] = np.dot(third_body, [1,0,0])
		basis_rot[1,2] = np.dot(third_body, [0,1,0])
		basis_rot[2,2] = np.dot(third_body, [0,0,1])

		rot = np.zeros((3,3))
		for ii in range(num_steps):

			dot = np.dot(prim_target_unit_v[ii,:], ortho_sec_target_unit_v[ii,:])
			if not np.isclose(dot, 0):
				raise ValueError(f"Prim target vectors and Sec target vectors aren't orthogonal, dot:{dot}, timespan index:{ii}")

			rot[0,0] = np.dot([1,0,0],prim_target_unit_v[ii,:])
			rot[1,0] = np.dot([1,0,0],ortho_sec_target_unit_v[ii,:])
			rot[2,0] = np.dot([1,0,0],third_target_vec[ii,:])
			rot[0,1] = np.dot([0,1,0],prim_target_unit_v[ii,:])
			rot[1,1] = np.dot([0,1,0],ortho_sec_target_unit_v[ii,:])
			rot[2,1] = np.dot([0,1,0],third_target_vec[ii,:])
			rot[0,2] = np.dot([0,0,1],prim_target_unit_v[ii,:])
			rot[1,2] = np.dot([0,0,1],ortho_sec_target_unit_v[ii,:])
			rot[2,2] = np.dot([0,0,1],third_target_vec[ii,:])

			r = Rotation.from_matrix(basis_rot) * Rotation.from_matrix(rot)
			quats[ii, :] = r.inv().as_quat()

		return quats