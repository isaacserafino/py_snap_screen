from django.apps import AppConfig

from web.signals import PaymentSignal


class WebConfig(AppConfig):
    name = 'web'

    def ready(self):
        AppConfig.ready(self)

        self.payment_signal = PaymentSignal()
        self.payment_signal.setup()
