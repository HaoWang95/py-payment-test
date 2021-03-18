from celery import Celery

celcery_instance = Celery('tasks', broker='amqp://guest:guest@127.0.0.1:5672//')

