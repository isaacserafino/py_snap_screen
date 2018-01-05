from django.contrib.auth.mixins import UserPassesTestMixin
from django.http.response import Http404
from django.shortcuts import get_object_or_404
from django.views.generic.detail import SingleObjectMixin

from osm_web.models import Stake, Project


class AdminRequiredMixin(UserPassesTestMixin, SingleObjectMixin):

    def test_func(self):
        if self.request.user == self.get_object().admin:
            return True

        raise Http404


class ProjectRelatedMixin:

    def get_context_data(self, **kwargs):
        project = self.retrieve_project()

        context = super(ProjectRelatedMixin, self).get_context_data(**kwargs)

        context['project'] = project

        return context

    def retrieve_project(self) -> Project:
        return self.retrieve_related_project()

    def retrieve_project_slug(self):
        return self.kwargs.get('slug', None)

    def retrieve_related_project(self) -> Project:
        project_slug = self.retrieve_project_slug()

        return get_object_or_404(Project, slug=project_slug, active=True)


class StakeholderRequiredMixin(ProjectRelatedMixin):

    def retrieve_project(self) -> Project:
        stake = self.retrieve_related_stake()

        return stake.project

    def retrieve_related_stake(self) -> Stake:
        project_slug = self.retrieve_project_slug()

        return get_object_or_404(Stake, project__slug=project_slug,
                project__active=True, quantity__gt=0, holder=self.request.user)
