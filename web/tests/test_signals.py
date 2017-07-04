from unittest import TestCase, mock

from paypal.standard.ipn.models import PayPalIPN

from web.signals import PaymentSignal


class PaymentSignalTest(TestCase):
    def setUp(self):
        self.candidate = PaymentSignal()

    @mock.patch('web.signals.valid_ipn_received', autospec=True)
    def test_setup(self, mock_payment_signal):
        self.candidate.setup()

        mock_payment_signal.connect.assert_called_once_with(self.candidate.receive_payment_notification)

    # TODO: (IMS) Implement test
    def test_receive_payment_notification(self):
        mock_notification = mock.create_autospec(PayPalIPN)

        self.candidate.receive_payment_notification(mock_notification)
