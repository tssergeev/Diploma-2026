import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fitness_club_client.settings")
application = get_wsgi_application()
