from celery import Celery
import threading

celcery_instance = Celery('tasks', broker='amqp://guest:guest@127.0.0.1:5672//')

class UpdatePaymentTask(threading.Thread):
    def __init__(self, tasks = {}):
        self.tasks = {}

    def update(self, paymend_id, time):
        self.tasks[paymend_id] = time

    def run(self):
        for k,v in self.tasks.items():
            pass






