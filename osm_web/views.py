from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from osm_web.models import Project


class LoginView(TemplateView):
    template_name = "login.djhtml"


class ProjectCreate(LoginRequiredMixin, CreateView):
    template_name = "create.djhtml"
    model = Project
    fields = ['description']


class ProjectDeactivate(LoginRequiredMixin, UpdateView):
    template_name = "deactivate.djhtml"
    queryset = Project.objects.filter(active=True)
    fields = ['active']

    def form_valid(self, form):
        self.object.active = False

        return super(ProjectDeactivate, self).form_valid(form)


class ProjectDetail(DetailView):
    template_name = "detail.djhtml"
    queryset = Project.objects.filter(active=True)


class ProjectList(ListView):
    template_name = "index.djhtml"
    queryset = Project.objects.filter(active=True)


class ProjectUpdate(LoginRequiredMixin, UpdateView):
    template_name = "update.djhtml"
    queryset = Project.objects.filter(active=True)
    fields = ['description']
