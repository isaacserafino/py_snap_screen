import re

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch.dispatcher import receiver
from django.urls.base import reverse
from django_bleach.models import BleachField
from django_extensions.db.fields import AutoSlugField


class Project(models.Model):
    active = models.BooleanField(default=True)
    description = BleachField(max_length=256, allowed_tags=[], strip_tags=True)
    slug = AutoSlugField(unique=True, populate_from='description')

    def get_absolute_url(self) -> str:
        return reverse('project-list')


@receiver(pre_save, sender=Project)
def clean_description(sender, instance:Project, *args, **kwargs) -> None:  # @UnusedVariable Because this method is an
        # override
    ''' Remove HTML entities and ampersands from description before saving. '''
    instance.description = re.sub(r'&(([A-Za-z]+|#x[\dA-Fa-f]+|#\d+);)?', '', instance.description)
