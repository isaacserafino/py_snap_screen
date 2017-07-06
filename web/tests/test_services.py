from unittest import mock, skip, TestCase

import dropbox

from py_snap_screen import settings
from web import services
from web.services import AdministrationService, MonitoringService, PaymentService
from web.tests import stubs


class AdministrationServiceTest(TestCase):
    @mock.patch("web.services.persistence_service", autospec=True)
    @mock.patch("web.services.supervisor_id_service", autospec=True)
    @mock.patch("web.services.viewer_connection_service", autospec=True)
    @mock.patch("web.services.monthly_limit_service", autospec=True)
    def setUp(self, mock_monthly_limit_service, mock_viewer_connection_service, mock_supervisor_id_service,
            mock_persistence_service):

        self.mock_monthly_limit_service = mock_monthly_limit_service
        self.mock_viewer_connection_service = mock_viewer_connection_service
        self.mock_supervisor_id_service = mock_supervisor_id_service
        self.mock_persistence_service = mock_persistence_service

        self.candidate = AdministrationService(services.monthly_limit_service, services.persistence_service,
                services.supervisor_id_service, services.viewer_connection_service)

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
        self.mock_viewer_connection_service.finish_creating_connection.assert_called_once_with(callback_parameters,
                self.flow)

        self.mock_persistence_service.save_viewer_connection.assert_called_once_with(stubs.CONNECTION,
                stubs.SUPERVISOR_ID)

        self.assertEqual(stubs.SUPERVISOR_ID, actual_supervisor_id)

    def test_retrieve_dashboard(self):
        self.mock_persistence_service.retrieve_supervisor_by_inbound_identity_token.return_value = stubs.SUPERVISOR
        self.mock_monthly_limit_service.retrieve_premium_edition_status.return_value = stubs.PREMIUM_EDITON_STATUS
        self.mock_persistence_service.retrieve_activity_count.return_value = stubs.ACTIVITY_COUNT
        self.mock_monthly_limit_service.retrieve_standard_edition_status.return_value = stubs.STANDARD_EDITION_STATUS

        # TODO: (IMS) Figure out and use correct inbound_identity_token
        actual_dashboard = self.candidate.retrieve_dashboard(1)

        self.mock_persistence_service.retrieve_supervisor_by_inbound_identity_token.assert_called_once_with(1)
        self.mock_monthly_limit_service.retrieve_premium_edition_status.assert_called_once_with(stubs.SUPERVISOR)
        self.mock_persistence_service.retrieve_activity_count.assert_called_once_with(stubs.SUPERVISOR_ID, stubs.MONTH)
        self.mock_monthly_limit_service.retrieve_standard_edition_status.assert_called_once_with(stubs.ACTIVITY_COUNT)

        self.assertFalse(actual_dashboard.premium_edition_active)
        self.assertEqual(stubs.PREMIUM_EDITION_EXPIRATION_DATE, actual_dashboard.premium_edition_expiration)
        self.assertEqual(stubs.ACTIVITY_COUNT, actual_dashboard.standard_edition_status.activity_count)
        self.assertTrue(actual_dashboard.standard_edition_status.activity_within_standard_edition_limit)
        self.assertEqual(stubs.SUPERVISOR_ID, actual_dashboard.supervisor_id)

    # TODO: Broken
    @skip('Viewer connections are now created within Supervisors by a signal from framework user creation')
    def test_retrieve_supervisor(self):
        self.mock_persistence_service.retrieve_supervisor_by_inbound_identity_token.return_value = stubs.SUPERVISOR

        stub_user = stubs.FRAMEWORK_USER_FUNCTION()
        actual_supervisor = self.candidate.retrieve_supervisor(stub_user)

        self.mock_persistence_service.retrieve_supervisor_by_inbound_identity_token.assert_called_once_with(stub_user)
        self.assertEqual(stubs.SUPERVISOR, actual_supervisor)

    def _assert_created_flow(self, session):
        self.mock_viewer_connection_service.create_flow_object.assert_called_once_with(settings.DROPBOX_API_KEY,
                settings.DROPBOX_API_SECRET, settings.DROPBOX_CALLBACK_URL, session, "dropbox-auth-csrf-token")


# TODO: (IMS) Implement
class PaymentServiceTest(TestCase):
    @mock.patch("web.services.persistence_service", autospec=True)
    @mock.patch("web.services.monthly_limit_service", autospec=True)
    def setUp(self, mock_monthly_limit_service, mock_persistence_service):
        self.mock_monthly_limit_service = mock_monthly_limit_service
        self.mock_persistence_service = mock_persistence_service
        self.candidate = PaymentService(None, services.monthly_limit_service, services.persistence_service)


class MonitoringServiceTest(TestCase):
    @mock.patch("web.services.viewer_service", autospec=True)
    @mock.patch('web.services.persistence_service', autospec=True)
    @mock.patch("web.services.monthly_limit_service", autospec=True)
    def setUp(self, mock_monthly_limit_service, mock_persistence_service, mock_viewer_service):
        self.mock_monthly_limit_service = mock_monthly_limit_service
        self.mock_persistence_service = mock_persistence_service
        self.mock_viewer_service = mock_viewer_service
        self.candidate = MonitoringService(services.persistence_service, services.viewer_service,
                services.monthly_limit_service)

    def test_track_activity(self):
        self.mock_persistence_service.retrieve_supervisor_status_by_supervisor_id.return_value = stubs.SUPERVISOR
        self.mock_monthly_limit_service.retrieve_premium_edition_status.return_value = stubs.PREMIUM_EDITON_STATUS
        self.mock_persistence_service.retrieve_activity_count.return_value = stubs.ACTIVITY_COUNT
        self.mock_monthly_limit_service.retrieve_standard_edition_status.return_value = stubs.STANDARD_EDITION_STATUS

        self.candidate.track_activity(stubs.ACTIVITY, stubs.SUPERVISOR_ID)

        self.mock_persistence_service.retrieve_supervisor_status_by_supervisor_id.assert_called_once_with(
                stubs.SUPERVISOR_ID)
        self.mock_monthly_limit_service.retrieve_premium_edition_status.assert_called_once_with(stubs.SUPERVISOR)
        self.mock_persistence_service.retrieve_activity_count.assert_called_once_with(stubs.SUPERVISOR_ID, stubs.MONTH)
        self.mock_monthly_limit_service.retrieve_standard_edition_status.assert_called_once_with(stubs.ACTIVITY_COUNT)

        self.mock_viewer_service.send_activity.assert_called_once_with(stubs.ACTIVITY, stubs.CONNECTION)
        self.mock_persistence_service.increment_activity_count.assert_called_once_with(stubs.SUPERVISOR_ID, stubs.MONTH)
