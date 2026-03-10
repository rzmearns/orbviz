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
		self._worker_thread_configs: dict[str, WorkerThreadConfig] = {}
		self._worker_threads: dict[str, Worker] = {}
		self._worker_thread_completion: dict [str, bool] = {}
		self._all_completion_fn = None

	def setAllThreadCompletionFunction(self, fn):
		self._all_completion_fn = fn

	def clearWorkerThreads(self):
		self._worker_thread_configs = {}
		self._worker_threads = {}
		self._worker_thread_completion = {}

	def addWorkerThreadConfig(self, config:WorkerThreadConfig):
		# TODO: check no thread with the same name
		logger.debug('Adding worker thread config %s', config)
		self._worker_thread_configs[config['thread_name']] = config

	def registerWorkerThreads(self):
		self._validateFields()
		for name, config in self._worker_thread_configs.items():
			self._worker_threads[name] = Worker(config['processing_fn'], *config['processing_args'], delay_start=config['delay_start'])
			self._worker_thread_completion[name] = False
			if config['chain_parent'] is not None:
				self._worker_threads[config['chain_parent']].addChainedWorker(config['thread_name'], self._worker_threads[config['thread_name']])
			if config['storage_fn'] is not None:
				storageFn = self.createStorageFn(config['thread_name'], config['storage_fn'])
				self._worker_threads[name].signals.result.connect(storageFn)
				use_finished_to_mark_completion = False
			else:
				use_finished_to_mark_completion = True

			if config['finished_fn'] is not None:
				completionFn = self.createCompleteFn(config['thread_name'], config['finished_fn'], use_finished_to_mark_completion)
				self._worker_threads[name].signals.report_finished.connect(completionFn)

			if config['error_fn'] is not None:
				self._worker_threads[name].signals.error.connect(config['error_fn'])

			self._worker_threads[name].setAutoDelete(config['auto_delete'])

	def start(self):
		for thread_name, thread in self._worker_threads.items():
			if thread is not None and not thread.delayStart:
				logger.info('Starting thread %s:%s',thread_name, thread)
				orbviz.threadpool.logStart(thread)

	def createCompleteFn(self, thread_name, orig_completion_fn, use_for_thread_completion=False):
		def completionFn(*args):
			orig_completion_fn(*args)
			if use_for_thread_completion:
				self._worker_thread_completion[thread_name] = True
				self._checkAllThreadsComplete()
		return completionFn

	def createStorageFn(self, thread_name, orig_storage_fn):
		def storageFn(*args):
			orig_storage_fn(*args)
			self._worker_thread_completion[thread_name] = True
			self._checkAllThreadsComplete()
		return storageFn

	def _checkAllThreadsComplete(self):
		all_completed = True
		for thread_name, completed in self._worker_thread_completion.items():
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
				self.signals.report_finished.emit(self)
				for worker_name, worker in self.chainedWorkers.items():
					if worker is not None:
						logger.info('Starting chained thread %s:%s',worker_name, worker)
						orbviz.threadpool.logStart(worker)

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