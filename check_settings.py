import os
import sys

# Add /label-studio to path
sys.path.append('/label-studio')
sys.path.append('/label-studio/label_studio')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings.label_studio')
import django
django.setup()
from django.conf import settings

print(f"ROOT: {settings.LOCAL_FILES_DOCUMENT_ROOT}")
print(f"ENABLED: {settings.LOCAL_FILES_SERVING_ENABLED}")
