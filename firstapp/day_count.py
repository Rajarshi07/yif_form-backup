from django.db.models.functions import TruncDay
from datetime import datetime, timedelta

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','yif_form.settings')
import django
django.setup()

from firstapp.models import registration

past_7_days = datetime.today() - timedelta(days=7)
returnn

