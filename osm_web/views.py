from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from osm_web.models import Project


class ProjectList(ListView):
    template_name = "index.djhtml"
    queryset = Project.objects.filter(active=True)


class ProjectDetail(DetailView):
    template_name = "detail.djhtml"
    model = Project


class ProjectCreate(LoginRequiredMixin, CreateView):
    template_name = "create.djhtml"
    model = Project
    fields = ['description']


class LoginView(TemplateView):
    template_name = "login.djhtml"
