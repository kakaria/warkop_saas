import os
from celery import Celery

# kasih tau celery dimana letak settingan Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# kasih nama pekerja kita
app = Celery('warkop-saas')

# ambil semua settingan yang awalnya 'CELERY_' dari settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# deteksi otomatis file tasks.py di semua app 
app.autodiscover_tasks()