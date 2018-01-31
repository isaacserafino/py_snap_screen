from django.contrib.auth.mixins import UserPassesTestMixin
from django.http.response import Http404
from django.views.generic.detail import SingleObjectMixin


class AdminRequiredMixin(UserPassesTestMixin, SingleObjectMixin):

    def test_func(self):
        if self.request.user == self.get_object().admin:
            return True

        raise Http404
