from celery import current_app as current_celery_app
from celery import Celery
from celery.schedules import crontab
from project.config import settings

def create_celery():
    celery_app = current_celery_app

    celery_app.config_from_object(settings, namespace="CELERY")
    # https://github.com/celery/celery/issues/3797
    

    @celery_app.task
    def celery_test():
        print("Celery test executed")

    
    return celery_app
