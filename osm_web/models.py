from abc import abstractmethod
import re

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models.aggregates import Sum
from django.urls.base import reverse
from django_bleach.models import BleachField
from django_extensions.db.fields import AutoSlugField

from py_snap_screen import settings
from django.db.models.expressions import F


class BetterBleachField(BleachField):

    def __init__(self, *args, **kwargs):
        super(BetterBleachField, self).__init__(max_length=256, allowed_tags=[None], strip_tags=True)

    def pre_save(self, model_instance, add):
        ''' Remove HTML entities and ampersands from description before saving. '''
        value = BleachField.pre_save(self, model_instance, add)

        return  re.sub(r'&(([A-Za-z]+|#x[\dA-Fa-f]+|#\d+);)?', '', value)


class Project(models.Model):
    active = models.BooleanField(default=True)
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    description = BetterBleachField()
    slug = AutoSlugField(unique=True, populate_from='description')

    def get_absolute_url(self) -> str:
        return reverse('project-list')

    def count_total_shares(self) -> int:
        return int(self.stake_set.aggregate(sum=Sum('quantity'))['sum'] or 0)


class Stake(models.Model):
    holder = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def calculate_available_shares_to_sell(self) -> int:
        return self.quantity - int(Ask.objects.filter(stake=self,
                active=True).aggregate(sum=Sum('quantity'))['sum'] or 0)


class BidAsk(models.Model):
    active = models.BooleanField(default=True)
    price = models.PositiveIntegerField(validators=[MinValueValidator(1),
            MaxValueValidator(settings.MAX_SHARE_PRICE)],
            help_text="reputation points per share")

    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    def get_absolute_url(self) -> str:
        return reverse('project-detail', args=[self.get_project_slug()])

    @abstractmethod
    def get_project_slug(self) -> str:
        pass

    class Meta:
        abstract = True


class Ask(BidAsk):
    stake = models.ForeignKey(Stake, on_delete=models.CASCADE)

    BidAsk._meta.get_field("quantity").verbose_name = "number of shares to sell"

    def get_project_slug(self) -> str:
        return self.stake.project.slug


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    incentives = models.PositiveIntegerField(validators=[MinValueValidator(1),
            MaxValueValidator(settings.MAX_SHARE_PRICE)])

    slug = AutoSlugField(unique=True, populate_from=('user__first_name', 'user__last_name'))

    def calculate_available_bid_incentives(self) -> int:
        return self.incentives - int(Bid.objects.filter(bidder=self,
                active=True).aggregate(
                sum=Sum(F('price') * F('quantity')))['sum'] or 0)


class Bid(BidAsk):
    bidder = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    BidAsk._meta.get_field("quantity").verbose_name = "number of shares to buy"

    def get_project_slug(self) -> str:
        return self.project.slug


import osm_web.signals  # @UnusedImport Simply to register them 
