from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.forms.models import ModelForm
from django.http.response import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic.detail import SingleObjectMixin

from osm_web.models import Project


class AdminRequiredMixin(UserPassesTestMixin, SingleObjectMixin):

    def test_func(self):
        if self.request.user == self.get_object().admin:
            return True

        raise Http404


class BidAskMixin(LoginRequiredMixin):
    fields = ['price', 'quantity']

    def form_valid(self, form:ModelForm) -> HttpResponse:
        self.object = form.save(commit=False)

        project_slug = self.kwargs.get('slug', None)
        if not self.prepare_to_save(form, project_slug):
            return super(BidAskMixin, self).form_invalid(form)

        self.object.save()

        return HttpResponseRedirect(self.get_success_url())

    def prepare_to_save(self, form:ModelForm, project_slug:str) -> bool:
        bid = self.object
        project = self.retrieve_project(project_slug)

        total_shares = project.count_total_shares()
        if bid.quantity > total_shares:
            form.add_error('quantity', 'That project does not have that many shares.')

            return False

        bidder = self.request.user
        existing_offers = bidder.userprofile.calculate_existing_bid_incentives()
        if bid.price * bid.quantity > bidder.userprofile.incentives - existing_offers:
            form.add_error('price', 'You do not have that many reputation points available.')

            return False

        bid.project = project
        bid.bidder = bidder

        return True

    def get_context_data(self, **kwargs):
        project_slug = self.kwargs.get('slug', None)
        project = self.retrieve_project(project_slug)

        context = super(BidAskMixin, self).get_context_data(**kwargs)

        context['project'] = project

        return context

    def retrieve_project(self, project_slug:str) -> Project:
        return get_object_or_404(Project, slug=project_slug, active=True)
