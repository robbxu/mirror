from project import create_app

# Starter - https://testdriven.io/courses/fastapi-celery/docker/
app = create_app()
celery = app.celery_app
