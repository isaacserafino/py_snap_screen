import datetime
import logging

from django.contrib.auth.models import User
from django.db import models
from django.urls.base import reverse
import dropbox
from paypal.standard.forms import PayPalPaymentsForm
from paypal.standard.ipn.models import PayPalIPN
from paypal.standard.models import ST_PP_COMPLETED
import shortuuid

from web.models import MonthlyLimitService, PaymentNotification, PaymentProfile, InboundIdentityToken, SupervisorId, \
    SupervisorStatus, ViewerConnection
from web.models import PersistenceService
from web.models import SupervisorIdService
from web.models import ViewerConnectionService
from web.models import ViewerService

logger = logging.getLogger(__name__)

# Persistence Models
class Supervisor(models.Model):
    active = models.BooleanField(default=True)
    premium_expiration = models.DateField(blank=True, null=True)
    inbound_identity_token = models.OneToOneField(User, on_delete=models.CASCADE)
    supervisor_id = models.CharField(max_length=40, unique=True)
    viewer_authentication_key = models.CharField(max_length=80)


class Activity(models.Model):
    supervisor = models.ForeignKey(Supervisor, on_delete=models.CASCADE)
    activity_month = models.DateField()
    activity_count = models.IntegerField(default=0)


# Core service business objects
class PayPalPaymentNotification(PaymentNotification):
    def __init__(self, notification: PayPalIPN):
        self.notification = notification

    def get_supervisor_id(self) -> SupervisorId:
        return SupervisorId(self.notification.custom)

    def validate(self) -> bool:
        return (self.notification.payment_status == ST_PP_COMPLETED and self.notification.receiver_email 
                == 'i@findmercy.com' and self.notification.business == 'i@findmercy.com' and self.notification.amount
                == '5.00' and self.notification.currency_code == 'USD')


class PayPalPaymentProfile(PaymentProfile):
    def __init__(self, configuration: dict):
        self.configuration = configuration

    def retrieve_form(self, supervisor_id: SupervisorId) -> str:
        configuration = self.configuration
        configuration['notify_url'] += reverse('paypal-ipn')
        configuration['custom'] = supervisor_id.value

        form = PayPalPaymentsForm(button_type=PayPalPaymentsForm.SUBSCRIBE, initial=configuration)

        return form.render()


class DjangoInboundIdentityToken(InboundIdentityToken):
    def __init__(self, django_user: User):
        self.django_user = django_user

    def create_supervisor(self, supervisor_model, supervisor_id: SupervisorId) -> None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('DjangoInboundIdentityToken.create_supervisor(supervisor_model="' + repr(supervisor_model)
                    + '", supervisor_id(.value)="' + supervisor_id.value + '"), self.django_user="'
                    + repr(self.django_user) + '"')

        supervisor_model.objects.create(active=True, inbound_identity_token=self.django_user,
                supervisor_id=supervisor_id.value)

    # TODO: (IMS) Implement this method:
    def retrieve_supervisor_status(self) -> SupervisorStatus:
        pass

    def save_supervisor(self) -> None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('DjangoInboundIdentityToken.save_supervisor(), self.django_user="' + repr(self.django_user)
                    + '"')
 
        self.django_user.supervisor.save()

    def update_viewer_connection(self, viewer_connection: ViewerConnection) -> None:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('DjangoInboundIdentityToken.update_viewer_connection(viewer_connection(.authorization_token)="'
                    + viewer_connection.authorization_token +'"), self.django_user="' + repr(self.django_user) + '"')

        self.django_user.supervisor.viewer_authentication_key = viewer_connection.authorization_token
        self.save_supervisor()

class CoreServiceFactory:
    core_monthly_limit_service = datetime.date
    core_persistence_service = Activity
    core_persistence_service2 = Supervisor
    core_supervisor_id_service = shortuuid.ShortUUID()
    core_viewer_service = dropbox.Dropbox
    core_viewer_connection_service = dropbox.DropboxOAuth2Flow
    
    def createMonthlyLimitService(self) -> MonthlyLimitService:
        return MonthlyLimitService(self.core_monthly_limit_service)
    
    def createPersistenceService(self) -> PersistenceService:
        return PersistenceService(self.core_persistence_service, self.core_persistence_service2)

    def createSupervisorIdService(self) -> SupervisorIdService:
        return SupervisorIdService(self.core_supervisor_id_service)

    def createViewerService(self) -> ViewerService:
        return ViewerService(self.core_viewer_service)

    def createViewerConnectionService(self) -> ViewerConnectionService:
        return ViewerConnectionService(self.core_viewer_connection_service)


factory = CoreServiceFactory()
monthly_limit_service = factory.createMonthlyLimitService()
persistence_service = factory.createPersistenceService()
viewer_service = factory.createViewerService()
supervisor_id_service = factory.createSupervisorIdService()
viewer_connection_service = factory.createViewerConnectionService()
