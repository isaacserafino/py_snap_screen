from unittest import TestCase
from unittest import mock

import dropbox
import shortuuid

from web import core
from web.models import Activity
from web.models import PersistenceService
from web.models import SupervisorId
from web.models import SupervisorIdService
from web.models import ViewerConnection
from web.models import ViewerConnectionService
from web.models import ViewerService
from web.tests import stubs

class PersistenceServiceTest(TestCase):
    def setUp(self):
        self.candidate = mock_factory.createPersistenceService()

    def test_save_viewer_connection(self):
        self.candidate.save_viewer_connection(stubs.CONNECTION, stubs.SUPERVISOR_ID)
        
        mock_factory.mock_persistence_service.assert_called_once_with(active=stubs.ACTIVE, supervisor_id=stubs.SUPERVISOR_ID_VALUE, viewer_authentication_key=stubs.AUTHORIZATION_TOKEN)
        mock_factory.mock_persistence_service.return_value.save.assert_called_once_with()

    def test_retrieve_viewer_connection(self):
        mock_factory.mock_persistence_service.objects.get.return_value = mock.MagicMock(active=stubs.ACTIVE, viewer_authentication_key=stubs.AUTHORIZATION_TOKEN)

        actual_connection = self.candidate.retrieve_viewer_connection(stubs.SUPERVISOR_ID)

        self.assertEqual(stubs.ACTIVE, actual_connection.active)
        self.assertEqual(stubs.AUTHORIZATION_TOKEN, actual_connection.authorization_token)


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
        actual_flow = self.candidate.create_flow_object(stubs.KEY, stubs.SECRET, stubs.CALLBACK_URL, stubs.SESSION, stubs.CSRF_TOKEN_ATTRIBUTE_NAME)

        mock_factory.mock_viewer_connection_service.assert_called_once_with(stubs.KEY, stubs.SECRET, stubs.CALLBACK_URL, stubs.SESSION, stubs.CSRF_TOKEN_ATTRIBUTE_NAME) 
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
        mock_factory.mock_viewer_service.return_value.files_upload.assert_called_once_with(stubs.CONTENTS, stubs.CORE_FILENAME)


class MockCoreServiceFactory: 
    @mock.patch("web.core.Supervisor", autospec=True)
    def createPersistenceService(self, mock_core):
        self.mock_persistence_service = mock_core
        return PersistenceService(core.Supervisor)

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
