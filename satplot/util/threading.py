import logging
import sys
import traceback

import typing

from PyQt5 import QtCore
import satplot

logger = logging.getLogger(__name__)

class WorkerSignals(QtCore.QObject):
	'''
	Defines the signals available from a running worker thread.

	Supported signals are:

	finished
		No data

	error
		tuple (exctype, value, traceback.format_exc() )

	result
		object data returned from processing, anything

	progress
		int indicating % progress

	'''
	finished = QtCore.pyqtSignal()
	error = QtCore.pyqtSignal(tuple)
	result = QtCore.pyqtSignal(object)
	progress = QtCore.pyqtSignal(int)
	report_finished = QtCore.pyqtSignal(object)

class Flag:
	def __init__(self, state:bool):
		self.state:bool = state

	def getState(self) -> bool:
		return self.state

	def setState(self, state:bool):
		self.state = state

	def __bool__(self) -> bool:
		return self.getState()

class Worker(QtCore.QRunnable):
	"""Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    Args:
    	callback (function): The function callback to run on this worker thread. Supplied args and
                     		 kwargs will be passed through to the runner.
    	args: Arguments to pass to the callback function
    	kwargs: Keywords to pass to the callback function
	"""
	def __init__(self, fn, *args, **kwargs):
		super().__init__()

		# Store constructor arguments
		self.fn = fn
		self.args = args
		if 'delay_start' in kwargs.keys():
			self.delayStart = kwargs.pop('delay_start')
		else:
			self.delayStart = False
		# print(f'{args=}')
		# print(f'{kwargs=}')
		self.kwargs = kwargs
		self.signals = WorkerSignals()
		self.started = Flag(False)
		self.running = Flag(False)
		self.chainedWorkers = {}

		# Add the callback to our kwargs
		# self.kwargs['progress_callback'] = self.signals.progress

	@QtCore.pyqtSlot()
	def run(self) -> None:
		"""Initalise the runner function with passed args, kwargs
		"""
		try:
			self.started.setState(True)
			self.running.setState(True)
			result = self.fn(*self.args, self.running, **self.kwargs)
			self.running.setState(False)
		except:
			traceback.print_exc()
			exctype, value = sys.exc_info()[:2]
			self.signals.error.emit((exctype, value, traceback.format_exc()))
		else:
			self.signals.result.emit(result)
		finally:
			if not self.running:
				self.running.setState(False)
				self.signals.finished.emit()
				self.signals.report_finished.emit(self)
				for worker_name, worker in self.chainedWorkers.items():
					if worker is not None:
						logger.info('Starting thread %s:%s',worker_name, worker)
						satplot.threadpool.logStart(worker)

	def isRunning(self) -> bool:
		return self.running.getState()

	def hasStarted(self) -> bool:
		return self.started.getState()

	def terminate(self):
		logger.info('SETTING FLAG %s: FALSE', self)
		self.running.setState(False)

	def addChainedWorker(self, worker_name:str, worker:"Worker"):
		self.chainedWorkers[worker_name] = worker

class Threadpool(QtCore.QThreadPool):

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.running_threads = []

	def getRunningThreads(self) -> list[Worker]:
		return self.running_threads

	def killAll(self) -> None:
		if len(self.running_threads) == 0:
			return

		for ii in range(len(self.running_threads)-1,-1,-1):
			logger.info('Killing thread:%s', self.running_threads[ii])
			self.running_threads[ii].terminate()
			logger.info('\tthread stopped')

	def logStart(self, thread:Worker) -> None:
		self.running_threads.append(thread)
		thread.signals.report_finished.connect(self.clearThreadRecord)
		self.start(thread)

	def clearThreadRecord(self, thread:Worker) -> None:
		self.running_threads.remove(thread)