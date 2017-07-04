import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.views.generic import View
from dropbox.oauth import DropboxOAuth2Flow

from py_snap_screen import settings
from web import core
from web.models import MonthlyLimitService, PaymentNotification, PaymentProfile
from web.models import PersistenceService
from web.models import Snap
from web.models import SupervisorId
from web.models import SupervisorIdService
from web.models import SupervisorStatus
from web.models import ViewerConnectionService
from web.models import ViewerService


# Views
class AdministrationView(LoginRequiredMixin, TemplateView):
    template_name = "supervisor.djhtml"

    def get(self, request, *args, **kwargs):  # @UnusedVariable Because this method is an override
        supervisor_status = administration_service.retrieve_supervisor(request.user.id);
        premium_edition_active = supervisor_status_service.determine_whether_premium_edition_active(supervisor_status)

        activity_within_standard_edition_limit = \
                supervisor_status_service.determine_whether_activity_within_standard_edition_limit(supervisor_status)

        payment_profile = payment_service.retrieve_profile()
        ': :type payment_profile: PaymentProfile'

        payment_form = payment_profile.retrieve_form()

        model = {'supervisor_status':supervisor_status, 'premium_edition_active': premium_edition_active,
                 'activity_within_standard_edition_limit': activity_within_standard_edition_limit,
                 'payment_form': payment_form}

        return render(request, self.template_name, model)


class LoginView(TemplateView):
    template_name = "login.djhtml"


class MonitoringView(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if not ("supervisor_id" in request.POST or "activity" in request.FILES):
                return View.dispatch(self, request, *args, **kwargs)

        supervisor_id_value = request.POST["supervisor_id"]
        ': :type supervisor_id_value: str'

        if not (len(supervisor_id_value) == 7 and supervisor_id_value.isalnum()):
                return View.dispatch(self, request, *args, **kwargs)

        file = request.FILES["activity"]

        filename = file.name
        ': :type filename: str'

        filename_match = re.fullmatch(r'next_(?P<interval>\d+)\.jpg', filename)

        if filename_match is None or not (1 <= int(filename_match.group('interval')) <= 600000):
                return View.dispatch(self, request, *args, **kwargs)

        # TODO: Use chunks?
        activity_value = file.read()
        ': :type activity_value: bytes'

        activity = Snap(filename, activity_value)
        supervisor_id = SupervisorId(supervisor_id_value)

        monitoring_service.track_activity(activity, supervisor_id)

        return redirect('/')


class ViewerConnectionCallbackView(LoginRequiredMixin, TemplateView):
    template_name = "callback.djhtml"

    def get(self, request, *args, **kwargs):  # @UnusedVariable Because this method is an override
        supervisor_id = administration_service.retrieve_supervisor_id(request.user)

        return render(request, self.template_name, {'supervisor_id': supervisor_id})


# Business Services
class AdministrationService:
    def __init__(self, persistence_service: PersistenceService, supervisor_id_service: SupervisorIdService,
                 viewer_connection_service: ViewerConnectionService):

        self.persistence_service = persistence_service
        self.supervisor_id_service = supervisor_id_service
        self.viewer_connection_service = viewer_connection_service

    def finish_creating_supervisor_id(self, callback_parameters, session: dict):
        flow = self._create_flow(session)

        connection = self.viewer_connection_service.finish_creating_connection(callback_parameters, flow)
        if connection is None: return None

        supervisor_id = self.supervisor_id_service.generate()
        if supervisor_id is None: return None

        self.persistence_service.save_viewer_connection(connection, supervisor_id)

        return supervisor_id

    def retrieve_supervisor(self, inbound_identity_token):
        return self.persistence_service.retrieve_supervisor_by_inbound_identity_token(inbound_identity_token)

    def retrieve_supervisor_id(self, framework_user):
        return SupervisorId(framework_user.supervisor.supervisor_id)

    def start_creating_supervisor_id(self, session: dict):
        flow = self._create_flow(session)

        return self.viewer_connection_service.start_creating_connection(flow)

    def _create_flow(self, session: dict) -> DropboxOAuth2Flow:
        return self.viewer_connection_service.create_flow_object(settings.DROPBOX_API_KEY, settings.DROPBOX_API_SECRET,
                                                                 settings.DROPBOX_CALLBACK_URL, session,
                                                                 "dropbox-auth-csrf-token")


class MonitoringService:
    def __init__(self, persistence_service: PersistenceService, viewer_service: ViewerService):
        self.persistence_service = persistence_service
        self.viewer_service = viewer_service

    def track_activity(self, activity: Snap, supervisor_id: SupervisorId):
        if supervisor_id is None or activity is None: return

        supervisor = self.persistence_service.retrieve_supervisor_status_by_supervisor_id(supervisor_id)
        if supervisor is None or not supervisor.active: return

        premium_edition_active = supervisor_status_service.determine_whether_premium_edition_active(supervisor)
        if not premium_edition_active:
            activity_within_standard_edition_limit = \
                    supervisor_status_service.determine_whether_activity_within_standard_edition_limit(supervisor)

            if not activity_within_standard_edition_limit: return

        connection = supervisor.viewer_connection
        if connection is None: return

        self.viewer_service.send_activity(activity, connection)
        supervisor_status_service.increment_activity_count(supervisor_id)


class PaymentService:
    def __init__(self, payment_profile: PaymentProfile):
        self.payment_profile = payment_profile

    def process_notification(self, supervisor_id: SupervisorId, payment_notification: PaymentNotification) -> None:
        if payment_notification.validate():
            supervisor_status_service.renew_premium_edition_for_one_month(supervisor_id)

    def retrieve_profile(self) -> PaymentProfile:
        return self.payment_profile


class SupervisorStatusService:
    LIMIT = 1000

    def __init__(self, monthly_limit_service: MonthlyLimitService, persistence_service: PersistenceService):
        self.monthly_limit_service = monthly_limit_service
        self.persistence_service = persistence_service

    def determine_whether_premium_edition_active(self, supervisor: SupervisorStatus) -> bool:
        expiration = supervisor.premium_expiration
        return expiration is not None and self.monthly_limit_service.determine_whether_current_date_before(expiration)

    def determine_whether_activity_within_standard_edition_limit(self, supervisor: SupervisorStatus) -> bool:
        activity_month = self.monthly_limit_service.retrieve_current_month() 

        snaps = self.persistence_service.retrieve_activity_count(supervisor.supervisor_id, activity_month)

        return snaps < self.LIMIT

    def increment_activity_count(self, supervisor_id: SupervisorId) -> None:
        activity_month = self.monthly_limit_service.retrieve_current_month()
        self.persistence_service.increment_activity_count(supervisor_id, activity_month)

    # TODO: (IMS) Implement test
    def renew_premium_edition_for_one_month(self, supervisor_id: SupervisorId) -> None:
        current_month = self.monthly_limit_service.retrieve_current_month()

        # TODO: How renew for another month?
        # TODO: (IMS) Payment logging
        self.persistence_service.update_premium_expiration(supervisor_id, current_month)


factory = core.CoreServiceFactory()
viewer_service = factory.createViewerService()
persistence_service = factory.createPersistenceService()
monitoring_service = MonitoringService(persistence_service, viewer_service)

payment_service = None
': :type payment_service: PaymentService'

supervisor_id_service = factory.createSupervisorIdService()
viewer_connection_service = factory.createViewerConnectionService()
administration_service = AdministrationService(persistence_service, supervisor_id_service, viewer_connection_service)

monthly_limit_service = factory.createMonthlyLimitService()
supervisor_status_service = SupervisorStatusService(monthly_limit_service, persistence_service)
