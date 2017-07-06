from unittest import mock, TestCase

from web.tests import stubs
from web.views import MonitoringView, ViewerConnectionCallbackView, AdministrationView


class AdministrationViewTest(TestCase):
    def setUp(self):
        self.candidate = AdministrationView()

    @mock.patch("web.views.render", autospec=True)
    @mock.patch("web.views.payment_service", autospec=True)
    @mock.patch("web.views.administration_service", autospec=True)
    def test_get(self, mock_administration_service, mock_payment_service, mock_render_function):
        # TODO: (IMS) Figure out and use real inbound_identity_token
        stub_request = mock.MagicMock(user = mock.MagicMock(id = stubs.INBOUND_IDENTITY_TOKEN))
        mock_administration_service.retrieve_dashboard.return_value = stubs.DASHBOARD
        mock_payment_service.retrieve_profile.return_value.retrieve_form.return_value = stubs.PAYMENT_FORM

        self.candidate.get(stub_request)

        mock_administration_service.retrieve_dashboard.assert_called_once_with(stubs.INBOUND_IDENTITY_TOKEN)
        mock_payment_service.retrieve_profile.return_value.retrieve_form.assert_called_once()
        mock_render_function.assert_called_once_with(stub_request, 'supervisor.djhtml', {'dashboard': stubs.DASHBOARD,
                'payment_form': stubs.PAYMENT_FORM})


class MonitoringViewTest(TestCase):
    def setUp(self):
        self.candidate = MonitoringView()

    @mock.patch("web.views.monitoring_service", autospec=True)
    def test_dispatch(self, mock_monitoring_service):
        self._test_dispatch(stubs.FILENAME, stubs.SUPERVISOR_ID_VALUE)

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
        self._test_dispatch('next_600001.jpg', stubs.SUPERVISOR_ID_VALUE)

        mock_monitoring_service.track_activity.assert_not_called()

    @mock.patch("web.views.monitoring_service", autospec=True)
    def test_post_supervisor_id_injection(self, mock_monitoring_service):
        self._test_dispatch(stubs.FILENAME, "' OR 1--")

        mock_monitoring_service.track_activity.assert_not_called()

    def _test_dispatch(self, with_filename, with_supervisor_id_value):
        STUB_FILE = mock.MagicMock(read=lambda:stubs.CONTENTS)
        # Must be assigned afterward because otherwise MagicMock itself provides a conflicting "name".
        STUB_FILE.name = with_filename

        STUB_REQUEST = mock.MagicMock(POST={'supervisor_id':with_supervisor_id_value}, FILES={'activity':STUB_FILE})
        self.candidate.dispatch(STUB_REQUEST)


class ViewerConnectionCallbackViewTest(TestCase):
    def setUp(self):
        self.candidate = ViewerConnectionCallbackView()

    @mock.patch("web.views.render", autospec=True)
    @mock.patch("web.views.administration_service", autospec=True)
    def test_get(self, mock_administration_service, mock_render_function):
        # TODO: (IMS) Figure out and use real inbound_identity_token
        stub_request = mock.MagicMock(user=stubs.INBOUND_IDENTITY_TOKEN)
        mock_administration_service.retrieve_supervisor_id.return_value = stubs.SUPERVISOR_ID

        self.candidate.get(stub_request);

        mock_administration_service.retrieve_supervisor_id.assert_called_once_with(stubs.INBOUND_IDENTITY_TOKEN)
        mock_render_function.assert_called_once_with(stub_request, 'callback.djhtml', {'supervisor_id':
                stubs.SUPERVISOR_ID})
