import re

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, View

from web.models import Snap, SupervisorId
from web.services import monitoring_service, administration_service, payment_service


# Views
class AdministrationView(LoginRequiredMixin, TemplateView):
    template_name = "supervisor.djhtml"

    def get(self, request, *args, **kwargs):  # @UnusedVariable Because this method is an override
        dashboard = administration_service.retrieve_dashboard(request.user.id)
        ': :type dashboard: Dashboard'

        payment_profile = payment_service.retrieve_profile()
        ': :type payment_profile: PaymentProfile'

        payment_form = payment_profile.retrieve_form()
        ': :type payment_form: str'

        model = {'dashboard':dashboard, 'payment_form': payment_form}

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
