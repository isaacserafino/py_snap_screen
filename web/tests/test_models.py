import datetime
from unittest import TestCase
from unittest import mock, skip

import dropbox
import shortuuid

from web import core
from web.models import MonthlyLimitService
from web.models import PersistenceService
from web.models import SupervisorIdService
from web.models import ViewerConnectionService
from web.models import ViewerService
from web.tests import stubs


class MonthlyLimitServiceTest(TestCase):
    def setUp(self):
        self.candidate = mock_factory.createMonthlyLimitService()

    def test_retrieve_current_month(self):
        mock_factory.mock_monthly_limit_service.today.return_value = stubs.TODAY

        actual_month = self.candidate.retrieve_current_month()

        self.assertEqual(stubs.MONTH, actual_month)

    def test_determine_whether_current_date_before(self):
        mock_factory.mock_monthly_limit_service.today.return_value = stubs.TODAY

        actual_determination = self.candidate.determine_whether_current_date_before(
                stubs.PREMIUM_EDITION_EXPIRATION_DATE)

        self.assertTrue(actual_determination)


class PersistenceServiceTest(TestCase):
    def setUp(self):
        self.candidate = mock_factory.createPersistenceService()

    def test_save_viewer_connection(self):
        self.candidate.save_viewer_connection(stubs.CONNECTION, stubs.SUPERVISOR_ID)
        
        mock_factory.mock_persistence_service2.assert_called_once_with(active=stubs.ACTIVE,
                supervisor_id=stubs.SUPERVISOR_ID_VALUE, viewer_authentication_key=stubs.AUTHORIZATION_TOKEN)
        
        mock_factory.mock_persistence_service2.return_value.save.assert_called_once_with()

    def test_retrieve_viewer_connection(self):
        mock_factory.mock_persistence_service2.objects.get.return_value = mock.MagicMock(active=stubs.ACTIVE,
            viewer_authentication_key=stubs.AUTHORIZATION_TOKEN)

        actual_connection = self.candidate.retrieve_viewer_connection(stubs.SUPERVISOR_ID)

        self.assertEqual(stubs.ACTIVE, actual_connection.active)
        self.assertEqual(stubs.AUTHORIZATION_TOKEN, actual_connection.authorization_token)

    # TODO: Broken
    @skip('Viewer connections are now created within Supervisors by a signal from framework user creation')
    def test_retrieve_supervisor_by_inbound_identity_token(self):
        mock_factory.mock_persistence_service2.objects.get.return_value = mock.MagicMock(active=stubs.ACTIVE,
                premium_expiration=stubs.PREMIUM_EDITION_EXPIRATION_DATE, supervisor_id=stubs.SUPERVISOR_ID_VALUE,
                viewer_authentication_key=stubs.AUTHORIZATION_TOKEN)

        stub_user = stubs.FRAMEWORK_USER_FUNCTION()
        actual_supervisor = self.candidate.retrieve_supervisor_by_inbound_identity_token(stub_user)

        mock_factory.mock_persistence_service2.objects.get.assert_called_once_with(inbound_identity_token=stub_user)
        self.assertEqual(stubs.ACTIVE, actual_supervisor.active)
        self.assertEqual(stubs.PREMIUM_EDITION_EXPIRATION_DATE, actual_supervisor.premium_expiration)
        self.assertEqual(stubs.SUPERVISOR_ID_VALUE, actual_supervisor.supervisor_id.value)
        self.assertEqual(stubs.AUTHORIZATION_TOKEN, actual_supervisor.viewer_connection.authorization_token)

    def test_retrieve_supervisor_status_by_supervisor_id(self):
        mock_factory.mock_persistence_service2.objects.get.return_value = mock.MagicMock(active=stubs.ACTIVE,
                premium_expiration=stubs.PREMIUM_EDITION_EXPIRATION_DATE, supervisor_id=stubs.SUPERVISOR_ID_VALUE,
                viewer_authentication_key=stubs.AUTHORIZATION_TOKEN)

        actual_supervisor = self.candidate.retrieve_supervisor_status_by_supervisor_id(stubs.SUPERVISOR_ID)

        mock_factory.mock_persistence_service2.objects.get.assert_called_once_with(
                supervisor_id=stubs.SUPERVISOR_ID_VALUE)

        self.assertEqual(stubs.ACTIVE, actual_supervisor.active)
        self.assertEqual(stubs.PREMIUM_EDITION_EXPIRATION_DATE, actual_supervisor.premium_expiration)
        self.assertEqual(stubs.SUPERVISOR_ID_VALUE, actual_supervisor.supervisor_id.value)
        self.assertEqual(stubs.AUTHORIZATION_TOKEN, actual_supervisor.viewer_connection.authorization_token)

    def test_retrieve_activity_count(self):
        mock_factory.mock_persistence_service.objects.get.return_value = mock.MagicMock(
                activity_count=stubs.ACTIVITY_COUNT)

        actual_count = self.candidate.retrieve_activity_count(stubs.SUPERVISOR_ID, stubs.MONTH)

        mock_factory.mock_persistence_service.objects.get.assert_called_once_with(
                supervisor__supervisor_id=stubs.SUPERVISOR_ID_VALUE, activity_month=stubs.MONTH)

        self.assertEqual(stubs.ACTIVITY_COUNT, actual_count)

    @mock.patch('web.models.F', autospec=True)
    def test_increment_activity_count_existing(self, mock_f):
        mock_activity_model = mock.MagicMock()
        mock_factory.mock_persistence_service.objects.filter.return_value = mock_activity_model
        mock_f.return_value = stubs.ACTIVITY_COUNT

        self.candidate.increment_activity_count(stubs.SUPERVISOR_ID, stubs.MONTH)

        mock_factory.mock_persistence_service.objects.filter.assert_called_once_with(
                supervisor__supervisor_id=stubs.SUPERVISOR_ID_VALUE, activity_month=stubs.MONTH)

        mock_f.assert_called_once_with('activity_count')
        mock_activity_model.update.assert_called_once_with(activity_count=stubs.INCREMENTED_ACTIVITY_COUNT)

    def test_increment_activity_count_new(self):
        mock_supervisor_model = mock.MagicMock()

        mock_factory.mock_persistence_service.objects.filter.return_value = False
        mock_factory.mock_persistence_service2.objects.get.return_value = mock_supervisor_model

        self.candidate.increment_activity_count(stubs.SUPERVISOR_ID, stubs.MONTH)

        mock_factory.mock_persistence_service.objects.filter.assert_called_once_with(
                supervisor__supervisor_id=stubs.SUPERVISOR_ID_VALUE, activity_month=stubs.MONTH)

        mock_factory.mock_persistence_service2.objects.get.assert_called_once_with(
                supervisor_id=stubs.SUPERVISOR_ID_VALUE)

        mock_supervisor_model.activity_set.create.assert_called_once_with(activity_month=stubs.MONTH, activity_count=1)


