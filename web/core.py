from django.db import models

import dropbox
import shortuuid

from web.models import PersistenceService
from web.models import SupervisorIdService
from web.models import ViewerConnectionService
from web.models import ViewerService

# Persistence Model
class Supervisor(models.Model):
    active = models.BooleanField(default=True)
    supervisor_id = models.CharField(max_length=40, unique=True)
    viewer_authentication_key = models.CharField(max_length=80)


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