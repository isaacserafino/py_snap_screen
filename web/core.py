from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

import dropbox
import shortuuid

from web.models import PersistenceService
from web.models import SupervisorIdService
from web.models import ViewerConnectionService
from web.models import ViewerService
from social_django.models import UserSocialAuth

# Persistence Model
class Supervisor(models.Model):
    active = models.BooleanField(default=True)
    inbound_identity_token = models.OneToOneField(User, on_delete=models.CASCADE)
    supervisor_id = models.CharField(max_length=40, unique=True)
    viewer_authentication_key = models.CharField(max_length=80)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        supervisor_id = shortuuid.ShortUUID().random(length=7)

        Supervisor.objects.create(active=True, inbound_identity_token=instance, supervisor_id=supervisor_id)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.supervisor.save()


@receiver(post_save, sender=UserSocialAuth)
def save_user(sender, instance, **kwargs):
    supervisor = instance.user.supervisor
    supervisor.viewer_authentication_key=instance.extra_data['access_token']

    supervisor.save()


class CoreServiceFactory:
    core_persistence_service = Supervisor
    core_supervisor_id_service = shortuuid.ShortUUID()
    core_viewer_service = dropbox.Dropbox
    core_viewer_connection_service = dropbox.DropboxOAuth2Flow
    
    def createPersistenceService(self):
        return PersistenceService(self.core_persistence_service)

    def createSupervisorIdService(self):
        return SupervisorIdService(self.core_supervisor_id_service)

    def createViewerService(self):
        return ViewerService(self.core_viewer_service)

    def createViewerConnectionService(self):
        return ViewerConnectionService(self.core_viewer_connection_service)