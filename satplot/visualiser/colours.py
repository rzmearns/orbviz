import numpy as np
import numpy.typing as nptyping

max_colours = 10

def normaliseColour(rgb_tuple:tuple[float,float,float]) -> list[float]:
	return [rgb_tuple[ii]/255 for ii in [0,1,2]]

def rgb2hex(rgb_tuple:tuple[int,int,int]) -> str:
	hex_str="#"
	for ii in range(3):
		if rgb_tuple[ii] == 0:
			hex_str += "00"
		else:
			hex_str += f"{hex(rgb_tuple[ii])[2:].rjust(2,'0')}"

	return hex_str

def getNumberedColour(num:int, type:str='bright') -> nptyping.NDArray | None:
	return{
		'bright': _brightColDict(num),
		'paper': _paperColDict(num),
	}.get(type, None)


def _brightColDict(num:int) -> nptyping.NDArray:
	return {
		0: np.asarray([230, 25, 75]),
		1: np.asarray([60,180,75]),
		2: np.asarray([255,225,25]),
		3: np.asarray([0,130,200]),
		4: np.asarray([245,130,48]),
		5: np.asarray([145,30,180]),
		6: np.asarray([70,240,240]),
		7: np.asarray([240,50,230]),
		8: np.asarray([210,245,60]),
		9: np.asarray([250,190,212]),
		#  10: np.asarray([230,25,75]),
		#  11: np.asarray([60,180,75]),
		#  12: np.asarray([255,225,25]),
		#  13: np.asarray([0,130,200]),
		#  14: np.asarray([245,130,48]),
		#  15: np.asarray([144,30,180]),
		#  16: np.asarray([70,240,240]),
		#  17: np.asarray([240,50,230]),
		#  18: np.asarray([210,245,60]),
		#  19: np.asarray([250,190,212]),
		#  20: np.asarray([230,25,75]),
		#  21: np.asarray([60,180,75]),
	}.get(num % max_colours, np.asarray([230,25,75]))


def _paperColDict(num:int) -> nptyping.NDArray:
	return {
		0: np.asarray([227,26,28]),
		1: np.asarray([31,120,180]),
		2: np.asarray([51,160,44]),
		3: np.asarray([255,127,0]),
		4: np.asarray([106,61,154]),
		5: np.asarray([251,154,153]),
		6: np.asarray([166,206,227]),
		7: np.asarray([178,223,138]),
		8: np.asarray([253,191,111]),
		9: np.asarray([202,178,214]),
	}.get(num % max_colours, np.asarray([128, 128, 128]))


def getNumberedLinestyle(num:int) -> str:
	return {
		0: 'solid',
		1: 'dash',
		2: 'dashdot',
		3: 'dot',
		4: 'longdash',
		5: 'longdashdot'
	}.get(np.floor(num / max_colours), 'solid')