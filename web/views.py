from django.contrib import admin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.views.generic import TemplateView

from py_snap_screen import settings
from web import core
from web.models import Snap
from web.models import SupervisorId
from web.models import SupervisorIdService
from web.models import ViewerConnection
from web.models import ViewerConnectionService
from web.models import ViewerService

# Views
class AdministrationView(LoginRequiredMixin, TemplateView):
    template_name = "supervisor.html"

    def get(self, request, *args, **kwargs):
        supervisor_status = administration_service.retrieve_supervisor(request.user.id);
        premium_edition_active = supervisor_status_service.determine_whether_premium_edition_active(supervisor_status)
        activity_within_standard_edition_limit = supervisor_status_service.determine_whether_activity_within_standard_edition_limit(supervisor_status)

        model = {'supervisor_status':supervisor_status, 'premium_edition_active': premium_edition_active, 'activity_within_standard_edition_limit': activity_within_standard_edition_limit}

        return render(request, self.template_name, model)


class LoginView(TemplateView):
    template_name = "login.html"

    def get(self, request, *args, **kwargs):
        next = request.GET.get('next', '/')

        return render(request, self.template_name, {'next': next})


class MonitoringView(View):
    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if not ("supervisor_id" in request.POST or "activity" in request.FILES):
                return View.dispatch(self, request, *args, **kwargs)

        supervisor_id_value = request.POST["supervisor_id"]
        file = request.FILES["activity"]

        filename = file.name
        # TODO: Use chunks?
        activity_value = file.read()

        activity = Snap(filename, activity_value)
        supervisor_id = SupervisorId(supervisor_id_value)

        monitoring_service.track_activity(activity, supervisor_id)

        return redirect('/')


class ViewerConnectionCallbackView(LoginRequiredMixin, TemplateView):
    template_name = "callback.html"

    def get(self, request, *args, **kwargs):
        supervisor_id = administration_service.retrieve_supervisor_id(request.user)

        return render(request, self.template_name, {'supervisor_id': supervisor_id})


# Business Services
class AdministrationService:
    def __init__(self, persistence_service, supervisor_id_service, viewer_connection_service):
        self.persistence_service = persistence_service
        self.supervisor_id_service = supervisor_id_service
        self.viewer_connection_service = viewer_connection_service

    def finish_creating_supervisor_id(self, callback_parameters, session):
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

    def start_creating_supervisor_id(self, session):
        flow = self._create_flow(session)

        return self.viewer_connection_service.start_creating_connection(flow)

    def _create_flow(self, session):
        return self.viewer_connection_service.create_flow_object(settings.DROPBOX_API_KEY, settings.DROPBOX_API_SECRET, settings.DROPBOX_CALLBACK_URL, session, "dropbox-auth-csrf-token")


class MonitoringService:
    def __init__(self, persistence_service, viewer_service):
        self.persistence_service = persistence_service
        self.viewer_service = viewer_service

    def track_activity(self, activity, supervisor_id):
        if supervisor_id is None or activity is None: return

        connection = self.persistence_service.retrieve_viewer_connection(supervisor_id)

        # TODO: call SupervisorStatusService
        

        if connection is not None and connection.active:
                self.viewer_service.send_activity(activity, connection)


class SupervisorStatusService:
    LIMIT = 1000

    def __init__(self, monthly_limit_service, persistence_service):
        self.monthly_limit_service = monthly_limit_service
        self.persistence_service = persistence_service

    def determine_whether_premium_edition_active(self, supervisor):
        expiration = supervisor.premium_expiration
        return expiration is not None and self.monthly_limit_service.determine_whether_current_date_before(expiration)

    def determine_whether_activity_within_standard_edition_limit(self, supervisor):
        activity_month = self.monthly_limit_service.retrieve_current_month() 

        snaps = self.persistence_service.retrieve_activity_count(supervisor.supervisor_id, activity_month)

        return snaps <= self.LIMIT


factory = core.CoreServiceFactory()
viewer_service = factory.createViewerService()
persistence_service = factory.createPersistenceService()
monitoring_service = MonitoringService(persistence_service, viewer_service)

supervisor_id_service = factory.createSupervisorIdService()
viewer_connection_service = factory.createViewerConnectionService()
administration_service = AdministrationService(persistence_service, supervisor_id_service, viewer_connection_service)

monthly_limit_service = factory.createMonthlyLimitService()
supervisor_status_service = SupervisorStatusService(monthly_limit_service, persistence_service)
