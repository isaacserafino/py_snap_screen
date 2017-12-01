import re

from django.db import models
from django.urls.base import reverse
from django_bleach.models import BleachField
from django_extensions.db.fields import AutoSlugField


class BetterBleachField(BleachField):
    def __init__(self):
        super(BetterBleachField, self).__init__(max_length=256, allowed_tags=[None], strip_tags=True)

    def pre_save(self, model_instance, add):
        ''' Remove HTML entities and ampersands from description before saving. '''
        value = BleachField.pre_save(self, model_instance, add)

        return  re.sub(r'&(([A-Za-z]+|#x[\dA-Fa-f]+|#\d+);)?', '', value)


class Project(models.Model):
    active = models.BooleanField(default=True)
    description = BetterBleachField()
    slug = AutoSlugField(unique=True, populate_from='description')

    def get_absolute_url(self) -> str:
        return reverse('project-list')
