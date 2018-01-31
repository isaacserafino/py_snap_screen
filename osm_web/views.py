from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.forms.models import ModelForm
from django.http.response import HttpResponseRedirect, HttpResponse
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.list import ListView

from osm_web.mixins import AdminRequiredMixin
from osm_web.models import Project, Ask, Stake, Bid
from py_snap_screen import settings
from django.shortcuts import get_object_or_404
from osm_web.pure import TradeValidator
from abc import ABC, abstractmethod


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


class AbstractBidAsk(ABC, LoginRequiredMixin):
    fields = ['price', 'quantity']

    @abstractmethod
    def retrieve_project(self) -> Project:
        pass

    @abstractmethod
    def validate(self) -> (str, str):
        pass

    def form_valid(self, form:ModelForm) -> HttpResponse:
        self.object = form.save(commit=False)

        field_name, error_message = self.validate()
        if error_message is not None:
            form.add_error(field_name, error_message)

            return super(AbstractBidAsk, self).form_invalid(form)

        self.object.save()

        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super(AbstractBidAsk, self).get_context_data(**kwargs)

        context['project'] = self.retrieve_project()

        return context

    def retrieve_project_slug(self) -> str:
        return self.kwargs.get('slug', None)


class TradeAsk(AbstractBidAsk, CreateView):
    template_name = "trade/ask.djhtml"
    model = Ask

    def retrieve_project(self) -> Project:
        stake = self.retrieve_related_stake()

        return stake.project

    def retrieve_related_stake(self) -> Stake:
        project_slug = self.retrieve_project_slug()

        return get_object_or_404(Stake, project__slug=project_slug,
                project__active=True, quantity__gt=0, holder=self.request.user)

    def validate(self) -> (str, str):
        self.object.stake = self.retrieve_related_stake()

        available_shares_to_sell = \
                self.object.stake.calculate_available_shares_to_sell()

        validator = TradeValidator(self.object.quantity)

        return validator.validate_ask(available_shares_to_sell)


class TradeBid(AbstractBidAsk, CreateView):
    template_name = "trade/bid.djhtml"
    model = Bid

    def retrieve_project(self) -> Project:
        project_slug = self.retrieve_project_slug()

        return get_object_or_404(Project, slug=project_slug, active=True)

    def validate(self) -> (str, str):
        bid = self.object
        bid.project = self.retrieve_project()
        bid.bidder = self.request.user.userprofile

        incentives_available = bid.bidder.calculate_available_bid_incentives()
        total_shares = bid.project.count_total_shares()

        validator = TradeValidator(bid.quantity)

        return validator.validate_bid(bid.price, incentives_available, total_shares)
