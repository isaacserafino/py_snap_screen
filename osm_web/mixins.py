from django.contrib.auth.mixins import UserPassesTestMixin
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from django.views.generic.detail import SingleObjectMixin

from osm_web.models import Stake


class AdminRequiredMixin(UserPassesTestMixin, SingleObjectMixin):

    def test_func(self):
        if self.request.user == self.get_object().admin:
            return True

        raise Http404


class StakeholderRequiredMixin:

    def retrieve_related_stake(self) -> Stake:
        project_slug = self.kwargs.get('slug', None)

        return get_object_or_404(Stake, project__slug=project_slug,
                project__active=True, quantity__gt=0, holder=self.request.user)

    def get_context_data(self, **kwargs):
        stake = self.retrieve_related_stake()

        context = super(StakeholderRequiredMixin, self).get_context_data(
                **kwargs)

        context['project'] = stake.project

        return context
