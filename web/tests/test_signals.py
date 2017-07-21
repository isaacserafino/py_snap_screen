from unittest import TestCase, mock

from paypal.standard.ipn.models import PayPalIPN

from web.signals import PaymentSignal


class PaymentSignalTest(TestCase):
    def setUp(self):
        self.candidate = PaymentSignal()

    @mock.patch('web.signals.valid_ipn_received', autospec=True)
    def test_setup(self, mock_payment_signal) -> None:
        self.candidate.setup()

        mock_payment_signal.connect.assert_called_once_with(self.candidate.receive_payment_notification)

    @mock.patch('web.signals.PayPalPaymentNotification', autospec=True)
    @mock.patch('web.signals.payment_service', autospec=True)
    def test_receive_payment_notification(self, mock_payment_service, mock_payment_notification) -> None:
        mock_core_notification = mock.create_autospec(PayPalIPN)

        self.candidate.receive_payment_notification(mock_core_notification)
        mock_payment_notification.assert_called_once_with(mock_core_notification)
        mock_payment_service.process_notification.assert_called_once_with(mock_payment_notification.return_value)
