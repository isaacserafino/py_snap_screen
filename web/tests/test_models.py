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
from unittest.mock import MagicMock

class PersistenceServiceTest(TestCase):
    STUB_ACTIVE = True
    STUB_AUTHORIZATION_TOKEN = "stub_authorization_token"
    STUB_SUPERVISOR_ID_VALUE = "3oe2UAP"

    connection = ViewerConnection(STUB_ACTIVE, STUB_AUTHORIZATION_TOKEN)
    supervisor_id = SupervisorId(STUB_SUPERVISOR_ID_VALUE)

    def setup(self):
        self.candidate = mock_factory.createPersistenceService()

    def test_save_viewer_connection(self):
        self.setup()

        self.candidate.save_viewer_connection(self.connection, self.supervisor_id)
        
        mock_factory.mock_persistence_service.assert_called_once_with(active=self.STUB_ACTIVE, supervisor_id=self.STUB_SUPERVISOR_ID_VALUE, viewer_authentication_key=self.STUB_AUTHORIZATION_TOKEN)
        mock_factory.mock_persistence_service.return_value.save.assert_called_once_with()

    def test_retrieve_viewer_connection(self):
        self.setup()

        mock_factory.mock_persistence_service.objects.get.return_value = mock.MagicMock(active=self.STUB_ACTIVE, viewer_authentication_key=self.STUB_AUTHORIZATION_TOKEN)

        actual_connection = self.candidate.retrieve_viewer_connection(self.supervisor_id)

        self.assertEqual(self.STUB_ACTIVE, actual_connection.active)
        self.assertEqual(self.STUB_AUTHORIZATION_TOKEN, actual_connection.authorization_token)


class SupervisorIdServiceTest(TestCase):
    STUB_SUPERVISOR_ID_VALUE = "3oe2UAP"

    def setup(self):
        self.candidate = mock_factory.createSupervisorIdService()
        
    def test_generate(self):
        self.setup()

        mock_factory.mock_supervisor_id_service.return_value.random.return_value = self.STUB_SUPERVISOR_ID_VALUE

        supervisor_id = self.candidate.generate()
        
        self.assertEqual(self.STUB_SUPERVISOR_ID_VALUE, supervisor_id.value)


class ViewerConnectionServiceTest(TestCase):
    STUB_AUTHORIZATION_URI = "https://www.example.com/stub_authorization_uri"
    STUB_QUERY_PARAMS = {}

    def setup(self):
        self.candidate = mock_factory.createViewerConnectionService()

    # TODO: Extract flow object creation into own test, use mock for these
    def test_start_creating_connection(self):
        self.setup()

        mock_factory.mock_viewer_connection_service.return_value.start.return_value = self.STUB_AUTHORIZATION_URI
        authorization_uri = self.candidate.start_creating_connection(self.candidate.create_flow_object(None, None, None, None, None))
        
        self.assertEqual(self.STUB_AUTHORIZATION_URI, authorization_uri)

    def test_finish_creating_connection(self):
        self.setup()

        self.candidate.finish_creating_connection(self.STUB_QUERY_PARAMS, self.candidate.create_flow_object(None, None, None, None, None))

        mock_factory.mock_viewer_connection_service.return_value.finish.assert_called_once_with(self.STUB_QUERY_PARAMS)


class ViewerServiceTest(TestCase):
    STUB_AUTHORIZATION_TOKEN = "stub_authorization_token"
    STUB_CONTENTS = "stub_contents".encode()
    STUB_FILENAME = "/stub_filename.txt"

    activity = Activity(STUB_FILENAME, STUB_CONTENTS)
    connection = ViewerConnection(True, STUB_AUTHORIZATION_TOKEN)

    def setup(self):
        self.candidate = mock_factory.createViewerService()

    def test_send_activity(self):
        self.setup()

        self.candidate.send_activity(self.activity, self.connection)
        
        mock_factory.mock_viewer_service.assert_called_once_with(self.STUB_AUTHORIZATION_TOKEN)
        mock_factory.mock_viewer_service.return_value.files_upload.assert_called_once_with(self.STUB_CONTENTS, self.STUB_FILENAME)


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
