from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.forms.models import ModelForm
from django.http.response import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from osm_web.mixins import AdminRequiredMixin, BidAskMixin
from osm_web.models import Project, Ask, Stake, Bid
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


class TradeAsk(BidAskMixin, CreateView):
    template_name = "trade/ask.djhtml"
    model = Ask

    def prepare_to_save(self, form:ModelForm, project_slug:str) -> bool:
        ask = self.object

        ask.stake = self.retrieve_related_stake(project_slug)

        existing_offers = ask.stake.count_existing_sell_offers()
        if ask.quantity > ask.stake.quantity - existing_offers:
            form.add_error('quantity', 'That many shares are not available.')

            return False

        return True

    def retrieve_project(self, project_slug:str) -> Project:
        stake = self.retrieve_related_stake(project_slug)

        return stake.project

    def retrieve_related_stake(self, project_slug:str) -> Stake:
        return get_object_or_404(Stake, project__slug=project_slug,
                project__active=True, quantity__gt=0, holder=self.request.user)


class TradeBid(BidAskMixin, CreateView):
    template_name = "trade/bid.djhtml"
    model = Bid
