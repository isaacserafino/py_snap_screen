from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from osm_web.models import UserProfile
from py_snap_screen import settings


@receiver(post_save, sender=User)
def create_user_profile(sender, instance: User, created: bool, **kwargs):  # @UnusedVariable To support receiver
    if created:
        UserProfile.objects.create(user=instance,
                incentives=settings.DEFAULT_INCENTIVES_PER_USER)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance: User, **kwargs):  # @UnusedVariable To support receiver
    instance.userprofile.save()
