from django.apps import AppConfig

from py_snap_screen import settings
from web import signals, views
from web.signals import PaymentSignal
from web.views import PaymentService
from web.core import PayPalPaymentProfile


class WebConfig(AppConfig):
    name = 'web'

    def ready(self):
        AppConfig.ready(self)

        payment_profile = PayPalPaymentProfile(settings.PAYPAL_PROFILE)

        payment_service = PaymentService(payment_profile)
        signals.payment_service = payment_service
        views.payment_service = payment_service

        self.payment_signal = PaymentSignal()
        self.payment_signal.setup()
