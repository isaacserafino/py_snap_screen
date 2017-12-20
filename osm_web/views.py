from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.forms.models import ModelForm
from django.http.response import HttpResponseRedirect, HttpResponse
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from osm_web.models import Project, Ask
from django.shortcuts import get_object_or_404


class AdminRequiredMixin(UserPassesTestMixin, SingleObjectMixin):
    raise_exception = True

    def test_func(self):
        return self.request.user == self.get_object().admin


class LoginView(TemplateView):
    template_name = "login.djhtml"


class ProjectCreate(LoginRequiredMixin, CreateView):
    template_name = "create.djhtml"
    model = Project
    fields = ['description']

    def form_valid(self, form:ModelForm) -> HttpResponse:
        self.object = form.save(commit=False)
        self.object.admin = self.request.user
        self.object.save()

        return HttpResponseRedirect(self.get_success_url())


class ProjectDeactivate(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
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


class ProjectUpdate(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    template_name = "update.djhtml"
    queryset = Project.objects.filter(active=True)
    fields = ['description']


class TradeAsk(LoginRequiredMixin, CreateView):
    template_name = "ask.djhtml"
    model = Ask
    fields = ['price', 'quantity']

    def retrieve_related_project(self):
        slug = self.kwargs.get('slug', None)
        return get_object_or_404(Project, slug=slug)

    def get_context_data(self, **kwargs):
        context = super(TradeAsk, self).get_context_data(**kwargs)
        context['project'] = self.retrieve_related_project()
        return context

    def form_valid(self, form:ModelForm) -> HttpResponse:
        self.object = form.save(commit=False)
        self.object.asker = self.request.user
        self.object.project = self.retrieve_related_project()
        self.object.save()

        return HttpResponseRedirect(self.get_success_url())
