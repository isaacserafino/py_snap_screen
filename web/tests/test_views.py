from django.test import TestCase
import dropbox
from unittest import mock

from py_snap_screen import settings
from web import views
from web.models import Activity
from web.models import SupervisorId
from web.models import ViewerConnection
from web.models import ViewerConnectionService
from web.models import ViewerService
from web.models import SupervisorIdService
from web.models import PersistenceService
from web.tests import stubs
from web.views import AdministrationService
from web.views import AdministrationView
from web.views import MonitoringService
from web.views import MonitoringView
from web.views import ViewerConnectionCallbackView

# TODO: (IMS) Create your tests here.

# View Tests
class AdministrationViewTest(TestCase):
    def setUp(self):
        pass


class MonitoringViewTest(TestCase):
    def setUp(self):
        pass


class ViewerConnectionCallbackViewTest(TestCase):
    def setUp(self):
        self.candidate = ViewerConnectionCallbackView()

    # TODO: Finish
    @mock.patch("web.views.administration_service", autospec=True)
    def test_post(self, mock_administration_service):
        self.candidate.get(mock.MagicMock(GET={}, session={}));

        mock_administration_service.finish_creating_supervisor_id.assert_called_once()


# Business Service Tests
class AdministrationServiceTest(TestCase):
    @mock.patch("web.views.persistence_service", autospec=True)
    @mock.patch("web.views.supervisor_id_service", autospec=True)
    @mock.patch("web.views.viewer_connection_service", autospec=True)
    def setUp(self, mock_viewer_connection_service, mock_supervisor_id_service, mock_persistence_service):
        self.mock_viewer_connection_service = mock_viewer_connection_service
        self.mock_supervisor_id_service = mock_supervisor_id_service
        self.mock_persistence_service = mock_persistence_service
        self.candidate = AdministrationService(views.persistence_service, views.supervisor_id_service, views.viewer_connection_service)

        self.flow = mock.create_autospec(dropbox.DropboxOAuth2Flow)
        self.mock_viewer_connection_service.create_flow_object.return_value = self.flow

    def test_start_creating_supervisor_id(self):
        session = {}
        
        self.mock_viewer_connection_service.start_creating_connection.return_value = stubs.AUTHORIZATION_URL

        actual_authorization_url = self.candidate.start_creating_supervisor_id(session)
        
        self._assert_created_flow(session)
        self.mock_viewer_connection_service.start_creating_connection.assert_called_once_with(self.flow)
        
        self.assertEqual(stubs.AUTHORIZATION_URL, actual_authorization_url)

    def test_finish_creating_supervisor_id(self):
        callback_parameters = {"state": "xyz"}
        session = {"dropbox-auth-csrf-token": "xyz"}

        self.mock_viewer_connection_service.finish_creating_connection.return_value = stubs.CONNECTION
        self.mock_supervisor_id_service.generate.return_value = stubs.SUPERVISOR_ID

        actual_supervisor_id = self.candidate.finish_creating_supervisor_id(callback_parameters, session)

        self._assert_created_flow(session)
        self.mock_viewer_connection_service.finish_creating_connection.assert_called_once_with(callback_parameters, self.flow)
        self.mock_persistence_service.save_viewer_connection.assert_called_once_with(stubs.CONNECTION, stubs.SUPERVISOR_ID)
        self.assertEqual(stubs.SUPERVISOR_ID, actual_supervisor_id)

    def _assert_created_flow(self, session):
        self.mock_viewer_connection_service.create_flow_object.assert_called_once_with(settings.DROPBOX_API_KEY, settings.DROPBOX_API_SECRET, settings.DROPBOX_CALLBACK_URL, session, "dropbox-auth-csrf-token")


class MonitoringServiceTest(TestCase):
    def setUp(self):
        pass