from django.test import TestCase
import dropbox
from unittest import mock

from py_snap_screen import settings
from web import views
from web.models import SupervisorId
from web.models import ViewerConnection
from web.models import ViewerConnectionService
from web.models import ViewerService
from web.models import SupervisorIdService
from web.tests import stubs
from web.views import AdministrationService
from web.views import AdministrationView
from web.views import MonitoringService
from web.views import MonitoringView
from web.views import SupervisorStatusService
from web.views import ViewerConnectionCallbackView

# View Tests
# TODO: Implement
class AdministrationViewTest(TestCase):
    def setUp(self):
        pass


class MonitoringViewTest(TestCase):
    def setUp(self):
        self.candidate = MonitoringView()

    @mock.patch("web.views.monitoring_service", autospec=True)
    def test_post(self, mock_monitoring_service):
        STUB_FILE = mock.MagicMock(read=lambda: stubs.CONTENTS)
        # Must be assigned afterward because otherwise MagicMock itself provides a conflicting "name".
        STUB_FILE.name = stubs.FILENAME

        STUB_REQUEST = mock.MagicMock(POST={'supervisor_id':stubs.SUPERVISOR_ID_VALUE}, FILES={'activity':STUB_FILE})
        self.candidate.dispatch(STUB_REQUEST);

        mock_monitoring_service.track_activity.assert_called_once()
        (captured_snap, captured_supervisor_id), _ = mock_monitoring_service.track_activity.call_args

        self.assertEqual(stubs.FILENAME, captured_snap.filename)
        self.assertEqual(stubs.CONTENTS, captured_snap.image)
        self.assertEqual(stubs.SUPERVISOR_ID_VALUE, captured_supervisor_id.value)


class ViewerConnectionCallbackViewTest(TestCase):
    def setUp(self):
        self.candidate = ViewerConnectionCallbackView()

    # TODO: Finish
    @mock.patch("web.views.administration_service", autospec=True)
    def test_get(self, mock_administration_service):
        self.candidate.get(mock.MagicMock(GET={}, session={}));

        mock_administration_service.retrieve_supervisor_id.assert_called_once()


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

    def test_retrieve_supervisor(self):
        self.mock_persistence_service.retrieve_supervisor_by_inbound_identity_token.return_value = stubs.SUPERVISOR

        actual_supervisor = self.candidate.retrieve_supervisor(stubs.INBOUND_IDENTITY_TOKEN)

        self.mock_persistence_service.retrieve_supervisor_by_inbound_identity_token.assert_called_once_with(stubs.INBOUND_IDENTITY_TOKEN)
        self.assertEqual(stubs.SUPERVISOR, actual_supervisor)

    def _assert_created_flow(self, session):
        self.mock_viewer_connection_service.create_flow_object.assert_called_once_with(settings.DROPBOX_API_KEY, settings.DROPBOX_API_SECRET, settings.DROPBOX_CALLBACK_URL, session, "dropbox-auth-csrf-token")


class SupervisorStatusServiceTest(TestCase):
    @mock.patch("web.views.persistence_service", autospec=True)
    @mock.patch("web.views.monthly_limit_service", autospec=True)
    def setUp(self, mock_monthly_limit_service, mock_persistence_service):
        self.mock_monthly_limit_service = mock_monthly_limit_service
        self.mock_persistence_service = mock_persistence_service
        self.candidate = SupervisorStatusService(views.monthly_limit_service, views.persistence_service)

    def test_determine_whether_premium_edition_active(self):
        self.mock_monthly_limit_service.determine_whether_current_date_before.return_value = True

        actual_determination = self.candidate.determine_whether_premium_edition_active(stubs.SUPERVISOR)

        self.mock_monthly_limit_service.determine_whether_current_date_before.assert_called_once_with(stubs.PREMIUM_EDITION_EXPIRATION_DATE)
        self.assertTrue(actual_determination)

    def test_determine_whether_activity_within_standard_edition_limit(self):
        self.mock_monthly_limit_service.retrieve_current_month.return_value = stubs.MONTH
        self.mock_persistence_service.retrieve_activity_count.return_value = stubs.ACTIVITY_COUNT
        actual_determination = self.candidate.determine_whether_activity_within_standard_edition_limit(stubs.SUPERVISOR)

        self.mock_monthly_limit_service.retrieve_current_month.assert_called_once()
        self.mock_persistence_service.retrieve_activity_count.assert_called_once_with(stubs.SUPERVISOR_ID, stubs.MONTH)
        self.assertTrue(actual_determination)

    def test_increment_activity_count(self):
        self.mock_monthly_limit_service.retrieve_current_month.return_value = stubs.MONTH

        self.candidate.increment_activity_count(stubs.SUPERVISOR_ID)

        self.mock_persistence_service.increment_activity_count.assert_called_once_with(stubs.SUPERVISOR_ID, stubs.MONTH)


class MonitoringServiceTest(TestCase):
    @mock.patch("web.views.viewer_service", autospec=True)
    @mock.patch("web.views.persistence_service", autospec=True)
    def setUp(self, mock_persistence_service, mock_viewer_service):
        self.mock_persistence_service = mock_persistence_service
        self.mock_viewer_service = mock_viewer_service
        self.candidate = MonitoringService(views.persistence_service, views.viewer_service)

    @mock.patch("web.views.supervisor_status_service", autospec=True)
    def test_track_activity(self, mock_supervisor_status_service):
        self.mock_persistence_service.retrieve_supervisor_status_by_supervisor_id.return_value = stubs.SUPERVISOR
        mock_supervisor_status_service.determine_whether_premium_edition_active.return_value = False
        mock_supervisor_status_service.determine_whether_activity_within_standard_edition_limit.return_value = True

        self.candidate.track_activity(stubs.ACTIVITY, stubs.SUPERVISOR_ID)

        mock_supervisor_status_service.determine_whether_premium_edition_active.assert_called_once_with(stubs.SUPERVISOR)
        mock_supervisor_status_service.determine_whether_activity_within_standard_edition_limit.assert_called_once_with(stubs.SUPERVISOR)
        self.mock_persistence_service.retrieve_supervisor_status_by_supervisor_id.assert_called_once_with(stubs.SUPERVISOR_ID)
        self.mock_viewer_service.send_activity.assert_called_once_with(stubs.ACTIVITY, stubs.CONNECTION)
        mock_supervisor_status_service.increment_activity_count.assert_called_once_with(stubs.SUPERVISOR_ID)
