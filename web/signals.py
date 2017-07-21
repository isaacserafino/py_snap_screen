from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from paypal.standard.ipn.models import PayPalIPN
from paypal.standard.ipn.signals import valid_ipn_received
from social_django.models import UserSocialAuth

from web.core import PayPalPaymentNotification, DjangoInboundIdentityToken
from web.services import payment_service, administration_service
from web.models import ViewerConnection


class PaymentSignal:
    def setup(self):
        valid_ipn_received.connect(self.receive_payment_notification)

    # TODO: (IMS) Need **kwargs?
    def receive_payment_notification(self, sender: PayPalIPN, **kwargs):  # @UnusedVariable Because this method is a
            # signal receiver
        notification = PayPalPaymentNotification(sender)

        payment_service.process_notification(notification)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance: User, created: bool, **kwargs):  # @UnusedVariable Because this method is an
        # override

    if created: administration_service.create_viewer_connection(DjangoInboundIdentityToken(instance))

@receiver(post_save, sender=User)
def save_user_profile(sender, instance: User, **kwargs):  # @UnusedVariable Because this method is an override
    administration_service.save_supervisor(DjangoInboundIdentityToken(instance))

@receiver(post_save, sender=UserSocialAuth)
def save_user(sender, instance:UserSocialAuth, **kwargs):  # @UnusedVariable Because this method is an override
    if 'access_token' in instance.extra_data:
            administration_service.update_connection(DjangoInboundIdentityToken(instance.user), ViewerConnection(True,
                    instance.extra_data['access_token']))
