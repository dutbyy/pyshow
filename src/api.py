from .render import pipeline as RenderFunc
from multiprocessing import Process, Queue
import time

class RenderApi:
    def __init__(self, config):
        self.queue = None
        self.render_process = None
        self.config = config

    def __del__(self):
        self.close()

    def init(self):
        if self.queue:
            return
        self.queue = Queue()
        self.render_process = Process(target = RenderFunc, args = (self.queue, self.config))
        self.render_process.daemon = True
        self.render_process.start()

    def update(self, obs, wait_time=None):
        self.queue.put(obs)
        if wait_time:
            time.sleep(wait_time)
        elif self.queue.qsize()>30:
            time.sleep(.05)
        else:
            time.sleep(.03)

    def close(self):
        if not self.queue:
            return
        self.render_process.terminate()
        self.queue.close()
        self.render_process = None
        self.queue = None
