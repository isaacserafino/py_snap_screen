from dropbox.oauth import DropboxOAuth2Flow

from py_snap_screen import settings
from web.core import PayPalPaymentProfile, monthly_limit_service, persistence_service, viewer_service, \
    supervisor_id_service, viewer_connection_service
from web.models import MonthlyLimitService, PaymentNotification, PaymentProfile, Dashboard, InboundIdentityToken,\
    ViewerConnection
from web.models import PersistenceService
from web.models import Snap
from web.models import SupervisorId
from web.models import SupervisorIdService
from web.models import ViewerConnectionService
from web.models import ViewerService


class AdministrationService:
    def __init__(self, monthly_limit_service: MonthlyLimitService, persistence_service: PersistenceService,
                supervisor_id_service: SupervisorIdService, viewer_connection_service: ViewerConnectionService):

        self.monthly_limit_service = monthly_limit_service
        self.persistence_service = persistence_service
        self.supervisor_id_service = supervisor_id_service
        self.viewer_connection_service = viewer_connection_service

    def finish_creating_supervisor_id(self, callback_parameters, session: dict) -> SupervisorId:
        flow = self._create_flow(session)

        connection = self.viewer_connection_service.finish_creating_connection(callback_parameters, flow)
        if connection is None: return None

        supervisor_id = self.supervisor_id_service.generate()
        if supervisor_id is None: return None

        self.persistence_service.save_viewer_connection(connection, supervisor_id)

        return supervisor_id

    def retrieve_dashboard(self, inbound_identity_token) -> Dashboard:
        supervisor_status = self.persistence_service.retrieve_supervisor_by_inbound_identity_token(
                inbound_identity_token)

        premium_edition_status = self.monthly_limit_service.retrieve_premium_edition_status(supervisor_status)

        activity_count = self.persistence_service.retrieve_activity_count(supervisor_status.supervisor_id,
                premium_edition_status.activity_month)

        standard_edition_status = self.monthly_limit_service.retrieve_standard_edition_status(activity_count)

        return Dashboard(premium_edition_status.premium_edition_active, supervisor_status.premium_expiration,
                        standard_edition_status, supervisor_status.supervisor_id) 

    def retrieve_supervisor_id(self, framework_user) -> SupervisorId:
        return SupervisorId(framework_user.supervisor.supervisor_id)

    def start_creating_supervisor_id(self, session: dict) -> str:
        flow = self._create_flow(session)

        return self.viewer_connection_service.start_creating_connection(flow)

    # TODO: (IMS) Test, rename identifiers in these 3 methods:
    def create_viewer_connection(self, framework_user: InboundIdentityToken) -> None:
        supervisor_id = self.supervisor_id_service.generate()
        self.persistence_service.create_supervisor(framework_user, supervisor_id)

    def save_supervisor(self, framework_user: InboundIdentityToken) -> None:
        self.persistence_service.save_supervisor(framework_user)

    def update_connection(self, framework_user: InboundIdentityToken, viewer_authentication_key: ViewerConnection
            ) -> None:
        self.persistence_service.update_connection(framework_user, viewer_authentication_key)

    def _create_flow(self, session: dict) -> DropboxOAuth2Flow:
        return self.viewer_connection_service.create_flow_object(settings.DROPBOX_API_KEY, settings.DROPBOX_API_SECRET,
                                                                 settings.DROPBOX_CALLBACK_URL, session,
                                                                 "dropbox-auth-csrf-token")


class MonitoringService:
    def __init__(self, persistence_service: PersistenceService, viewer_service: ViewerService,
                monthly_limit_service: MonthlyLimitService):
        self.persistence_service = persistence_service
        self.viewer_service = viewer_service
        self.monthly_limit_service = monthly_limit_service

    def track_activity(self, activity: Snap, supervisor_id: SupervisorId) -> None:
        if supervisor_id is None or activity is None: return

        supervisor = self.persistence_service.retrieve_supervisor_status_by_supervisor_id(supervisor_id)
        if supervisor is None or not supervisor.active: return

        premium_status = self.monthly_limit_service.retrieve_premium_edition_status(supervisor)
        if not premium_status.premium_edition_active:
            activity_count = self.persistence_service.retrieve_activity_count(supervisor_id,
                    premium_status.activity_month)

            standard_status = self.monthly_limit_service.retrieve_standard_edition_status(activity_count)

            if not standard_status.activity_within_standard_edition_limit: return

        connection = supervisor.viewer_connection
        if connection is None: return

        self.viewer_service.send_activity(activity, connection)

        self.persistence_service.increment_activity_count(supervisor_id, premium_status.activity_month)


class PaymentService:
    def __init__(self, payment_profile: PaymentProfile, monthly_limit_service: MonthlyLimitService):
        self.payment_profile = payment_profile
        self.monthly_limit_service = monthly_limit_service

    def process_notification(self, payment_notification: PaymentNotification) -> None:
        if payment_notification.validate():
            supervisor_id = payment_notification.get_supervisor_id()
            self.monthly_limit_service.renew_premium_edition_for_one_month(supervisor_id)

    def retrieve_profile(self) -> PaymentProfile:
        return self.payment_profile


monitoring_service = MonitoringService(persistence_service, viewer_service, monthly_limit_service)

administration_service = AdministrationService(monthly_limit_service, persistence_service, supervisor_id_service,
        viewer_connection_service)

payment_profile = PayPalPaymentProfile(settings.PAYPAL_PROFILE)
payment_service = PaymentService(payment_profile, monthly_limit_service)
