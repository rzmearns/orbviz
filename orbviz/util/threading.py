import logging
import sys
import traceback

from typing import TypedDict, Callable, Any

from PyQt5 import QtCore

import orbviz

logger = logging.getLogger(__name__)

class WorkerThreadConfig(TypedDict):
	"""TypedDict container for configuring a worker thread

	Attributes:
	"""
	thread_name: str
	processing_fn: Callable
	processing_args: list[Any]
	chain_parent: str
	delay_start: bool
	storage_fn: Callable
	finished_fn: Callable
	error_fn: Callable
	auto_delete: bool

class WorkerManager:
	def __init__(self):
		self._wt_configs: dict[str, WorkerThreadConfig] = {}
		self._wt: dict[str, Worker] = {}
		self._wt_is_complete: dict [str, bool] = {}
		self._all_completion_fn = None

	def setAllThreadCompletionFunction(self, fn):
		self._all_completion_fn = fn

	def clearWorkerThreads(self):
		self._wt_configs = {}
		self._wt = {}
		self._wt_is_complete = {}

	def addWorkerThreadConfig(self, config:WorkerThreadConfig):
		# TODO: check no thread with the same name
		logger.debug('Adding worker thread config %s', config)
		self._wt_configs[config['thread_name']] = config

	def registerWorkerThreads(self):
		self._validateFields()
		for name, config in self._wt_configs.items():
			self._wt[name] = Worker(config['processing_fn'], *config['processing_args'], delay_start=config['delay_start'])
			self._wt_is_complete[name] = False
			if config['chain_parent'] is not None:
				self._wt[config['chain_parent']].addChainedWorker(config['thread_name'], self._wt[config['thread_name']])

			if config['storage_fn'] is not None:
				storageFn = self.createStorageFn(name, self._wt[name], config['storage_fn'])
				# trigger the storageFn when the worker thread emits the result
				self._wt[name].signals.result.connect(storageFn)
				# the last step of the storage function should be to kick off all chained workers

			# Create function to log when thread is complete, and check status of all threads
			completionFn = self.createCompleteFn(name, self._wt[name])
			self._wt[name].signals.report_complete.connect(completionFn)

			if config['error_fn'] is not None:
				self._wt[name].signals.error.connect(config['error_fn'])

			self._wt[name].setAutoDelete(config['auto_delete'])

	def start(self):
		for worker_name, worker in self._wt.items():
			if worker is not None and not worker.delayStart:
				logger.info('Starting thread %s:%s',worker_name, worker)
				orbviz.threadpool.logStart(worker)

	def createCompleteFn(self, worker_name, worker):
		def completionFn(*args):
			logger.info("%s completed", worker)
			self._wt_is_complete[worker_name] = True
			self._checkAllThreadsComplete()
		return completionFn

	def createStorageFn(self, worker_name, worker, orig_storage_fn):
		def storageFn(*args):
			orig_storage_fn(*args)
			worker.startChainedWorkers()
		return storageFn

	def _checkAllThreadsComplete(self):
		all_completed = True
		for worker_name, completed in self._wt_is_complete.items():
			if not completed:
				all_completed = False

		if all_completed:
			logger.info("All data threads completed processing. Running completion function %s", self._all_completion_fn)
			self._all_completion_fn()

	def _validateFields(self):
		# TODO: add checks for all correct types and no strings versions of variables
		pass

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
	report_complete = QtCore.pyqtSignal(object)

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

	def __repr__(self):
		return f"{self.fn} worker object"

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
			logger.error('Thread %s experienced error. TERMINATING', self)
			self.signals.error.emit((exctype, value, traceback.format_exc()))
		else:
			logger.info('Thread %s finished. Emitting RESULT signal', self)
			self.signals.result.emit(result)
		finally:
			if not self.running:
				self.running.setState(False)
				logger.info('Thread %s finished. Emitting FINISHED signal', self)
				self.signals.finished.emit()
				# only report complete if no chained workers
				# (report finished will result in threading being deleted)
				if not self.chainedWorkers:
					print(f'{self}:{self.chainedWorkers=}')
					logger.info('Thread %s completed. No chained workers. Emitting REPORT_COMPLETE signal', self)
					self.signals.report_complete.emit(self)

	def isRunning(self) -> bool:
		return self.running.getState()

	def hasStarted(self) -> bool:
		return self.started.getState()

	def terminate(self):
		logger.info('SETTING FLAG %s: FALSE', self)
		self.running.setState(False)

	def addChainedWorker(self, worker_name:str, worker:"Worker"):
		self.chainedWorkers[worker_name] = worker

	def startChainedWorkers(self):
		# This will always be called, so need to guard to only kick off chained workers if they exist (and report completion)
		if self.chainedWorkers:
			for worker_name, worker in self.chainedWorkers.items():
				if worker is not None:
					logger.info('Starting chained thread %s:%s',worker_name, worker)
					orbviz.threadpool.logStart(worker)
			# Once all chained workers have started, report this thread finished.
			logger.info('Thread %s completed. All chained workers started. Emitting REPORT_COMPLETE signal', self)
			self.signals.report_complete.emit(self)

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
		thread.signals.report_complete.connect(self.clearThreadRecord)
		self.start(thread)

	def clearThreadRecord(self, thread:Worker) -> None:
		self.running_threads.remove(thread)