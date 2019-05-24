"""Repeated timer util"""

import sched
import time
import random


class RepeatedExec:
  """Timer class which executes a given function every interval (seconds)"""

  def __init__(self, interval, func, *args, auto_start=False, interval_variance=0, **kwargs):
    """
    interval: time in seconds
    """
    self.scheduler = sched.scheduler(time.time, time.sleep)

    self.func = func
    self.args = args
    self.kwargs = kwargs

    self.interval = interval
    self.interval_variance = interval_variance

    self._running = False

    # Start repeating at auto
    if auto_start:
      self.start()

  def __run(self):
    """Triggers the function"""
    if self._running:
      self.func(*self.args, **self.kwargs)

      # Add random variance to interval
      rand_interval = self.interval + random.uniform(0, self.interval_variance)

      self.event = self.scheduler.enter(rand_interval, 1, self.__run)

  def start(self):
    """Starts the repeating timer"""
    self._running = True
    self.__run()
    self.scheduler.run()

  def stop(self):
    """Stops the repeating timer"""
    self._running = False
    if self.scheduler and self.event:
      self.scheduler.cancel(self.event)