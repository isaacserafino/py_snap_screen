from django.test import TestCase

from web import core
from web.models import Activity
from web.models import PersistenceService
from web.models import SupervisorId
from web.models import SupervisorIdService
from web.models import ViewerConnection
from web.models import ViewerConnectionService
from web.models import ViewerService
from py_snap_screen import settings

# TODO: (IMS) Change from service tests to view tests

class PersistenceServiceTest(TestCase):
    STUB_ACTIVE = True
    STUB_AUTHORIZATION_TOKEN = "stub_authorization_token"
    STUB_SUPERVISOR_ID_VALUE = "3oe2UAP"

    connection = ViewerConnection(STUB_ACTIVE, STUB_AUTHORIZATION_TOKEN)
    supervisor_id = SupervisorId(STUB_SUPERVISOR_ID_VALUE)

    def setup(self):
        self.candidate = core_service_factory.createPersistenceService()

    def test_save_viewer_connection(self):
        self.setup()

        self.candidate.save_viewer_connection(self.connection, self.supervisor_id)
        
        supervisor = core_service_factory.core_persistence_service.objects.get(supervisor_id=self.STUB_SUPERVISOR_ID_VALUE)

        self.assertEqual(self.STUB_ACTIVE, supervisor.active)
        self.assertEqual(self.STUB_AUTHORIZATION_TOKEN, supervisor.viewer_authentication_key)
        self.assertEqual(self.STUB_SUPERVISOR_ID_VALUE, supervisor.supervisor_id)

    def test_retrieve_viewer_connection(self):
        self.setup()

        supervisor = core_service_factory.core_persistence_service(active=self.STUB_ACTIVE, supervisor_id=self.STUB_SUPERVISOR_ID_VALUE, viewer_authentication_key=self.STUB_AUTHORIZATION_TOKEN)
        supervisor.save()

        actual_connection = self.candidate.retrieve_viewer_connection(self.supervisor_id)

        self.assertEqual(self.connection.active, actual_connection.active)
        self.assertEqual(self.connection.authorization_token, actual_connection.authorization_token)


class SupervisorIdServiceTest(TestCase):
    def setup(self):
        self.candidate = core_service_factory.createSupervisorIdService()
        
    def test_generate(self):
        self.setup()

        supervisor_id = self.candidate.generate()
        self.assertEqual(7, len(supervisor_id.value))


class ViewerConnectionServiceTest(TestCase):
    pass


class ViewerServiceTest(TestCase):
    # TODO: (IMS) Protect this actual live value
    AUTHORIZATION_TOKEN = settings.TEST_AUTHORIZATION_TOKEN
    STUB_CONTENTS = "stub_contents".encode()
    STUB_FILENAME = "/stub_filename.txt"

    activity = Activity(STUB_FILENAME, STUB_CONTENTS)
    connection = ViewerConnection(True, AUTHORIZATION_TOKEN)

    def setup(self):
        self.candidate = core_service_factory.createViewerService()

    def test_send_activity(self):
        self.setup()

        self.candidate.send_activity(self.activity, self.connection)
        
        api = core_service_factory.core_viewer_service(self.AUTHORIZATION_TOKEN)
        metadata, resource = api.files_download(self.STUB_FILENAME)

        self.assertEqual(self.STUB_CONTENTS, resource.content)

        api.files_delete(self.STUB_FILENAME)


core_service_factory = core.CoreServiceFactory()