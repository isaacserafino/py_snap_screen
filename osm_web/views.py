from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.forms.models import ModelForm
from django.http.response import HttpResponseRedirect, HttpResponse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from osm_web.mixins import AdminRequiredMixin, StakeholderRequiredMixin
from osm_web.models import Project, Ask, Stake
from py_snap_screen import settings


class ProjectCreate(LoginRequiredMixin, CreateView):
    template_name = "project/create.djhtml"
    model = Project
    fields = ['description']

    @transaction.atomic
    def form_valid(self, form:ModelForm) -> HttpResponse:
        self.object = form.save(commit=False)
        self.object.admin = self.request.user
        self.object.save()

        stake = Stake.objects.create(holder=self.request.user,
                project=self.object, quantity=settings.DEFAULT_SHARES_PER_PROJECT)

        stake.save()

        return HttpResponseRedirect(self.get_success_url())


class ProjectDeactivate(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    template_name = "project/deactivate.djhtml"
    queryset = Project.objects.filter(active=True)
    fields = ['active']

    def form_valid(self, form):
        self.object.active = False

        return super(ProjectDeactivate, self).form_valid(form)


class ProjectDetail(DetailView):
    template_name = "project/detail.djhtml"
    queryset = Project.objects.filter(active=True)

    def get_context_data(self, **kwargs):
        context = super(ProjectDetail, self).get_context_data(**kwargs)
        related_stake = self.object.stake_set.filter(quantity__gt=0,
                holder=self.request.user)

        context['user_is_stakeholder'] = related_stake.exists()

        return context


class ProjectList(ListView):
    template_name = "project/index.djhtml"
    queryset = Project.objects.filter(active=True)


class ProjectUpdate(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    template_name = "project/update.djhtml"
    queryset = Project.objects.filter(active=True)
    fields = ['description']


class TradeAsk(LoginRequiredMixin, StakeholderRequiredMixin, CreateView):
    template_name = "trade/ask.djhtml"
    model = Ask
    fields = ['price', 'quantity']

    def form_valid(self, form:ModelForm) -> HttpResponse:
        ask = form.save(commit=False)
        self.object = ask

        ask.stake = self.retrieve_related_stake()

        existing_offers = ask.stake.existing_offers()

        if ask.quantity > ask.stake.quantity - existing_offers:
            form.add_error('quantity', 'That many shares are not available.')

            return super(TradeAsk, self).form_invalid(form)

        ask.save()

        return HttpResponseRedirect(self.get_success_url())
