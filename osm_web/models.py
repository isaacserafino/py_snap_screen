import re

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls.base import reverse
from django_bleach.models import BleachField
from django_extensions.db.fields import AutoSlugField


class BetterBleachField(BleachField):

    def __init__(self, *args, **kwargs):
        super(BetterBleachField, self).__init__(max_length=256, allowed_tags=[None], strip_tags=True)

    def pre_save(self, model_instance, add):
        ''' Remove HTML entities and ampersands from description before saving. '''
        value = BleachField.pre_save(self, model_instance, add)

        return  re.sub(r'&(([A-Za-z]+|#x[\dA-Fa-f]+|#\d+);)?', '', value)


class Project(models.Model):
    active = models.BooleanField(default=True)
    admin = models.ForeignKey(User)
    description = BetterBleachField()
    slug = AutoSlugField(unique=True, populate_from='description')

    def get_absolute_url(self) -> str:
        return reverse('project-list')

    def held_by(self, user: User) -> bool:
        return self.stake_set.filter(holder=user, quantity__gt=0).exists()


class Ask(models.Model):
    active = models.BooleanField(default=True)
    asker = models.ForeignKey(User)
    price = models.PositiveIntegerField(validators=[MinValueValidator(1),
            MaxValueValidator(1000000000)])

    project = models.ForeignKey(Project)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    def get_absolute_url(self) -> str:
        return reverse('project-detail', args=[self.project.slug])


class Stake(models.Model):
    holder = models.ForeignKey(User)
    project = models.ForeignKey(Project)
    quantity = models.PositiveIntegerField()
