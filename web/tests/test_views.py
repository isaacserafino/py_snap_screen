from unittest import mock, TestCase

from web.tests import stubs
from web.views import MonitoringView, ViewerConnectionCallbackView


# TODO: Implement
class AdministrationViewTest(TestCase):
    def setUp(self):
        pass


class MonitoringViewTest(TestCase):
    def setUp(self):
        self.candidate = MonitoringView()

    @mock.patch("web.views.monitoring_service", autospec=True)
    def test_post(self, mock_monitoring_service):
        self._test_post(stubs.FILENAME, stubs.SUPERVISOR_ID_VALUE)

        mock_monitoring_service.track_activity.assert_called_once()
        (captured_snap, captured_supervisor_id), _ = mock_monitoring_service.track_activity.call_args
        ''':
        :type captured_supervisor_id: SupervisorId
        :type captured_snap: Snap
        '''

        self.assertEqual(stubs.FILENAME, captured_snap.filename)
        self.assertEqual(stubs.CONTENTS, captured_snap.image)
        self.assertEqual(stubs.SUPERVISOR_ID_VALUE, captured_supervisor_id.value)

    @mock.patch("web.views.monitoring_service", autospec=True)
    def test_post_filename_injection(self, mock_monitoring_service):
        self._test_post('next_600001.jpg', stubs.SUPERVISOR_ID_VALUE)

        mock_monitoring_service.track_activity.assert_not_called()

    @mock.patch("web.views.monitoring_service", autospec=True)
    def test_post_supervisor_id_injection(self, mock_monitoring_service):
        self._test_post(stubs.FILENAME, "' OR 1--")

        mock_monitoring_service.track_activity.assert_not_called()

    def _test_post(self, with_filename, with_supervisor_id_value):
        STUB_FILE = mock.MagicMock(read=lambda:stubs.CONTENTS)
        # Must be assigned afterward because otherwise MagicMock itself provides a conflicting "name".
        STUB_FILE.name = with_filename

        STUB_REQUEST = mock.MagicMock(POST={'supervisor_id':with_supervisor_id_value}, FILES={'activity':STUB_FILE})
        self.candidate.dispatch(STUB_REQUEST)


class ViewerConnectionCallbackViewTest(TestCase):
    def setUp(self):
        self.candidate = ViewerConnectionCallbackView()

    # TODO: Finish
    @mock.patch("web.views.administration_service", autospec=True)
    def test_get(self, mock_administration_service):
        self.candidate.get(mock.MagicMock(GET={}, session={}));

        mock_administration_service.retrieve_supervisor_id.assert_called_once()
