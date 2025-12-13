from datetime import datetime, time

from django.utils import timezone


def default_midnight():
    # minuit dans la timezone Django
    return timezone.make_aware(datetime.combine(timezone.localdate(), time(0, 0, 0)))