class SupervisorIdServiceTest(TestCase):
    def setUp(self):
        self.candidate = mock_factory.createSupervisorIdService()
        
    def test_generate(self):
        mock_factory.mock_supervisor_id_service.return_value.random.return_value = stubs.SUPERVISOR_ID_VALUE

        supervisor_id = self.candidate.generate()
        
        self.assertEqual(stubs.SUPERVISOR_ID_VALUE, supervisor_id.value)


class ViewerConnectionServiceTest(TestCase):
    def setUp(self):
        self.candidate = mock_factory.createViewerConnectionService()

    def test_create_flow_object(self):
        actual_flow = self.candidate.create_flow_object(stubs.KEY, stubs.SECRET, stubs.CALLBACK_URL, stubs.SESSION,
                stubs.CSRF_TOKEN_ATTRIBUTE_NAME)

        mock_factory.mock_viewer_connection_service.assert_called_once_with(stubs.KEY, stubs.SECRET, stubs.CALLBACK_URL,
                stubs.SESSION, stubs.CSRF_TOKEN_ATTRIBUTE_NAME)

        self.assertEqual(mock_factory.mock_viewer_connection_service.return_value, actual_flow)

    def test_start_creating_connection(self):
        flow = mock.create_autospec(dropbox.DropboxOAuth2Flow)

        flow.start.return_value = stubs.AUTHORIZATION_URL
        authorization_url = self.candidate.start_creating_connection(flow)
        
        self.assertEqual(stubs.AUTHORIZATION_URL, authorization_url)

    def test_finish_creating_connection(self):
        flow = mock.create_autospec(dropbox.DropboxOAuth2Flow)
        flow.finish.return_value = mock.MagicMock(access_token=stubs.AUTHORIZATION_TOKEN)

        actual_connection = self.candidate.finish_creating_connection(stubs.QUERY_PARAMS, flow)

        flow.finish.assert_called_once_with(stubs.QUERY_PARAMS)
        self.assertTrue(actual_connection.active)
        self.assertEqual(stubs.AUTHORIZATION_TOKEN, actual_connection.authorization_token)


class ViewerServiceTest(TestCase):
    def setUp(self):
        self.candidate = mock_factory.createViewerService()

    def test_send_activity(self):
        self.candidate.send_activity(stubs.ACTIVITY, stubs.CONNECTION)
        
        mock_factory.mock_viewer_service.assert_called_once_with(stubs.AUTHORIZATION_TOKEN)
        mock_factory.mock_viewer_service.return_value.files_upload.assert_called_once_with(stubs.CONTENTS,
                stubs.CORE_FILENAME)


class MockCoreServiceFactory:
    @mock.patch("datetime.date", autospec=True)
    def createMonthlyLimitService(self, mock_core):
        self.mock_monthly_limit_service = mock_core
        return MonthlyLimitService(datetime.date)

    @mock.patch("web.core.Supervisor", autospec=True)
    @mock.patch("web.core.Activity", autospec=True)
    def createPersistenceService(self, mock_core, mock_core2):
        self.mock_persistence_service = mock_core
        self.mock_persistence_service2 = mock_core2
        return PersistenceService(core.Activity, core.Supervisor)

    @mock.patch("shortuuid.ShortUUID", autospec=True)
    def createSupervisorIdService(self, mock_core):
        self.mock_supervisor_id_service = mock_core
        id_generator = shortuuid.ShortUUID()
        return SupervisorIdService(id_generator)

    @mock.patch("dropbox.DropboxOAuth2Flow", autospec=True)
    def createViewerConnectionService(self, mock_core):
        self.mock_viewer_connection_service = mock_core
        return ViewerConnectionService(dropbox.DropboxOAuth2Flow)

    @mock.patch("dropbox.Dropbox", autospec=True)
    def createViewerService(self, mock_core):
        self.mock_viewer_service = mock_core
        return ViewerService(dropbox.Dropbox)

mock_factory = MockCoreServiceFactory()
