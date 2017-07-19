from unittest import skip

from django.test import TestCase

from py_snap_screen import settings
from web import core
from web.models import ViewerConnection
from web.tests import stubs
from web.services import AdministrationService


# TODO: (IMS) Change from service tests to view tests
class PersistenceServiceTest(TestCase):
    fixtures = ['test_data.json']

    def setUp(self):
        self.candidate = core_service_factory.createPersistenceService()

    @skip('Viewer connections are now created within Supervisors by a signal from framework user creation')
    def test_save_viewer_connection(self):
        self.candidate.save_viewer_connection(stubs.CONNECTION, stubs.SUPERVISOR_ID)
        
        supervisor = core_service_factory.core_persistence_service2.objects.get(supervisor_id=stubs.SUPERVISOR_ID_VALUE)

        self.assertEqual(stubs.ACTIVE, supervisor.active)
        self.assertEqual(stubs.AUTHORIZATION_TOKEN, supervisor.viewer_authentication_key)
        self.assertEqual(stubs.SUPERVISOR_ID_VALUE, supervisor.supervisor_id)

    @skip('Viewer connections are now created within Supervisors by a signal from framework user creation')
    def test_retrieve_viewer_connection(self):
        user = stubs.FRAMEWORK_USER_FUNCTION()
        supervisor = core_service_factory.core_persistence_service2(active=stubs.ACTIVE,
                                                                    supervisor_id=stubs.SUPERVISOR_ID_VALUE,
                                                                    viewer_authentication_key=stubs.AUTHORIZATION_TOKEN,
                                                                    inbound_identity_token=user)
        supervisor.save()

        actual_connection = self.candidate.retrieve_viewer_connection(stubs.SUPERVISOR_ID)

        self.assertEqual(stubs.ACTIVE, actual_connection.active)
        self.assertEqual(stubs.AUTHORIZATION_TOKEN, actual_connection.authorization_token)

    def test_increment_activity_count(self):
#         user = stubs.FRAMEWORK_USER_FUNCTION()
#         supervisor = core_service_factory.core_persistence_service2.objects.get(inbound_identity_token=user)
#         supervisor.supervisor_id = stubs.SUPERVISOR_ID_VALUE
#         supervisor.save()
        supervisor = core_service_factory.core_persistence_service2.objects.get(id=stubs.INBOUND_IDENTITY_TOKEN)

        activity = core_service_factory.core_persistence_service(supervisor=supervisor, activity_month=stubs.MONTH,
                                                                 activity_count=stubs.ACTIVITY_COUNT)

        activity.save()

        self.candidate.increment_activity_count(stubs.SUPERVISOR_ID, stubs.MONTH)

        activity = core_service_factory.core_persistence_service.objects.get(
            supervisor__supervisor_id=stubs.SUPERVISOR_ID_VALUE, activity_month=stubs.MONTH)

        self.assertEqual(stubs.INCREMENTED_ACTIVITY_COUNT, activity.activity_count)


class SupervisorIdServiceTest(TestCase):
    def setUp(self):
        self.candidate = core_service_factory.createSupervisorIdService()
        
    def test_generate(self):
        supervisor_id = self.candidate.generate()
        self.assertEqual(7, len(supervisor_id.value))


class AdministrationServiceTest(TestCase):
    def setUp(self):
        monthly_limit_service = core_service_factory.createMonthlyLimitService()
        persistence_service = core_service_factory.createPersistenceService()
        supervisor_id_service = core_service_factory.createSupervisorIdService()
        viewer_connection_service = core_service_factory.createViewerConnectionService()
        self.candidate = AdministrationService(monthly_limit_service, persistence_service, supervisor_id_service,
                viewer_connection_service)

    def test_start_creating_supervisor_id(self):
        session = {}
        authorization_url = self.candidate.start_creating_supervisor_id(session)
        
        self.assertTrue(authorization_url.startswith(
            "https://www.dropbox.com/oauth2/authorize?response_type=code&client_id=" + settings.DROPBOX_API_KEY
            + "&redirect_uri=http%3A%2F%2F127.0.0.1%3A8000%2Fviewer-connection-callback%2F&state="))
        self.assertIn("dropbox-auth-csrf-token", session)

    # TODO: Is it feasible or desirable to test the callback?


class ViewerServiceTest(TestCase):
    AUTHORIZATION_TOKEN = settings.TEST_AUTHORIZATION_TOKEN
    connection = ViewerConnection(True, AUTHORIZATION_TOKEN)

    def setUp(self):
        self.candidate = core_service_factory.createViewerService()

    def test_send_activity(self):
        self.candidate.send_activity(stubs.ACTIVITY, self.connection)

        api = core_service_factory.core_viewer_service(self.AUTHORIZATION_TOKEN)
        _, resource = api.files_download(stubs.CORE_FILENAME)

        self.assertEqual(stubs.CONTENTS, resource.content)

    def tearDown(self):
        api = core_service_factory.core_viewer_service(self.AUTHORIZATION_TOKEN)
        api.files_delete(stubs.CORE_FILENAME)


core_service_factory = core.CoreServiceFactory()
