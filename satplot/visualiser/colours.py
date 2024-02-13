import numpy as np

max_colours = 10


def getNumberedColour(num, type='bright'):
	return{
		'bright': _brightColDict(num),
		'paper': _paperColDict(num),

	}.get(type, None)


def _brightColDict(num):
	return {
		0: np.asarray([0.9020, 0.0980, 0.2941]),
		1: np.asarray([0.2353, 0.7059, 0.2941]),
		2: np.asarray([1.0000, 0.8824, 0.0980]),
		3: np.asarray([0.0000, 0.5098, 0.7843]),
		4: np.asarray([0.9608, 0.5098, 0.1882]),
		5: np.asarray([0.5686, 0.1176, 0.7059]),
		6: np.asarray([0.2745, 0.9412, 0.9412]),
		7: np.asarray([0.9412, 0.1961, 0.9020]),
		8: np.asarray([0.8235, 0.9608, 0.2353]),
		9: np.asarray([0.9804, 0.7451, 0.8314]),
		# 10: np.asarray([0.0000, 0.5020, 0.5020]),
		# 11: np.asarray([0.8627, 0.7451, 1.0000]),
		# 12: np.asarray([0.6667, 0.4314, 0.1569]),
		# 13: np.asarray([1.0000, 0.9804, 0.7843]),
		# 14: np.asarray([0.5020, 0.0000, 0.0000]),
		# 15: np.asarray([0.6667, 1.0000, 0.7647]),
		# 16: np.asarray([0.5020, 0.5020, 0.0000]),
		# 17: np.asarray([1.0000, 0.8431, 0.7059]),
		# 18: np.asarray([0.0000, 0.0000, 0.5020]),
		# 19: np.asarray([0.5020, 0.5020, 0.5020]),
		# 20: np.asarray([1.0000, 1.0000, 1.0000]),
		# 21: np.asarray([0.0000, 0.0000, 0.0000]),
	}.get(num % max_colours, np.asarray([0.5, 0.5, 0.5]))


def _paperColDict(num):
	return {
		0: np.asarray([0.8902, 0.1020, 0.1098]),
		1: np.asarray([0.1216, 0.4706, 0.7059]),
		2: np.asarray([0.2000, 0.6275, 0.1725]),
		3: np.asarray([1.0000, 0.4980, 0.0000]),
		4: np.asarray([0.4157, 0.2392, 0.6039]),
		5: np.asarray([0.9843, 0.6039, 0.6000]),
		6: np.asarray([0.6510, 0.8078, 0.8902]),		
		7: np.asarray([0.6980, 0.8745, 0.5412]),
		8: np.asarray([0.9922, 0.7490, 0.4353]),		
		9: np.asarray([0.7922, 0.6980, 0.8392]),		
	}.get(num % max_colours, np.asarray([0.5, 0.5, 0.5]))


def getNumberedLinestyle(num):
	return {
		0: 'solid',
		1: 'dashed',
		2: 'dashdot',
		3: extraLinestyleDict['densely dashdotted'],
		4: extraLinestyleDict['dashdotdotted'],
		5: extraLinestyleDict['loosely dashdotdotted'],
		6: extraLinestyleDict['loosely dashdotted'],
	}.get(np.floor(num / max_colours), 'dotted')


extraLinestyleDict = {
	'loosely dotted': (0, (1, 10)),
	'dotted': (0, (1, 1)),
	'densely dotted': (0, (1, 1)),

	'loosely dashed': (0, (5, 10)),
	'dashed': (0, (5, 5)),
	'densely dashed': (0, (5, 1)),

	'loosely dashdotted': (0, (3, 10, 1, 10)),
	'dashdotted': (0, (3, 5, 1, 5)),
	'densely dashdotted': (0, (3, 1, 1, 1)),

	'dashdotdotted': (0, (3, 5, 1, 5, 1, 5)),
	'loosely dashdotdotted': (0, (3, 10, 1, 10, 1, 10)),
	'densely dashdotdotted': (0, (3, 1, 1, 1, 1, 1))}
