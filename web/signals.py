from paypal.standard.ipn.models import PayPalIPN
from paypal.standard.ipn.signals import valid_ipn_received

from web.core import PayPalPaymentNotification
from web.services import payment_service


class PaymentSignal:
    def setup(self):
        valid_ipn_received.connect(self.receive_payment_notification)

    # TODO: (IMS) Need **kwargs?
    def receive_payment_notification(self, sender: PayPalIPN):
        notification = PayPalPaymentNotification(sender)

        # TODO: (IMS) Get Supervisor ID
        supervisor_id = None

        payment_service.process_notification(supervisor_id, notification)
