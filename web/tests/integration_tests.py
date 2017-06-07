from django.test import TestCase

from py_snap_screen import settings
from web import core
from web.models import Activity
from web.models import PersistenceService
from web.models import SupervisorId
from web.models import SupervisorIdService
from web.models import ViewerConnection
from web.models import ViewerConnectionService
from web.models import ViewerService
from web.tests import stubs
from web.views import AdministrationService

# TODO: (IMS) Change from service tests to view tests

class PersistenceServiceTest(TestCase):
    def setUp(self):
        self.candidate = core_service_factory.createPersistenceService()

    def test_save_viewer_connection(self):
        self.candidate.save_viewer_connection(stubs.CONNECTION, stubs.SUPERVISOR_ID)
        
        supervisor = core_service_factory.core_persistence_service.objects.get(supervisor_id=stubs.SUPERVISOR_ID_VALUE)

        self.assertEqual(stubs.ACTIVE, supervisor.active)
        self.assertEqual(stubs.AUTHORIZATION_TOKEN, supervisor.viewer_authentication_key)
        self.assertEqual(stubs.SUPERVISOR_ID_VALUE, supervisor.supervisor_id)

    def test_retrieve_viewer_connection(self):
        supervisor = core_service_factory.core_persistence_service(active=stubs.ACTIVE, supervisor_id=stubs.SUPERVISOR_ID_VALUE, viewer_authentication_key=stubs.AUTHORIZATION_TOKEN)
        supervisor.save()

        actual_connection = self.candidate.retrieve_viewer_connection(stubs.SUPERVISOR_ID)

        self.assertEqual(stubs.ACTIVE, actual_connection.active)
        self.assertEqual(stubs.AUTHORIZATION_TOKEN, actual_connection.authorization_token)


class SupervisorIdServiceTest(TestCase):
    def setUp(self):
        self.candidate = core_service_factory.createSupervisorIdService()
        
    def test_generate(self):
        supervisor_id = self.candidate.generate()
        self.assertEqual(7, len(supervisor_id.value))


class AdministrationServiceTest(TestCase):
    def setUp(self):
        persistence_service = core_service_factory.createPersistenceService()
        supervisor_id_service = core_service_factory.createSupervisorIdService()
        viewer_connection_service = core_service_factory.createViewerConnectionService()
        self.candidate = AdministrationService(persistence_service, supervisor_id_service, viewer_connection_service)

    def test_start_creating_supervisor_id(self):
        session = {}
        authorization_url = self.candidate.start_creating_supervisor_id(session)
        
        self.assertTrue(authorization_url.startswith("https://www.dropbox.com/oauth2/authorize?response_type=code&client_id=" + settings.DROPBOX_API_KEY + "&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Fviewer-connection-callback%2F&state="))
        self.assertIn("dropbox-auth-csrf-token", session)

    # TODO: Is it feasible or desireable to test the callback?


class ViewerServiceTest(TestCase):
    AUTHORIZATION_TOKEN = settings.TEST_AUTHORIZATION_TOKEN
    connection = ViewerConnection(True, AUTHORIZATION_TOKEN)

    def setUp(self):
        self.candidate = core_service_factory.createViewerService()

    def test_send_activity(self):
        self.candidate.send_activity(stubs.ACTIVITY, self.connection)

        api = core_service_factory.core_viewer_service(self.AUTHORIZATION_TOKEN)
        metadata, resource = api.files_download(stubs.CORE_FILENAME)

        self.assertEqual(stubs.CONTENTS, resource.content)

    def tearDown(self):
        api = core_service_factory.core_viewer_service(self.AUTHORIZATION_TOKEN)
        api.files_delete(stubs.CORE_FILENAME)


core_service_factory = core.CoreServiceFactory()