import re

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls.base import reverse
from django_bleach.models import BleachField
from django_extensions.db.fields import AutoSlugField
from django.db.models.aggregates import Sum


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


class Stake(models.Model):
    holder = models.ForeignKey(User)
    project = models.ForeignKey(Project)
    quantity = models.PositiveIntegerField()

    def existing_offers(self) -> int:
        return int(Ask.objects.filter(stake=self,
                active=True).aggregate(sum=Sum('quantity'))['sum'] or 0)


class Ask(models.Model):
    active = models.BooleanField(default=True)
    price = models.PositiveIntegerField(validators=[MinValueValidator(1),
            MaxValueValidator(1000000000)])

    stake = models.ForeignKey(Stake)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    def get_absolute_url(self) -> str:
        return reverse('project-detail', args=[self.stake.project.slug])
