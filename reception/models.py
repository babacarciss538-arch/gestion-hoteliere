from django.db import models


class CheckIn(models.Model):
    actual_check_in = models.DateTimeField(null=True, blank=True)
    expected_check_out = models.DateField(null=True, blank=True)
